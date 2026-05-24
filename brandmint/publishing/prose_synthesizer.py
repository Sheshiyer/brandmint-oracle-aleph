"""
Prose synthesizer — transforms structured skill JSON into narrative brand prose.

Replaces the mechanical "database export" rendering with LLM-powered synthesis
that injects brand voice and transforms analytical structures into readable
narratives. NotebookLM generates dramatically better artifacts from prose
written *as* the brand versus prose *about* the brand's analysis.

Uses OpenRouter chat/completions API via urllib.request (zero pip deps).
Falls back to mechanical rendering when OPENROUTER_API_KEY is not set.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from rich.console import Console


# ---------------------------------------------------------------------------
# Default config
# ---------------------------------------------------------------------------

DEFAULT_MODEL = "anthropic/claude-3.5-haiku"
DEFAULT_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
MAX_RETRIES = 2
RETRY_DELAY = 30  # seconds
MAX_INPUT_CHARS = 100_000  # warn if user prompt exceeds this (~25K tokens)


# ---------------------------------------------------------------------------
# Group-specific prompt templates
# ---------------------------------------------------------------------------

GROUP_PROMPTS: Dict[str, Dict[str, Any]] = {
    "brand-foundation": {
        "title": "Brand Foundation",
        "narrative_structure": [
            "The Market Landscape — Speak directly to the audience about the market reality "
            "this brand enters. Paint the opportunity with specificity: market gaps, unmet needs, "
            "and the white space this brand owns.",
            "The Target Customer — Describe the ideal customer as if you know them personally. "
            "What drives them, what frustrates them, what they've tried before, and what they "
            "really need. Make the reader feel recognized.",
            "The Competitive Terrain — Name competitors directly and explain what they get wrong. "
            "State clearly where this brand dominates and why the competition can't follow.",
        ],
    },
    "brand-strategy": {
        "title": "Brand Strategy",
        "narrative_structure": [
            "Our Position — State the brand's position with conviction. What we are, what we're not, "
            "and why that distinction matters to every person reading this.",
            "How We Communicate — Demonstrate the messaging system in action. Present taglines and "
            "proof points as live ammunition, not museum pieces. Write copy that could ship tomorrow.",
            "Our Voice in Action — Write in the brand's voice throughout — do not describe the voice. "
            "The reader should experience the personality directly, never see it explained.",
            "What We Look Like — Describe the visual system as brand experience, not spec sheet. "
            "Write about what the brand feels like to see, touch, and inhabit.",
        ],
    },
    "campaign-content": {
        "title": "Campaign Content",
        "narrative_structure": [
            "The Campaign Story — Open with the campaign narrative as if launching today. "
            "What is the brand saying to the world, and why does it matter right now?",
            "Launch-Ready Copy — Present headlines, CTAs, and ad copy as finished deliverables. "
            "Write copy that could go live without revision.",
            "Visual Storytelling — Describe video and visual content as creative direction "
            "brought to life. Include the emotional arc and key visual moments.",
            "Press and Public Voice — Write press materials as if the brand's publicist. "
            "Professional, quotable, newsworthy.",
        ],
    },
    "communications-social": {
        "title": "Communications & Social Strategy",
        "narrative_structure": [
            "The Relationship Arc — Present email sequences as the brand's ongoing conversation. "
            "From first touch to loyal customer — write in the voice at each stage.",
            "Social Content System — Show the social strategy as a living system. "
            "Present content themes and voice examples across platforms.",
            "Community Presence — Write the influencer and community strategy as if you're "
            "the brand speaking directly to its community.",
        ],
    },
}


# ---------------------------------------------------------------------------
# ProseSynthesizer
# ---------------------------------------------------------------------------

class ProseSynthesizer:
    """Transform skill JSON outputs into narrative brand prose via LLM."""

    def __init__(
        self,
        voice_config: Optional[dict] = None,
        brand_config: Optional[dict] = None,
        model: str = DEFAULT_MODEL,
        cache_dir: Optional[Path] = None,
        console: Optional[Console] = None,
    ):
        self.voice_config = voice_config or {}
        self.brand_config = brand_config or {}
        self.model = model
        self.cache_dir = cache_dir
        self.console = console or Console()
        self._api_key = os.environ.get("OPENROUTER_API_KEY", "")
        self._print_lock = threading.Lock()

        # Telemetry accumulators
        self._total_input_tokens = 0
        self._total_output_tokens = 0
        self._total_cost_usd = 0.0
        self._telemetry_lock = threading.Lock()

    @property
    def available(self) -> bool:
        """Check if synthesis is possible (API key set)."""
        return bool(self._api_key)

    def _safe_print(self, message: str) -> None:
        """Thread-safe console output."""
        with self._print_lock:
            self.console.print(message)

    def synthesize_all(
        self,
        groups: Dict[str, Dict[str, Any]],
        skill_outputs: Dict[str, dict],
        config: dict,
    ) -> Dict[str, str]:
        """Synthesize all groups in parallel.

        Args:
            groups: SOURCE_GROUPS dict from source_builder.
            skill_outputs: All loaded skill JSON outputs.
            config: Parsed brand-config.yaml.

        Returns:
            Dict mapping group_id to synthesized prose markdown.
        """
        synthesizable = {
            gid: gdef for gid, gdef in groups.items()
            if gid in GROUP_PROMPTS
        }

        if not synthesizable:
            return {}

        results: Dict[str, str] = {}
        self._safe_print(
            f"  [cyan]Synthesizing {len(synthesizable)} groups "
            f"via {self.model}...[/cyan]"
        )

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(
                    self.synthesize_group,
                    group_id=gid,
                    group_def=gdef,
                    skill_outputs=skill_outputs,
                    config=config,
                ): gid
                for gid, gdef in synthesizable.items()
            }

            for future in as_completed(futures):
                gid = futures[future]
                try:
                    prose = future.result()
                    if prose:
                        results[gid] = prose
                        self._safe_print(
                            f"    [green]\u2713[/green] {gid} synthesized "
                            f"({len(prose):,} chars)"
                        )
                    else:
                        self._safe_print(
                            f"    [yellow]![/yellow] {gid} \u2014 empty result, "
                            f"falling back to mechanical"
                        )
                except Exception as e:
                    self._safe_print(
                        f"    [red]\u2717[/red] {gid} \u2014 synthesis failed: {e}"
                    )

        # Print telemetry summary
        if self._total_input_tokens > 0:
            self._safe_print(
                f"  [dim]Synthesis totals: "
                f"{self._total_input_tokens:,} in / "
                f"{self._total_output_tokens:,} out tokens"
                f"{f' (~${self._total_cost_usd:.4f})' if self._total_cost_usd > 0 else ''}"
                f"[/dim]"
            )

        return results

    def synthesize_group(
        self,
        group_id: str,
        group_def: dict,
        skill_outputs: Dict[str, dict],
        config: dict,
    ) -> Optional[str]:
        """Synthesize a single source group into narrative prose.

        Returns synthesized markdown, or None on failure.
        """
        prompt_def = GROUP_PROMPTS.get(group_id)
        if not prompt_def:
            return None

        # Gather the skill data for this group
        group_data: Dict[str, Any] = {}
        for skill_id in group_def.get("skills", []):
            if skill_id in skill_outputs:
                group_data[skill_id] = skill_outputs[skill_id]

        # Gather config sections
        config_sections: Dict[str, Any] = {}
        for section_key in group_def.get("include_config_sections", []):
            section = config.get(section_key)
            if section:
                config_sections[section_key] = section

        if not group_data and not config_sections:
            return None

        # Check cache
        cache_key = self._cache_key(group_id, group_data, config_sections)
        cached = self._read_cache(cache_key)
        if cached is not None:
            self._safe_print(
                f"    [dim]cache hit: {group_id}[/dim]"
            )
            return cached

        # Build prompts
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(
            group_id=group_id,
            prompt_def=prompt_def,
            group_data=group_data,
            config_sections=config_sections,
            brand_name=config.get("brand", {}).get("name", "Brand"),
        )

        # Input size guard
        total_input_chars = len(system_prompt) + len(user_prompt)
        if total_input_chars > MAX_INPUT_CHARS:
            self._safe_print(
                f"    [yellow]![/yellow] {group_id} \u2014 input payload is "
                f"{total_input_chars:,} chars (~{total_input_chars // 4:,} tokens). "
                f"May exceed model context window."
            )

        # Call LLM
        start = time.monotonic()
        prose, usage = self._call_llm(system_prompt, user_prompt)
        elapsed = time.monotonic() - start

        if not prose:
            return None

        # Accumulate telemetry
        if usage:
            with self._telemetry_lock:
                self._total_input_tokens += usage.get("prompt_tokens", 0)
                self._total_output_tokens += usage.get("completion_tokens", 0)
                self._total_cost_usd += usage.get("total_cost", 0.0)
            self._safe_print(
                f"    [dim]{group_id}: {elapsed:.1f}s, "
                f"{usage.get('prompt_tokens', 0):,}+{usage.get('completion_tokens', 0):,} tokens"
                f"[/dim]"
            )

        # Validate output
        if not self._validate_output(prose):
            self._safe_print(
                f"    [yellow]![/yellow] {group_id} \u2014 output validation failed"
            )
            return None

        # Write cache
        self._write_cache(cache_key, prose)

        return prose

    # -- Prompt construction ------------------------------------------------

    def _build_system_prompt(self) -> str:
        """Build the system prompt from voice config + writing rules.

        Injects meta_prompt, tone_descriptors, and voice_persona from
        the voice-and-tone skill output for maximum brand fidelity.
        """
        # Use meta_prompt from voice-and-tone.json if available
        meta_prompt = self.voice_config.get("meta_prompt", "")

        # Fallback: build from brand config if no voice output exists
        if not meta_prompt:
            brand_name = self.brand_config.get("brand", {}).get("name", "Brand")
            tagline = self.brand_config.get("brand", {}).get("tagline", "")
            meta_prompt = (
                f"You are writing as {brand_name}"
                f"{' \u2014 ' + tagline if tagline else ''}. "
                f"Write with authority and expertise about this brand."
            )

        # Enrich with tone descriptors if available
        tone_descriptors = self.voice_config.get("tone_descriptors", [])
        if tone_descriptors:
            tone_names = [
                t.get("descriptor", t.get("name", ""))
                if isinstance(t, dict) else str(t)
                for t in tone_descriptors
            ]
            tone_names = [n for n in tone_names if n]
            if tone_names:
                meta_prompt += (
                    f"\n\nTONE: Your writing tone is {', '.join(tone_names)}."
                )

        # Enrich with voice persona details if available
        voice_persona = self.voice_config.get("voice_persona", {})
        if voice_persona:
            identity = voice_persona.get("identity", "")
            archetype = voice_persona.get("archetype", "")
            comm_style = voice_persona.get("communication_style", "")
            persona_parts = []
            if identity:
                persona_parts.append(f"Identity: {identity}")
            if archetype:
                persona_parts.append(f"Archetype: {archetype}")
            if comm_style:
                persona_parts.append(f"Style: {comm_style}")
            if persona_parts:
                meta_prompt += "\n\nVOICE PERSONA:\n" + "\n".join(persona_parts)

        writing_rules = (
            "\n\nWRITING RULES:\n"
            "1. Write narrative prose, not bullet lists or tables.\n"
            "2. Weave data points into flowing sentences \u2014 cite specific numbers, "
            "names, and facts naturally within the prose.\n"
            "3. Preserve ALL factual content from the source data \u2014 nothing may be "
            "dropped, invented, or embellished.\n"
            "4. Transform lists into paragraphs with connective tissue and analysis.\n"
            "5. Target 1500-3000 words per document.\n"
            "6. Write as if authoring a brand strategy book \u2014 authoritative, "
            "insightful, ready to present to stakeholders.\n"
            "7. Use markdown headings (## and ###) to structure the document.\n"
            "8. Do NOT include meta-commentary about the data or the analysis "
            "process \u2014 present findings as established facts.\n"
            "9. Do NOT use phrases like 'the analysis shows', 'the data reveals', "
            "'according to the research' \u2014 instead, state things directly.\n"
            "10. Write FROM the brand's perspective, not ABOUT the brand's analysis."
        )

        return meta_prompt + writing_rules

    def _build_user_prompt(
        self,
        group_id: str,
        prompt_def: dict,
        group_data: Dict[str, Any],
        config_sections: Dict[str, Any],
        brand_name: str,
    ) -> str:
        """Build the user prompt for a specific group."""
        parts: List[str] = []

        parts.append(
            f"Write the \"{prompt_def['title']}\" section for {brand_name}.\n"
            f"You are {brand_name}. Write directly as the brand, not about the brand.\n"
        )

        # Narrative structure guidance
        parts.append("STRUCTURE:\n")
        for i, section in enumerate(prompt_def["narrative_structure"], 1):
            parts.append(f"{i}. {section}\n")

        # Config sections
        if config_sections:
            parts.append(f"\n--- {brand_name.upper()} IDENTITY ---\n")
            parts.append(json.dumps(config_sections, indent=2, default=str))

        # Skill outputs
        if group_data:
            parts.append(f"\n--- {brand_name.upper()} STRATEGY DATA ---\n")
            for skill_id, data in group_data.items():
                parts.append(f"\n### {skill_id}\n")
                parts.append(json.dumps(data, indent=2, default=str))

        parts.append(
            f"\n--- END DATA ---\n\n"
            f"Write the complete \"{prompt_def['title']}\" document now. "
            f"Use ## headings for major sections and ### for subsections. "
            f"Every fact and data point from the source data must appear in the prose. "
            f"Write as {brand_name} — direct, confident, specific. "
            f"Prose paragraphs, not bullet lists."
        )

        return "\n".join(parts)

    # -- LLM call -----------------------------------------------------------

    def _call_llm(
        self, system_prompt: str, user_prompt: str,
    ) -> Tuple[Optional[str], Optional[dict]]:
        """Call OpenRouter chat/completions API.

        Returns (content, usage_dict) tuple. Content is None on failure.
        Usage dict contains prompt_tokens, completion_tokens, total_cost if
        available from the API response.
        """
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "max_tokens": 8192,
            "temperature": 0.4,
        }

        for attempt in range(MAX_RETRIES + 1):
            try:
                req = urllib.request.Request(
                    DEFAULT_ENDPOINT,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={
                        "Authorization": f"Bearer {self._api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "http://localhost:4191",
                        "X-Title": "brandmint-prose-synthesizer",
                    },
                    method="POST",
                )

                with urllib.request.urlopen(req, timeout=180) as resp:
                    body = resp.read().decode("utf-8")

                data = json.loads(body)
                choices = data.get("choices", [])
                if not choices:
                    return None, None

                content = choices[0].get("message", {}).get("content", "")

                # Extract usage telemetry
                usage = data.get("usage", {})
                # OpenRouter may include cost in top-level or usage
                total_cost = data.get("total_cost", usage.get("total_cost", 0.0))
                usage["total_cost"] = total_cost

                return (content if content else None), usage

            except urllib.error.HTTPError as exc:
                status = exc.code
                detail = exc.read().decode("utf-8", errors="ignore")

                if status == 429 and attempt < MAX_RETRIES:
                    self._safe_print(
                        f"    [yellow]Rate limited \u2014 waiting {RETRY_DELAY}s "
                        f"(attempt {attempt + 1}/{MAX_RETRIES + 1})[/yellow]"
                    )
                    time.sleep(RETRY_DELAY)
                    continue

                self._safe_print(
                    f"    [red]OpenRouter HTTP {status}: "
                    f"{detail[:200]}[/red]"
                )
                return None, None

            except (urllib.error.URLError, OSError, json.JSONDecodeError) as e:
                self._safe_print(
                    f"    [red]OpenRouter request error: {e}[/red]"
                )
                return None, None

        return None, None

    # -- Output validation --------------------------------------------------

    @staticmethod
    def _validate_output(prose: str) -> bool:
        """Basic validation that output is prose markdown, not raw JSON."""
        if not prose or len(prose) < 200:
            return False
        # Must have at least one markdown heading
        if "##" not in prose:
            return False
        # Should not contain large JSON blocks
        if prose.count("{") > 20:
            return False
        return True

    # -- Content-addressed cache --------------------------------------------

    def _cache_key(
        self,
        group_id: str,
        group_data: dict,
        config_sections: dict,
    ) -> str:
        """Compute SHA-256 cache key from inputs."""
        hasher = hashlib.sha256()
        hasher.update(group_id.encode())
        hasher.update(self.model.encode())
        hasher.update(
            json.dumps(group_data, sort_keys=True, default=str).encode()
        )
        hasher.update(
            json.dumps(config_sections, sort_keys=True, default=str).encode()
        )
        # Include voice meta_prompt in hash so cache invalidates on voice change
        hasher.update(
            self.voice_config.get("meta_prompt", "").encode()
        )
        return hasher.hexdigest()[:16]

    def _read_cache(self, key: str) -> Optional[str]:
        """Read cached prose by key. Returns None on miss."""
        if not self.cache_dir:
            return None
        cache_file = self.cache_dir / f"{key}.md"
        if cache_file.is_file():
            try:
                return cache_file.read_text(encoding="utf-8")
            except OSError:
                return None
        return None

    def _write_cache(self, key: str, prose: str) -> None:
        """Write synthesized prose to cache."""
        if not self.cache_dir:
            return
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            cache_file = self.cache_dir / f"{key}.md"
            cache_file.write_text(prose, encoding="utf-8")
        except OSError:
            pass  # Cache write failure is non-fatal

    @classmethod
    def clear_cache(cls, cache_dir: Path) -> int:
        """Remove all cached prose files. Returns count of files removed."""
        if not cache_dir.is_dir():
            return 0
        files = list(cache_dir.glob("*.md"))
        count = len(files)
        if count > 0:
            shutil.rmtree(cache_dir)
        return count
