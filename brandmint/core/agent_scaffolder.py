"""
Agent Scaffolder - Generates context-specific prompts for skill agents
Phase 3 implementation
"""

from typing import Dict, Any, List
from ..models.skill import UnifiedSkill
from ..models.scenario import ExecutionContext


class AgentScaffolder:
    """
    Generates scaffolded prompts for agents based on execution context
    """
    
    def __init__(self):
        self.prompt_template = self._load_prompt_template()
    
    def generate_context_prompt(
        self,
        skill: UnifiedSkill,
        context: ExecutionContext,
        upstream_data: Dict[str, Any] = None,
        scenario_name: str = "execution",
    ) -> str:
        """
        Generate a fully scaffolded prompt for running a skill
        
        Args:
            skill: The skill to run
            context: Execution context with constraints
            upstream_data: Data from upstream skills
            scenario_name: Name of the scenario being executed
        
        Returns:
            Complete prompt ready for Task tool
        """
        upstream_data = upstream_data or {}
        
        # Build sections
        context_section = self._build_context_section(context, scenario_name)
        platform_section = self._build_platform_section(context)
        input_section = self._build_input_section(skill, upstream_data)
        task_section = self._build_task_section(skill)
        output_section = self._build_output_section(skill, context)
        optimization_section = self._build_optimization_section(context)
        
        # Assemble prompt
        prompt = self.prompt_template.format(
            skill_name=skill.name,
            scenario_name=scenario_name,
            context_section=context_section,
            platform_section=platform_section,
            input_section=input_section,
            task_section=task_section,
            output_section=output_section,
            optimization_section=optimization_section,
        )
        
        return prompt
    
    def _build_context_section(self, context: ExecutionContext, scenario_name: str) -> str:
        """Build the CONTEXT CONSTRAINTS section"""
        return f"""CONTEXT CONSTRAINTS:
- Budget Tier: {context.budget_tier.value}
- Tone: {context.tone}
- Output Format: {context.output_format}
- Token Limit: {context.token_limit_per_skill} tokens
- Depth Level: {context.depth_level}
- Quality Bar: {context.quality_bar}
- Scenario: {scenario_name}"""
    
    def _build_platform_section(self, context: ExecutionContext) -> str:
        """Build the PLATFORM CONSTRAINTS section"""
        if not context.platform_constraints:
            return ""
        
        constraints_list = "\n".join(f"- {c}" for c in context.platform_constraints)
        return f"""
PLATFORM CONSTRAINTS:
{constraints_list}"""
    
    def _build_input_section(self, skill: UnifiedSkill, upstream_data: Dict[str, Any]) -> str:
        """Build the INPUT DATA section"""
        if not upstream_data:
            return """
INPUT DATA:
- [Will be provided from upstream skills]"""
        
        inputs_list = "\n".join(
            f"- {key}: {self._summarize_data(value)}"
            for key, value in upstream_data.items()
        )
        
        return f"""
INPUT DATA:
{inputs_list}"""
    
    def _build_task_section(self, skill: UnifiedSkill) -> str:
        """Build the TASK section"""
        if skill.protocol_steps:
            steps_list = "\n".join(f"{i+1}. {step}" for i, step in enumerate(skill.protocol_steps[:10]))
            return f"""
TASK:
{skill.description}

PROTOCOL:
{steps_list}
{"..." if len(skill.protocol_steps) > 10 else ""}"""
        else:
            return f"""
TASK:
{skill.description}

Follow the standard protocol for {skill.name}."""
    
    def _build_output_section(self, skill: UnifiedSkill, context: ExecutionContext) -> str:
        """Build the OUTPUT REQUIREMENTS section"""
        format_instructions = self._get_format_instructions(context.output_format)
        validation_note = self._get_validation_note(skill.required_keys)
        
        keys_list = ", ".join(skill.required_keys[:5])
        if len(skill.required_keys) > 5:
            keys_list += "..."
        
        return f"""
OUTPUT REQUIREMENTS:
- Must include JSON block with keys: {keys_list}
- {format_instructions}
- {validation_note}"""
    
    def _build_optimization_section(self, context: ExecutionContext) -> str:
        """Build the BUDGET OPTIMIZATION section"""
        depth_instructions = self._get_depth_instructions(context.depth_level)
        priority_instructions = self._get_priority_instructions(context.prioritize)
        tips = self._get_token_saving_tips(context.depth_level)
        
        return f"""
BUDGET OPTIMIZATION:
- {depth_instructions}
- {priority_instructions}
- {tips}"""
    
    def _get_format_instructions(self, output_format: str) -> str:
        """Get format-specific instructions"""
        formats = {
            "minimal": "JSON only with brief inline comments. No extended narrative sections.",
            "standard": "JSON block + concise narrative sections (200-400 words each).",
            "maximum": "JSON block + comprehensive narrative with examples and alternatives.",
        }
        return formats.get(output_format, formats["standard"])
    
    def _get_validation_note(self, required_keys: List[str]) -> str:
        """Get validation note"""
        if not required_keys:
            return "Include structured JSON for machine consumption."
        return f"All {len(required_keys)} required keys must be present for validation."
    
    def _get_depth_instructions(self, depth_level: str) -> str:
        """Get depth-specific instructions"""
        depths = {
            "surface": "Abbreviated format. Use bullet points over paragraphs. Skip nice-to-have sections.",
            "focused": "Standard depth. Focus on essentials. Skip tangential examples.",
            "comprehensive": "Full depth with examples. Cover all major points thoroughly.",
            "exhaustive": "Maximum depth. Include alternatives, edge cases, and extensive examples.",
        }
        return depths.get(depth_level, depths["focused"])
    
    def _get_priority_instructions(self, prioritize: str) -> str:
        """Get priority-specific instructions"""
        priorities = {
            "speed": "Prioritize completion over perfection. Good enough is good enough.",
            "quality": "Prioritize thoroughness and polish. Take time to refine.",
            "cost": "Prioritize token efficiency. Be concise without sacrificing clarity.",
            "balanced": "Balance speed, quality, and cost. Optimize for practical value.",
        }
        return priorities.get(prioritize, priorities["balanced"])
    
    def _get_token_saving_tips(self, depth_level: str) -> str:
        """Get token-saving tips based on depth"""
        if depth_level in ["surface", "focused"]:
            return "Use tables and lists over prose. Avoid redundant examples."
        return "Optimize for clarity and completeness."
    
    def _summarize_data(self, value: Any) -> str:
        """Summarize data for prompt"""
        if isinstance(value, dict):
            return f"Dict with {len(value)} keys"
        elif isinstance(value, list):
            return f"List with {len(value)} items"
        elif isinstance(value, str) and len(value) > 100:
            return f"{value[:100]}..."
        return str(value)
    
    def _load_prompt_template(self) -> str:
        """Load the base prompt template"""
        return """You are executing the {skill_name} skill as part of a {scenario_name} campaign.

{context_section}
{platform_section}
{input_section}
{task_section}
{output_section}
{optimization_section}

Execute this skill now and produce the required output."""
