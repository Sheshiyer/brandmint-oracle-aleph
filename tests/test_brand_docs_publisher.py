import json
from pathlib import Path

from brandmint.publishing.brand_docs_publisher import BrandDocsPublisher, PAGE_SPECS


SAMPLE_CONFIG = {
    "execution_context": {"launch_channel": "kickstarter", "quality_bar": "premium"},
    "brand": {"name": "Test Brand", "tagline": "Screen-Free Playtime Companion"},
    "theme": {"name": "Soft Intelligence", "description": "Technology that feels like a hug."},
    "positioning": {
        "hero_headline": "Screen-Free Playtime Companion",
        "statement": "A warm launch portal for product, campaign, and research review.",
    },
    "palette": {
        "primary": {"name": "Muted Lilac", "hex": "#AA98D6"},
        "secondary": {"name": "Cloud White", "hex": "#F8F6F2"},
        "accent": {"name": "Warm Orange", "hex": "#E67A2E"},
    },
    "typography": {
        "header": {"font": "Figtree"},
        "body": {"font": "Inter"},
    },
    "products": {
        "hero": {
            "name": "ZackAI Smart Plush",
            "description": "Screen-free plush companion",
            "physical_form": "Round plush creature with cat-like ears and USB-C charging",
        }
    },
    "materials": ["soft plush fabric", "USB-C charging cable"],
    "publishing": {"notebooklm": {"reuse_policy": "fresh-per-spec", "image_source_policy": "product-reference-only"}},
}


def _make_publisher(tmp_path: Path) -> BrandDocsPublisher:
    config_path = tmp_path / "brand-config.yaml"
    config_path.write_text("brand:\n  name: Test Brand\n", encoding="utf-8")
    (tmp_path / ".brandmint" / "outputs").mkdir(parents=True, exist_ok=True)
    (tmp_path / "deliverables" / "notebooklm" / "artifacts").mkdir(parents=True, exist_ok=True)
    return BrandDocsPublisher(
        brand_dir=tmp_path,
        config=SAMPLE_CONFIG,
        config_path=config_path,
    )


def test_render_product_specifications_page_includes_frontmatter_and_product_spec(tmp_path: Path) -> None:
    publisher = _make_publisher(tmp_path)
    spec = next(item for item in PAGE_SPECS if item.path == "product/specifications.md")

    page = publisher._render_page(
        spec,
        outputs={"detailed-product-description": {"hero_product": {"name": "ZackAI Smart Plush"}}},
        inventory={},
        asset_map={},
        notebooklm={"reports": [], "infographics": [], "tables": [], "audio": [], "decks": [], "flashcards": [], "quizzes": [], "mind_maps": [], "counts": {}},
    )

    assert "title: Product Specifications" in page
    assert "category: product" in page
    assert "icon: 🧵" in page
    assert "# Product Specifications" in page
    assert "Round plush creature with cat-like ears and USB-C charging" in page
    assert "- soft plush fabric" in page


def test_render_visual_assets_library_includes_generated_assets_and_infographics(tmp_path: Path) -> None:
    publisher = _make_publisher(tmp_path)
    spec = next(item for item in PAGE_SPECS if item.path == "brand/visual-assets.md")
    asset_map = {
        "brand/visual-assets.md": {
            "all_assets": [
                {
                    "asset_id": "3B",
                    "file": "3B-hero-product.png",
                    "alt": "Hero Product",
                    "section": "Hero Product",
                    "variant_count": 1,
                }
            ]
        }
    }
    notebooklm = {
        "infographics": [
            {
                "title": "Infographic — Square",
                "route": "/notebooklm/infographic-square.png",
                "kind": "Infographic",
                "file": "infographic-square.png",
            }
        ],
        "reports": [],
        "tables": [],
        "audio": [],
        "decks": [],
        "flashcards": [],
        "quizzes": [],
        "mind_maps": [],
        "counts": {},
    }

    page = publisher._render_page(spec, outputs={}, inventory={}, asset_map=asset_map, notebooklm=notebooklm)

    assert "![Hero Product](/images/3B-hero-product.png)" in page
    assert "### 3B — Hero Product" in page
    assert "## NotebookLM Infographics" in page
    assert "![Infographic — Square](/notebooklm/infographic-square.png)" in page


def test_scan_notebooklm_artifacts_classifies_current_outputs(tmp_path: Path) -> None:
    publisher = _make_publisher(tmp_path)
    artifacts = tmp_path / "deliverables" / "notebooklm" / "artifacts"
    (artifacts / "report-blog.md").write_text("# Blog Report\n\nThis is the launch summary report.", encoding="utf-8")
    (artifacts / "infographic-square.png").write_bytes(b"png")
    (artifacts / "table-product.csv").write_text("name,value\nZackAI,99\n", encoding="utf-8")
    (artifacts / "quiz-medium.json").write_text(json.dumps({"title": "Quiz", "questions": [1, 2, 3]}), encoding="utf-8")

    notebooklm = publisher._scan_notebooklm_artifacts()

    assert notebooklm["counts"]["reports"] == 1
    assert notebooklm["counts"]["infographics"] == 1
    assert notebooklm["counts"]["tables"] == 1
    assert notebooklm["counts"]["quizzes"] == 1
    assert notebooklm["reports"][0]["doc_path"] == "research/report-blog.md"
    assert notebooklm["infographics"][0]["route"] == "/notebooklm/infographic-square.png"
    assert notebooklm["tables"][0]["row_count"] == 1
    assert notebooklm["quizzes"][0]["item_count"] == 3


def test_write_site_data_includes_notebooklm_highlights(tmp_path: Path) -> None:
    publisher = _make_publisher(tmp_path)
    (publisher.wiki_site_dir / "src" / "data").mkdir(parents=True, exist_ok=True)
    publisher.wiki_output_dir.mkdir(parents=True, exist_ok=True)

    asset_map = {
        "product/overview.md": {"hero": {"file": "3B-hero-product.png", "alt": "Hero Product"}},
        "brand/visual-assets.md": {"all_assets": [{"file": "3B-hero-product.png", "alt": "Hero Product"}]},
    }
    notebooklm = {
        "all": [{"title": "Blog Report"}, {"title": "Infographic — Square"}],
        "reports": [
            {
                "title": "Blog Report",
                "summary": "Launch summary report.",
                "doc_href": "/docs/research/report-blog",
                "route": "/notebooklm/report-blog.md",
                "kind": "Report",
            }
        ],
        "infographics": [
            {
                "title": "Infographic — Square",
                "summary": "NotebookLM visual summary artifact surfaced in the media library.",
                "route": "/notebooklm/infographic-square.png",
                "kind": "Infographic",
                "image_route": "/notebooklm/infographic-square.png",
            }
        ],
        "decks": [],
        "audio": [],
        "tables": [],
        "flashcards": [],
        "quizzes": [],
        "mind_maps": [],
        "counts": {"reports": 1, "infographics": 1},
    }

    publisher._write_site_data(outputs={"buyer-persona": {}}, asset_map=asset_map, notebooklm=notebooklm)
    data = json.loads((publisher.wiki_site_dir / "src" / "data" / "site-data.json").read_text())

    assert data["brandName"] == "Test Brand"
    assert data["heroImage"] == "/images/3B-hero-product.png"
    assert data["heroSecondaryHref"] == "/docs/research/notebooklm-artifacts"
    assert any(item["title"] == "NotebookLM Artifacts" for item in data["featuredDocs"])
    assert any(item["kind"] == "Report" for item in data["notebooklmHighlights"])
    assert any(item["image"] == "/notebooklm/infographic-square.png" for item in data["visualHighlights"])


def test_write_localized_wiki_docs_skips_non_zackai_brand(tmp_path: Path) -> None:
    publisher = _make_publisher(tmp_path)
    publisher.wiki_output_fr_dir.mkdir(parents=True, exist_ok=True)
    notebooklm = {"reports": [], "infographics": [], "tables": [], "audio": [], "decks": [], "flashcards": [], "quizzes": [], "mind_maps": [], "counts": {}}

    publisher._write_localized_wiki_docs(outputs={}, inventory={}, asset_map={}, notebooklm=notebooklm)

    assert list(publisher.wiki_output_fr_dir.rglob("*.md")) == []


def test_write_localized_wiki_docs_generates_french_priority_pages(tmp_path: Path) -> None:
    publisher = _make_publisher(tmp_path)
    publisher.config.setdefault("brand", {})["name"] = "ZackAI"
    publisher.wiki_output_fr_dir.mkdir(parents=True, exist_ok=True)

    outputs = {
        "detailed-product-description": {
            "handoff": {
                "hero_product": {
                    "name": "ZackAI Smart Plush — Phantom Purple",
                    "description": "AI-powered screen-free learning companion with animated LED eyes",
                },
                "feature_breakdown": [
                    {"name": "Screen-free conversation", "benefit": "Children learn through dialogue rather than passive screen time."}
                ],
                "materials_and_safety": ["soft fluffy plush fabric"],
                "use_cases": ["bedtime storytelling"],
                "objections_addressed": ["Why not just use a tablet? ZackAI keeps the experience tactile and calm."],
                "proof_angles": ["screen-free learning alternative"],
            }
        },
        "product-positioning-summary": {
            "performance": {
                "points_of_difference": [
                    "True conversational AI that adapts in real time to each child's age, interests, and language level"
                ]
            },
            "judgments": {
                "credibility_proof": [
                    "GDPR, CE, and EN71 certified — the trifecta of EU child product compliance"
                ]
            },
            "positioning_statement": "For intentional parents in France...",
        },
        "mds-messaging-direction-summary": {
            "core_message": "ZackAI is the cuddly, screen-free AI companion that speaks your child's language..."
        },
        "visual-identity-core": {
            "visual_mood": {"name": "Soft Intelligence", "keywords": ["cozy", "tactile"]},
            "color_palette": [{"name": "Muted Lilac", "hex": "#AA98D6", "role": "primary", "psychology": "Gentle imagination and creative calm.", "usage": "Hero surfaces"}],
            "typography": {"header": {"family": "Figtree"}, "body": {"family": "Inter"}},
            "imagery_direction": {
                "photography_style": {"description": "Warm, soft-lit lifestyle photography in cozy home environments.", "color_treatment": "Slightly warm white balance", "composition": "Eye-level compositions"},
                "illustration_style": {"description": "Rounded, organic vector illustrations with soft edges and gentle gradients."},
                "environments": ["Cozy children's bedrooms with soft rugs and cushions"],
                "constraints": ["No screens visible in any imagery — this is a screen-free product"],
            },
            "negative_prompt": {"avoid": ["Metallic or chrome surfaces"]},
            "competitor_differentiation": {"visual_territory_owned": {"color": "Muted Lilac as primary — a distinctive, warm-imaginative space no competitor occupies."}},
        },
        "campaign-page-copy": {
            "handoff": {
                "sections": [{"title": "Why families need this now", "copy": "Parents want less screen time and more meaningful play. ZackAI gives children a responsive companion that listens, teaches, and comforts."}],
                "feature_pillars": ["screen-free learning"],
                "objections": ["No subscription"],
                "cta_language": ["Back ZackAI on Kickstarter"],
                "rewards_framing": [{"tier": "Early Bird", "offer": "Hero color at launch price"}],
                "faq": [{"q": "Is ZackAI screen-free?", "a": "Yes. The core interaction is voice, plush touch, and expressive LED feedback."}],
                "social_proof_angles": ["intentional parenting"],
            }
        },
        "voice-and-tone": {
            "brand_persona": {
                "name": "Zack",
                "communication_style": "Zack speaks like a beloved older sibling or a favourite storybook narrator.",
                "personality_traits": ["Warm and nurturing", "Trustworthy and transparent"],
            },
            "voice_attributes": [
                {"name": "Warm", "definition": "Every word should feel like a cosy blanket — safe, inviting, and full of care.", "do": "Use sensory, emotionally resonant language: 'Zack is ready for your next adventure together.'", "dont": "Don't use cold, transactional language: 'Device is operational and awaiting input.'"}
            ],
            "tone_spectrum": {"contexts": [{"context": "Website (Hero & Product Pages)", "tone": "Warm confidence with clear value propositions", "warmth": 8, "playfulness": 7, "professionalism": 6, "example": "A fluffy learning companion that speaks 40+ languages, needs no screen, and never runs out of patience."}]},
            "vocabulary": {"preferred_words": ["companion"], "avoided_words": ["device"], "power_phrases": ["No screen. No subscription. No worry."]},
            "writing_rules": [{"rule": "Child as hero", "description": "Always position the child as the protagonist."}],
            "sample_copy": {"website_hero": {"headline": "A fluffy friend who speaks their language.", "subheadline": "ZackAI is the screen-free learning companion for curious kids aged 3–12. 40+ languages. No subscription. Just squeeze and explore.", "cta": "Meet Zack — EUR 99, everything included"}, "push_notification": "Psst — Zack has a new story about a fox who counts in Japanese. Your little one might love it.", "packaging_insert": "Salut! I'm Zack — your new adventure buddy. I love stories, silly questions, and learning new words. Squeeze my paw and say hello. I already speak your language (and about 40 others). Let's explore together!"},
            "bilingual_guidelines": {"rules": [{"rule": "French-first for France launch", "description": "All consumer-facing copy for the French market must be written natively in French, not translated from English."}]},
        },
        "welcome-email-sequence": {
            "handoff": {"emails": [{"name": "Welcome to ZackAI", "timing": "Immediate", "subject": "You’re in — welcome to the warm side of AI play", "goal": "Confirm signup and establish brand promise", "summary": "Introduce ZackAI, core promise, and what subscribers can expect next."}]}
        },
        "pre-launch-email-sequence": {
            "handoff": {"emails": [{"name": "The problem with screen-time solutions", "timing": "T-10 days", "subject": "Why parents are searching for a better kind of play", "goal": "Prime the problem/solution frame"}]}
        },
        "launch-email-sequence": {
            "handoff": {"emails": [{"name": "Launch Morning", "timing": "Launch Day 09:00", "subject": "ZackAI is live on Kickstarter", "goal": "Drive initial pledge surge", "cta": "Back ZackAI now"}]}
        },
        "social-content-engine": {
            "handoff": {
                "content_pillars": ["screen-free learning"],
                "post_concepts": ["bedtime ritual reel"],
                "channel_adaptations": {"instagram": "emotion-first reels and warm carousel posts", "x": "sharp hooks, launch updates, reward urgency", "linkedin": "founder story, design credibility, category framing"},
                "publishing_cadence": "daily during launch week, then 4-5 posts per week during the live campaign",
                "cta_ideas": ["Join the Kickstarter"],
                "community_prompts": ["What should ZackAI say at bedtime?"],
            }
        },
        "influencer-outreach-pro": {
            "handoff": {
                "creator_segments": ["parenting creators"],
                "outreach_angles": ["screen-free learning"],
                "sample_messages": {"dm": "Hi [Name], we’re launching ZackAI, a warm screen-free AI plush companion for curious kids, and your community felt like a beautiful fit for an early look."},
                "collaboration_concepts": ["unboxing and bedtime ritual reel"],
                "gifting_strategy": "Send hero color sample with launch briefing and preferred story angles.",
                "measurement_ideas": ["creator code clicks"],
            }
        },
        "campaign-video-script": {
            "handoff": {
                "opening_hook": "What if the smartest thing in your child’s room felt like a hug instead of a screen?",
                "story_arc": ["problem", "product reveal"],
                "scene_beats": ["Hands reach for a device, then pause."],
                "voiceover": ["Meet ZackAI, the screen-free playtime companion."],
                "on_screen_text": ["Screen-Free Playtime Companion"],
                "proof_moments": ["screen-free positioning"],
                "cta": "Back ZackAI now and join the first generation of screen-free AI families.",
            }
        },
        "pre-launch-ads": {
            "handoff": {
                "audience_segments": ["intentional parents"],
                "hooks": ["A screen-free AI friend for curious kids"],
                "headline_variants": ["Screen-Free Playtime Companion"],
                "body_copy_variants": ["ZackAI brings conversational learning into a soft, glowing plush companion parents can trust."],
                "cta_variants": ["Join the waitlist"],
                "creative_direction": ["warm natural light"],
                "angles_to_test": ["screen-free learning"],
            }
        },
        "live-campaign-ads": {
            "handoff": {
                "campaign_stage_segments": ["launch surge"],
                "hooks": ["Back the plush AI families are rallying behind"],
                "copy_variants": ["Families are backing ZackAI because it feels like the future of play—soft, safe, and screen-free."],
                "urgency_messages": ["Early tiers are moving"],
                "retargeting_angles": ["waitlist visitors"],
                "creative_guidance": ["use real campaign progress"],
            }
        },
        "buyer-persona": {
            "demographics": {
                "age_range": "30-42",
                "family_status": "Married or partnered with 1-3 children.",
                "location": "Urban and peri-urban France — Paris/Ile-de-France, Lyon.",
                "tech_comfort": "High digital literacy but deliberately tech-skeptical for children."
            },
            "psychographics": {
                "values": ["Intentional parenting over convenience parenting"],
                "fears": ["That AI is recording, profiling, or manipulating their child"],
                "aspirations": ["Raise a curious, empathetic, multilingual child without relying on screens"],
                "daily_frustrations": ["The 'can I watch something?' negotiation that happens 5-10 times per day"]
            },
            "buying_triggers": ["Learns it is GDPR-compliant and EN71/CE certified — safety-first messaging lands hard"],
            "objections": [{"objection": "It is still AI talking to my child. How do I know it is safe?", "counter": "ZackAI is EN71, ASTM F963, and CE certified for physical safety, and fully GDPR-compliant for data privacy."}],
            "persona_summary": "The Intentional Parent is a well-educated, upper-middle-income parent in urban France.",
        },
        "competitor-analysis": {
            "competitors": [{"name": "Bondu", "category": "AI smart plush toy", "threat_level": "HIGH — direct competitor in same category, same market"}],
            "zackai_differentiators": [{"differentiator": "40+ Languages with Conversational AI", "why_it_wins": "No competitor offers real-time conversational language learning in 40+ languages."}],
            "market_gaps_exploited": ["No AI companion in EU market offers 40+ conversational languages"],
            "visual_differentiation_strategy": {"avoid": ["Teal/mint green (Bondu's territory — #78C9B3)"], "own": ["Muted Lilac (#AA98D6) as primary — warm, unique, unoccupied in category"]},
            "pricing_analysis": {"verdict": "ZackAI at EUR 99 all-in is the best value proposition in the category."},
            "strategic_recommendations": ["Lead with '40+ languages, zero screens, no subscription' as the three-pillar differentiation"],
        },
    }
    notebooklm = {"reports": [], "infographics": [], "tables": [], "audio": [], "decks": [], "flashcards": [], "quizzes": [], "mind_maps": [], "counts": {}}

    publisher._write_localized_wiki_docs(outputs=outputs, inventory={}, asset_map={}, notebooklm=notebooklm)

    fr_product = (publisher.wiki_output_fr_dir / "product" / "overview.md").read_text()
    fr_features = (publisher.wiki_output_fr_dir / "product" / "features.md").read_text()
    fr_specs = (publisher.wiki_output_fr_dir / "product" / "specifications.md").read_text()
    fr_voice = (publisher.wiki_output_fr_dir / "brand" / "voice-tone.md").read_text()
    fr_visual_assets = (publisher.wiki_output_fr_dir / "brand" / "visual-assets.md").read_text()
    fr_primary_persona = (publisher.wiki_output_fr_dir / "audience" / "primary-persona.md").read_text()
    fr_secondary_personas = (publisher.wiki_output_fr_dir / "audience" / "secondary-personas.md").read_text()
    fr_competitive = (publisher.wiki_output_fr_dir / "market" / "competitive-landscape.md").read_text()
    fr_email = (publisher.wiki_output_fr_dir / "marketing" / "email-templates.md").read_text()
    fr_social = (publisher.wiki_output_fr_dir / "marketing" / "social-content.md").read_text()
    fr_video = (publisher.wiki_output_fr_dir / "marketing" / "video-scripts.md").read_text()
    fr_ads = (publisher.wiki_output_fr_dir / "marketing" / "ad-creative.md").read_text()
    fr_quickstart = (publisher.wiki_output_fr_dir / "getting-started" / "quickstart.md").read_text()

    assert "title: Vue d’ensemble produit" in fr_product
    assert "# Vue d’ensemble produit" in fr_product
    assert "## Réassurance parentale" in fr_product
    assert "title: Fonctionnalités produit" in fr_features
    assert "## Les bénéfices cœur" in fr_features
    assert "title: Spécifications produit" in fr_specs
    assert "## Spécification canonique" in fr_specs
    assert "title: Voix & ton" in fr_voice
    assert "## Les 6 attributs de voix" in fr_voice
    assert "title: Bibliothèque visuelle" in fr_visual_assets
    assert "## Assets Brandmint générés" in fr_visual_assets
    assert "title: Persona principal" in fr_primary_persona
    assert "## Profil synthétique" in fr_primary_persona
    assert "title: Personas secondaires" in fr_secondary_personas
    assert "## Segments adjacents à privilégier" in fr_secondary_personas
    assert "title: Paysage concurrentiel" in fr_competitive
    assert "## Différenciateurs ZackAI" in fr_competitive
    assert "title: Templates email" in fr_email
    assert "## Séquence de lancement" in fr_email
    assert "title: Contenu social" in fr_social
    assert "## Adaptation par canal" in fr_social
    assert "title: Scripts vidéo" in fr_video
    assert "## Arc narratif" in fr_video
    assert "title: Création publicitaire" in fr_ads
    assert "## Ads live campaign" in fr_ads
    assert "title: Démarrage rapide" in fr_quickstart
    assert "Markdown wiki FR" in fr_quickstart


def test_write_report_includes_localized_docs(tmp_path: Path) -> None:
    publisher = _make_publisher(tmp_path)
    publisher.wiki_output_dir.mkdir(parents=True, exist_ok=True)
    publisher.wiki_output_fr_dir.mkdir(parents=True, exist_ok=True)
    (publisher.wiki_output_dir / "index.md").write_text("# Index\n", encoding="utf-8")
    (publisher.wiki_output_fr_dir / "product").mkdir(parents=True, exist_ok=True)
    (publisher.wiki_output_fr_dir / "product" / "overview.md").write_text("# Vue d’ensemble produit\n", encoding="utf-8")

    publisher._write_report(outputs={}, inventory={"documents": []}, asset_map={}, notebooklm={"reports": [], "counts": {}})
    report = json.loads(publisher.report_path.read_text())

    assert report["wiki_output_fr_dir"].endswith("wiki-output-fr")
    assert report["localized_docs"]["fr"] == ["product/overview.md"]
