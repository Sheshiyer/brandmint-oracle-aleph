from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional


FRENCH_LOCALIZED_PAGES: Dict[str, Dict[str, str]] = {
    "index.md": {
        "title": "Index du dossier de lancement",
        "description": "Vue d’ensemble française du portail ZackAI avec accès rapide au produit, à la campagne, au visuel et à la recherche.",
    },
    "product/overview.md": {
        "title": "Vue d’ensemble produit",
        "description": "Récit produit, positionnement et promesse centrale de ZackAI pour le lancement actuel.",
    },
    "product/features.md": {
        "title": "Fonctionnalités produit",
        "description": "Lecture française des bénéfices, usages et signaux de confiance qui structurent ZackAI au quotidien.",
    },
    "product/specifications.md": {
        "title": "Spécifications produit",
        "description": "Spécification canonique, matériaux, points de sécurité et détails d’exécution pour le ZackAI hero product.",
    },
    "brand/voice-tone.md": {
        "title": "Voix & ton",
        "description": "Règles de voix, calibration tonale et garde-fous rédactionnels pour faire parler ZackAI en français avec justesse.",
    },
    "brand/visual-guidelines.md": {
        "title": "Lignes directrices visuelles",
        "description": "Palette, typographie, direction artistique et garde-fous du système de marque ZackAI.",
    },
    "brand/visual-assets.md": {
        "title": "Bibliothèque visuelle",
        "description": "Lecture française de la bibliothèque d’assets ZackAI et des infographies NotebookLM du run beta-update.",
    },
    "audience/primary-persona.md": {
        "title": "Persona principal",
        "description": "Lecture française du parent intentionnel qui porte la décision d’achat ZackAI.",
    },
    "audience/secondary-personas.md": {
        "title": "Personas secondaires",
        "description": "Segments adjacents et besoins complémentaires autour du persona principal ZackAI.",
    },
    "market/competitive-landscape.md": {
        "title": "Paysage concurrentiel",
        "description": "Lecture française du paysage concurrentiel, des menaces et des angles de différenciation ZackAI.",
    },
    "marketing/campaign-copy.md": {
        "title": "Copy de campagne",
        "description": "Narratif Kickstarter, structure de page, objections, CTA et preuve sociale pour ZackAI.",
    },
    "marketing/email-templates.md": {
        "title": "Templates email",
        "description": "Lecture française des séquences welcome, pré-lancement et lancement pour le funnel ZackAI.",
    },
    "marketing/social-content.md": {
        "title": "Contenu social",
        "description": "Stratégie sociale française pour ZackAI : cadence, piliers éditoriaux, créateurs et prompts de communauté.",
    },
    "marketing/video-scripts.md": {
        "title": "Scripts vidéo",
        "description": "Lecture française du film Kickstarter ZackAI : hook, séquences, preuve et CTA.",
    },
    "marketing/ad-creative.md": {
        "title": "Création publicitaire",
        "description": "Angles paid media français pour ZackAI avant et pendant la campagne Kickstarter.",
    },
    "getting-started/quickstart.md": {
        "title": "Démarrage rapide",
        "description": "Guide de repérage rapide pour les outputs, visuels et artefacts NotebookLM du run beta-update.",
    },
    "research/notebooklm-artifacts.md": {
        "title": "Artefacts NotebookLM",
        "description": "Hub de recherche pour les rapports, decks, audio, infographies et exports structurés générés par NotebookLM.",
    },
}


def _normalized_brand_name(config: Optional[Dict[str, Any]]) -> str:
    brand_name = (config or {}).get("brand", {}).get("name", "")
    return "".join(ch for ch in str(brand_name).lower() if ch.isalnum())


def _supports_custom_french_copy(config: Optional[Dict[str, Any]]) -> bool:
    """Return True only for the ZackAI-specific FR copy pack.

    This module contains a bespoke French narrative tuned for the ZackAI
    launch. For other brands, the publisher should skip FR page generation
    to avoid cross-brand copy leakage.
    """
    normalized = _normalized_brand_name(config)
    return normalized == "zackai"


def localized_page_paths(locale: str, config: Optional[Dict[str, Any]] = None) -> List[str]:
    if locale == "fr":
        if not _supports_custom_french_copy(config):
            return []
        return list(FRENCH_LOCALIZED_PAGES.keys())
    return []


def localized_page_metadata(
    locale: str,
    path: str,
    config: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, str]]:
    if locale == "fr":
        if not _supports_custom_french_copy(config):
            return None
        return FRENCH_LOCALIZED_PAGES.get(path)
    return None


def render_localized_page_body(
    locale: str,
    path: str,
    *,
    outputs: Dict[str, Any],
    config: Dict[str, Any],
    config_path: Path,
    brand_dir: Path,
    notebooklm: Dict[str, Any],
) -> Optional[str]:
    if locale != "fr":
        return None
    if not _supports_custom_french_copy(config):
        return None

    if path == "index.md":
        return _render_fr_index(config, brand_dir, notebooklm)
    if path == "product/overview.md":
        return _render_fr_product_overview(outputs)
    if path == "product/features.md":
        return _render_fr_product_features(outputs)
    if path == "product/specifications.md":
        return _render_fr_product_specifications(outputs, config)
    if path == "brand/voice-tone.md":
        return _render_fr_voice_tone(outputs)
    if path == "brand/visual-guidelines.md":
        return _render_fr_visual_guidelines(outputs, config)
    if path == "brand/visual-assets.md":
        return _render_fr_visual_assets(outputs, notebooklm)
    if path == "audience/primary-persona.md":
        return _render_fr_primary_persona(outputs)
    if path == "audience/secondary-personas.md":
        return _render_fr_secondary_personas(outputs)
    if path == "market/competitive-landscape.md":
        return _render_fr_competitive_landscape(outputs)
    if path == "marketing/campaign-copy.md":
        return _render_fr_campaign_copy(outputs)
    if path == "marketing/email-templates.md":
        return _render_fr_email_templates(outputs)
    if path == "marketing/social-content.md":
        return _render_fr_social_content(outputs)
    if path == "marketing/video-scripts.md":
        return _render_fr_video_scripts(outputs)
    if path == "marketing/ad-creative.md":
        return _render_fr_ad_creative(outputs)
    if path == "getting-started/quickstart.md":
        return _render_fr_quickstart(config_path, brand_dir, notebooklm)
    if path == "research/notebooklm-artifacts.md":
        return _render_fr_notebooklm_artifacts(notebooklm)
    return None


def _render_fr_index(config: Dict[str, Any], brand_dir: Path, notebooklm: Dict[str, Any]) -> str:
    brand_name = config.get("brand", {}).get("name", "ZackAI")
    tagline = config.get("brand", {}).get("tagline", "Compagnon de jeu sans écran")
    lines = [
        "# Index du dossier de lancement",
        "",
        f"Ce portail rassemble la dernière version du run **{brand_dir.name}** pour {brand_name}. Il combine le récit produit, la direction visuelle, la campagne Kickstarter et les artefacts de recherche NotebookLM dans une expérience wiki bilingue.",
        "",
        "## Snapshot du build",
        "",
        f"- **Marque :** {brand_name}",
        f"- **Tagline :** {tagline}",
        f"- **Run root :** `{brand_dir}`",
        f"- **Build Astro publié :** `{brand_dir / 'wiki-site' / 'dist'}`",
        f"- **Artefacts NotebookLM surfacés :** {len(notebooklm.get('all', []))}",
        "",
        "## Accès rapide",
        "",
        "- [Vue d’ensemble produit](/fr/docs/product/overview)",
        "- [Lignes directrices visuelles](/fr/docs/brand/visual-guidelines)",
        "- [Copy de campagne](/fr/docs/marketing/campaign-copy)",
        "- [Démarrage rapide](/fr/docs/getting-started/quickstart)",
        "- [Artefacts NotebookLM](/fr/docs/research/notebooklm-artifacts)",
        "",
        "## Comment lire ce portail",
        "",
        "1. Commencez par le produit pour recalibrer la promesse ZackAI.",
        "2. Passez par le visuel pour vérifier que la marque reste douce, premium et sans écran.",
        "3. Ouvrez ensuite la copy de campagne pour revoir les angles Kickstarter.",
        "4. Terminez par NotebookLM pour explorer les synthèses, decks, audio et exports structurés.",
    ]
    return "\n".join(lines) + "\n"


def _render_fr_product_overview(outputs: Dict[str, Any]) -> str:
    detailed = outputs.get("detailed-product-description", {})
    positioning = outputs.get("product-positioning-summary", {})
    mds = outputs.get("mds-messaging-direction-summary", {})

    hero = detailed.get("handoff", {}).get("hero_product", {})
    features = detailed.get("handoff", {}).get("feature_breakdown", [])
    materials = detailed.get("handoff", {}).get("materials_and_safety", [])
    use_cases = detailed.get("handoff", {}).get("use_cases", [])
    objections = detailed.get("handoff", {}).get("objections_addressed", [])
    proof_angles = detailed.get("handoff", {}).get("proof_angles", [])
    points_of_difference = positioning.get("performance", {}).get("points_of_difference", [])
    credibility = positioning.get("judgments", {}).get("credibility_proof", [])
    positioning_statement = positioning.get("positioning_statement", "")
    core_message = mds.get("core_message", "")

    lines = [
        "# Vue d’ensemble produit",
        "",
        "![Hero Product](/images/3B-hero-product-nanobananapro-v1.png)",
        "",
        "ZackAI est un compagnon IA en peluche, premium et sans écran, conçu pour transformer le jeu, l’apprentissage et le coucher en rituels conversationnels chaleureux.",
        "",
        "## Le produit en une phrase",
        "",
        f"- **Nom hero :** {hero.get('name', 'ZackAI Smart Plush — Phantom Purple')}",
        "- **Promesse courte :** compagnon d’apprentissage sans écran, propulsé par l’IA, avec yeux LED animés et présence émotionnelle chaleureuse.",
        f"- **Forme physique :** créature pelucheuse ronde, douce et rassurante, avec oreilles félines, visage crème, yeux LED expressifs et recharge USB-C.",
        "",
        "## Positionnement cœur",
        "",
        "ZackAI se place à l’intersection entre la peluche affective, le compagnon conversationnel et l’outil d’éveil multilingue. L’idée n’est pas d’ajouter encore un gadget dans la chambre de l’enfant, mais de proposer une présence familière, calme et intelligente, qui accompagne le jeu et la curiosité sans introduire d’écran.",
        "",
        "- **Sans écran :** l’interaction repose sur la voix, le toucher et la présence émotionnelle.",
        "- **Multilingue :** 40+ langues pour accompagner les foyers bilingues et la découverte ludique des langues.",
        "- **Sans abonnement :** un achat unique à EUR 99 pour le lancement, sans fatigue d’abonnement ni verrouillage financier.",
        "- **Conçu pour la confiance parentale :** matériaux doux, forme rassurante et posture de conformité européenne.",
        "",
        "## Pourquoi ZackAI répond à un vrai besoin maintenant",
        "",
        "Les parents veulent moins d’écran, plus de présence, et des objets technologiques qui ne cassent pas le rythme émotionnel de la maison. ZackAI répond précisément à cette tension : offrir un compagnon intelligent qui parle, écoute, rassure et stimule l’imaginaire sans glisser vers une expérience de type tablette ou assistant vocal générique.",
        "",
        "## Ce que le produit apporte concrètement",
        "",
    ]

    feature_translations = {
        "Screen-free conversation": "Conversation sans écran",
        "Animated LED personality": "Personnalité LED animée",
        "40+ language support": "Support de 40+ langues",
        "Parent-trustworthy construction": "Construction pensée pour la confiance parentale",
    }
    benefit_translations = {
        "Children learn through dialogue rather than passive screen time.": "Les enfants apprennent par le dialogue au lieu de consommer un temps d’écran passif.",
        "Expressive eyes reinforce emotional cues and delight.": "Les yeux expressifs renforcent les signaux émotionnels et ajoutent une vraie dimension de joie.",
        "Useful for bilingual homes and playful language discovery.": "Particulièrement pertinent pour les foyers bilingues et la découverte ludique des langues.",
        "Warm materials, rounded hardware, and no subscription dependency.": "Matériaux chaleureux, éléments matériels rassurants et absence totale de dépendance à l’abonnement.",
    }
    for item in features:
        lines.append(f"- **{feature_translations.get(item.get('name', ''), item.get('name', 'Capacité'))} :** {benefit_translations.get(item.get('benefit', ''), item.get('benefit', ''))}")
    lines.extend([
        "",
        "## Différenciation face au marché",
        "",
    ])
    for item in points_of_difference[:5]:
        lines.append(f"- { _translate_difference(item) }")

    lines.extend([
        "",
        "## Matériaux, sensation et sécurité",
        "",
        "ZackAI doit toujours se lire comme un objet doux, tactile et calme avant de se lire comme de la technologie. Les matériaux et signaux de construction sont donc aussi importants que l’intelligence conversationnelle elle-même.",
        "",
    ])
    for material in materials:
        lines.append(f"- { _translate_material(material) }")

    lines.extend([
        "",
        "## Moments d’usage à privilégier",
        "",
    ])
    for item in use_cases:
        lines.append(f"- { _translate_use_case(item) }")

    lines.extend([
        "",
        "## Réassurance parentale",
        "",
    ])
    for item in objections:
        lines.append(f"- { _translate_objection(item) }")
    for item in credibility[:4]:
        lines.append(f"- { _translate_credibility(item) }")

    if core_message:
        lines.extend([
            "",
            "## Message directeur",
            "",
            f"> {_translate_core_message(core_message)}",
        ])

    if proof_angles:
        lines.extend([
            "",
            "## Angles de preuve à reprendre dans le portail",
            "",
        ])
        for item in proof_angles:
            lines.append(f"- { _translate_proof_angle(item) }")

    if positioning_statement:
        lines.extend([
            "",
            "## Signature de positionnement",
            "",
            _translate_positioning_statement(positioning_statement),
        ])

    lines.extend([
        "",
        "## Pour aller plus loin",
        "",
        "- [Voir les lignes directrices visuelles](/fr/docs/brand/visual-guidelines)",
        "- [Ouvrir le hub NotebookLM](/fr/docs/research/notebooklm-artifacts)",
        "- [Consulter la copy de campagne](/fr/docs/marketing/campaign-copy)",
    ])
    return "\n".join(lines) + "\n"


def _render_fr_visual_guidelines(outputs: Dict[str, Any], config: Dict[str, Any]) -> str:
    visual = outputs.get("visual-identity-core", {})
    palette = visual.get("color_palette", [])
    typography = visual.get("typography", {})
    imagery = visual.get("imagery_direction", {})
    negative = visual.get("negative_prompt", {}).get("avoid", [])
    competitor = visual.get("competitor_differentiation", {})

    lines = [
        "# Lignes directrices visuelles",
        "",
        "![Brand Kit Bento Grid](/images/2A-brand-kit-bento-nanobananapro-v1.png)",
        "",
        "![Brand Seal](/images/2B-brand-seal-flux2pro-v1.png)",
        "",
        "![Logo Emboss](/images/2C-logo-emboss-flux2pro-v1.png)",
        "",
        "Le système visuel ZackAI doit toujours faire ressentir la **douceur**, la **sécurité** et une **intelligence chaleureuse**. La marque n’est pas une techno froide pour enfants : c’est une présence affective, premium et rassurante, conçue pour le foyer.",
        "",
        "## Palette & typographie",
        "",
        f"- **Primaire :** {config.get('palette', {}).get('primary', {}).get('name', 'Muted Lilac')} {config.get('palette', {}).get('primary', {}).get('hex', '#AA98D6')}",
        f"- **Secondaire :** {config.get('palette', {}).get('secondary', {}).get('name', 'Cloud White')} {config.get('palette', {}).get('secondary', {}).get('hex', '#F8F6F2')}",
        f"- **Accent :** {config.get('palette', {}).get('accent', {}).get('name', 'Warm Sunset Orange')} {config.get('palette', {}).get('accent', {}).get('hex', '#E67A2E')}",
        f"- **Typo titres :** {config.get('typography', {}).get('header', {}).get('font', 'Figtree')}",
        f"- **Typo texte :** {config.get('typography', {}).get('body', {}).get('font', 'Inter')}",
        "",
        "## Humeur visuelle",
        "",
        f"- **Nom :** {visual.get('visual_mood', {}).get('name', 'Soft Intelligence')}",
        f"- **Promesse :** une IA accessible et enveloppée de douceur tactile ; une technologie qui ressemble davantage à une étreinte qu’à un écran.",
        "",
        "### Mots-clés à préserver",
        "",
    ]
    for keyword in visual.get("visual_mood", {}).get("keywords", [])[:8]:
        lines.append(f"- { _translate_keyword(keyword) }")

    lines.extend([
        "",
        "## Lecture de la palette",
        "",
    ])
    for color in palette:
        lines.append(f"### {color.get('name', 'Couleur')} — {color.get('hex', '')}")
        lines.append("")
        lines.append(f"- **Rôle :** { _translate_role(color.get('role', '')) }")
        if color.get("psychology"):
            lines.append(f"- **Effet recherché :** { _translate_psychology(color.get('psychology', '')) }")
        if color.get("usage"):
            lines.append(f"- **Usages :** { _translate_usage(color.get('usage', '')) }")
        lines.append("")

    lines.extend([
        "## Règles typographiques",
        "",
    ])
    header = typography.get("header", {})
    body = typography.get("body", {})
    lines.extend([
        f"- **Titres :** {header.get('family', 'Figtree')} pour conserver une géométrie ronde, amicale et haut de gamme.",
        f"- **Texte courant :** {body.get('family', 'Inter')} pour garder une lecture simple, claire et confortable.",
        "- **Toujours privilégier :** des tailles généreuses, un rythme respirant et une hiérarchie très lisible pour les parents.",
        "- **À éviter :** les graisses trop fines, les capitales agressives et tout traitement qui durcit la marque.",
        "",
        "## Direction photo & illustration",
        "",
        f"- **Photographie :** { _translate_sentence(imagery.get('photography_style', {}).get('description', '')) }",
        f"- **Traitement couleur :** { _translate_sentence(imagery.get('photography_style', {}).get('color_treatment', '')) }",
        f"- **Composition :** { _translate_sentence(imagery.get('photography_style', {}).get('composition', '')) }",
        f"- **Illustration :** { _translate_sentence(imagery.get('illustration_style', {}).get('description', '')) }",
        "",
        "### Environnements à privilégier",
        "",
    ])
    for item in imagery.get("environments", []):
        lines.append(f"- { _translate_environment(item) }")

    lines.extend([
        "",
        "### Contraintes non négociables",
        "",
    ])
    for item in imagery.get("constraints", []):
        lines.append(f"- { _translate_constraint(item) }")

    owned = competitor.get("visual_territory_owned", {})
    if owned:
        lines.extend([
            "",
            "## Territoire visuel à posséder",
            "",
            f"- **Couleur :** { _translate_sentence(owned.get('color', '')) }",
            f"- **Texture :** { _translate_sentence(owned.get('texture', '')) }",
            f"- **Personnalité :** { _translate_sentence(owned.get('personality', '')) }",
            f"- **Typographie :** { _translate_sentence(owned.get('typography', '')) }",
        ])

    if negative:
        lines.extend([
            "",
            "## Ce qu’il faut explicitement éviter",
            "",
        ])
        for item in negative[:10]:
            lines.append(f"- { _translate_avoid(item) }")

    lines.extend([
        "",
        "## Résumé d’usage",
        "",
        "Chaque surface ZackAI — portail, page produit, kit de marque, packaging, rendu héro ou asset NotebookLM surfacé — doit sembler douce, habitable et digne de confiance. Si un écran, une esthétique enterprise ou une froideur technique dominent la composition, la direction visuelle a échoué.",
    ])
    return "\n".join(lines) + "\n"


def _render_fr_voice_tone(outputs: Dict[str, Any]) -> str:
    voice = outputs.get("voice-and-tone", {})
    persona = voice.get("brand_persona", {})
    attributes = voice.get("voice_attributes", [])
    contexts = voice.get("tone_spectrum", {}).get("contexts", [])
    preferred = voice.get("vocabulary", {}).get("preferred_words", [])
    avoided = voice.get("vocabulary", {}).get("avoided_words", [])
    power_phrases = voice.get("vocabulary", {}).get("power_phrases", [])
    writing_rules = voice.get("writing_rules", [])
    bilingual = voice.get("bilingual_guidelines", {})
    sample = voice.get("sample_copy", {})

    lines = [
        "# Voix & ton",
        "",
        "Cette page définit la manière dont ZackAI doit parler aux parents, aux enfants et à la communauté. Le but n’est pas seulement de traduire le contenu en français, mais de faire entendre une marque qui semble réellement née dans cet univers : douce, claire, fiable et jamais gadget.",
        "",
        "## Persona de marque",
        "",
        f"- **Nom :** {persona.get('name', 'Zack')}",
        f"- **Archétype :** The Playful Guardian — protecteur, curieux, chaleureux, jamais infantilisant.",
        f"- **Style de communication :** { _translate_communication_style(persona.get('communication_style', '')) }",
        "",
        "### Traits à préserver",
        "",
    ]
    for item in persona.get("personality_traits", []):
        lines.append(f"- { _translate_personality_trait(item) }")

    lines.extend([
        "",
        "## Les 6 attributs de voix",
        "",
    ])
    for item in attributes:
        lines.append(f"### { _translate_voice_attribute_name(item.get('name', 'Attribut')) }")
        lines.append("")
        lines.append(_translate_voice_attribute_definition(item.get("definition", "")))
        lines.append("")
        if item.get("do"):
            lines.append(f"- **À faire :** { _translate_voice_example(item.get('do', '')) }")
        if item.get("dont"):
            lines.append(f"- **À éviter :** { _translate_voice_example(item.get('dont', '')) }")
        lines.append("")

    if contexts:
        lines.extend([
            "## Calibration par contexte",
            "",
            "La voix reste stable, mais le ton se déplace selon le moment du parcours. En France, ZackAI doit rester retenu, chaleureux et intelligible même quand le contexte devient plus commercial.",
            "",
        ])
        for item in contexts:
            lines.append(f"### { _translate_context_name(item.get('context', 'Contexte')) }")
            lines.append("")
            lines.append(f"- **Ton recherché :** { _translate_context_tone(item.get('tone', '')) }")
            lines.append(f"- **Chaleur :** {item.get('warmth', '')}/10")
            lines.append(f"- **Jeu :** {item.get('playfulness', '')}/10")
            lines.append(f"- **Professionnalisme :** {item.get('professionalism', '')}/10")
            if item.get("example"):
                lines.append(f"- **Exemple :** { _translate_context_example(item.get('example', '')) }")
            lines.append("")

    if preferred:
        lines.extend([
            "## Vocabulaire à privilégier",
            "",
        ])
        for item in preferred[:12]:
            lines.append(f"- { _translate_preferred_word(item) }")
    if avoided:
        lines.extend([
            "",
            "## Vocabulaire à éviter",
            "",
        ])
        for item in avoided[:12]:
            lines.append(f"- { _translate_avoided_word(item) }")

    if power_phrases:
        lines.extend([
            "",
            "## Formules fortes",
            "",
        ])
        for item in power_phrases[:8]:
            lines.append(f"- { _translate_power_phrase(item) }")

    if writing_rules:
        lines.extend([
            "",
            "## Règles d’écriture",
            "",
        ])
        for item in writing_rules:
            lines.append(f"- **{ _translate_writing_rule_name(item.get('rule', 'Règle')) } :** { _translate_writing_rule_desc(item.get('description', '')) }")

    if bilingual:
        lines.extend([
            "",
            "## Spécificité FR/EN",
            "",
            "Pour ZackAI, le français n’est pas une couche secondaire. Sur le marché France, la voix doit sembler pensée directement en français, avec une vraie sensibilité locale et sans anglicismes inutiles.",
            "",
        ])
        for item in bilingual.get("rules", []):
            lines.append(f"- **{ _translate_bilingual_rule_name(item.get('rule', 'Règle')) } :** { _translate_bilingual_rule_desc(item.get('description', '')) }")
        if bilingual.get("french_tone_notes"):
            lines.extend(["", bilingual.get("french_tone_notes"), ""])

    lines.extend([
        "## Exemples de sortie",
        "",
        f"- **Hero :** { _translate_sample_text(sample.get('website_hero', {}).get('headline', '')) }",
        f"- **Sous-hero :** { _translate_sample_text(sample.get('website_hero', {}).get('subheadline', '')) }",
        f"- **CTA :** { _translate_sample_text(sample.get('website_hero', {}).get('cta', '')) }",
        f"- **Push :** { _translate_sample_text(sample.get('push_notification', '')) }",
        f"- **Packaging :** { _translate_sample_text(sample.get('packaging_insert', '')) }",
    ])
    return "\n".join(lines) + "\n"


def _render_fr_product_features(outputs: Dict[str, Any]) -> str:
    detailed = outputs.get("detailed-product-description", {})
    campaign = outputs.get("campaign-page-copy", {})
    handoff = detailed.get("handoff", {})
    campaign_handoff = campaign.get("handoff", {})
    features = handoff.get("feature_breakdown", [])
    use_cases = handoff.get("use_cases", [])
    objections = handoff.get("objections_addressed", [])
    pillars = campaign_handoff.get("feature_pillars", [])
    sections = campaign_handoff.get("sections", [])

    lines = [
        "# Fonctionnalités produit",
        "",
        "![Capsule Collection](/images/3A-capsule-collection-nanobananapro-v1.png)",
        "",
        "![Product Detail](/images/3C-product-detail-nanobananapro-v1.png)",
        "",
        "Cette page traduit les capacités ZackAI en bénéfices vécus. On ne vend pas une fiche technique : on montre comment le produit devient un compagnon sans écran, fiable, doux et désirable dans le quotidien familial.",
        "",
        "## Les bénéfices cœur",
        "",
    ]
    for item in features:
        lines.append(f"- **{ _translate_feature_name(item.get('name', 'Fonction')) } :** { _translate_feature_benefit(item.get('benefit', '')) }")

    if pillars:
        lines.extend([
            "",
            "## Piliers à réactiver dans les pages produit",
            "",
        ])
        for item in pillars:
            lines.append(f"- { _translate_campaign_pillar(item) }")

    if sections:
        lines.extend([
            "",
            "## Ce que ces fonctionnalités doivent raconter",
            "",
        ])
        for item in sections[:4]:
            lines.append(f"- **{ _translate_campaign_section_title(item.get('title', 'Section')) } :** { _translate_campaign_section_copy(item.get('copy', '')) }")

    if use_cases:
        lines.extend([
            "",
            "## Moments d’usage",
            "",
        ])
        for item in use_cases:
            lines.append(f"- { _translate_use_case(item) }")

    if objections:
        lines.extend([
            "",
            "## Objections que les fonctionnalités doivent résoudre",
            "",
        ])
        for item in objections:
            lines.append(f"- { _translate_objection(item) }")

    lines.extend([
        "",
        "## Comment lire cette page en équipe",
        "",
        "- **Produit :** vérifier que chaque fonctionnalité reste attachée à un bénéfice humain clair.",
        "- **Créa :** montrer l’usage tactile, pas une techno abstraite.",
        "- **Copy :** rester dans la langue du réconfort, de la curiosité et de la confiance parentale.",
        "",
        "## Liens utiles",
        "",
        "- [Vue d’ensemble produit](/fr/docs/product/overview)",
        "- [Spécifications produit](/fr/docs/product/specifications)",
        "- [Copy de campagne](/fr/docs/marketing/campaign-copy)",
    ])
    return "\n".join(lines) + "\n"


def _render_fr_product_specifications(outputs: Dict[str, Any], config: Dict[str, Any]) -> str:
    hero = config.get("products", {}).get("hero", {})
    detailed = outputs.get("detailed-product-description", {}).get("handoff", {})
    materials = detailed.get("materials_and_safety", config.get("materials", []))
    proof_angles = detailed.get("proof_angles", [])

    lines = [
        "# Spécifications produit",
        "",
        "![Catalog Layout](/images/4A-catalog-layout-nanobananapro-v1.png)",
        "",
        "![Flatlay](/images/4B-flatlay-nanobananapro-v1.png)",
        "",
        "Cette page est la base canonique pour les équipes produit, créa et contenu. Elle fixe ce que ZackAI est, comment il se présente physiquement et quels signaux matériels doivent rester stables d’un rendu à l’autre.",
        "",
        "## Spécification canonique",
        "",
        f"- **Nom :** {hero.get('name', 'ZackAI Smart Plush — Phantom Purple')}",
        "- **Description :** compagnon d’apprentissage sans écran avec personnalité LED animée, douceur premium et logique sans abonnement.",
        f"- **Forme physique :** { _translate_physical_form(hero.get('physical_form', '')) }",
        "",
        "## Matériaux & composants visibles",
        "",
    ]
    for item in materials:
        lines.append(f"- { _translate_material(item) }")

    lines.extend([
        "",
        "## Principes de sécurité & de perception",
        "",
        "- Les composants doivent toujours se lire comme arrondis, sécurisés et intégrés à une enveloppe douce.",
        "- Aucun rendu ne doit faire glisser ZackAI vers une esthétique de gadget, robot ou smart speaker domestique.",
        "- La recharge USB-C existe comme détail fonctionnel, mais ne doit jamais devenir le sujet visuel principal.",
        "- Phantom Purple reste le point d’ancrage signature dans la lecture produit.",
    ])

    if proof_angles:
        lines.extend([
            "",
            "## Angles de preuve produits",
            "",
        ])
        for item in proof_angles:
            lines.append(f"- { _translate_proof_angle(item) }")

    lines.extend([
        "",
        "## Utilisation de cette spec",
        "",
        "- **Pour les rendus visuels :** garder la douceur, les oreilles félines, les yeux LED expressifs et la logique sans écran.",
        "- **Pour la copy :** traduire la spec en bénéfices vécus, pas en jargon technique.",
        "- **Pour le wiki :** toute contradiction entre cette page et les autres pages produit doit être traitée comme une dérive de spec.",
        "",
        "## Liens utiles",
        "",
        "- [Vue d’ensemble produit](/fr/docs/product/overview)",
        "- [Fonctionnalités produit](/fr/docs/product/features)",
    ])
    return "\n".join(lines) + "\n"


def _render_fr_email_templates(outputs: Dict[str, Any]) -> str:
    welcome = outputs.get("welcome-email-sequence", {}).get("handoff", {}).get("emails", [])
    prelaunch = outputs.get("pre-launch-email-sequence", {}).get("handoff", {}).get("emails", [])
    launch = outputs.get("launch-email-sequence", {}).get("handoff", {}).get("emails", [])

    lines = [
        "# Templates email",
        "",
        "Cette page structure les séquences email ZackAI en français pour garder un tunnel relationnel cohérent : accueil chaleureux, montée en désir avant le lancement, puis cadence de conversion claire pendant la campagne Kickstarter.",
        "",
        "## Séquence de bienvenue",
        "",
        "L’objectif de la séquence d’accueil est de faire sentir au nouvel inscrit qu’il rejoint un univers premium, doux et digne de confiance — pas simplement une liste email.",
        "",
    ]
    for item in welcome:
        lines.append(f"### { _translate_email_name(item.get('name', 'Email')) }")
        lines.append("")
        lines.append(f"- **Timing :** { _translate_timing(item.get('timing', '')) }")
        lines.append(f"- **Objet :** { _translate_email_subject(item.get('subject', '')) }")
        lines.append(f"- **Objectif :** { _translate_email_goal(item.get('goal', '')) }")
        if item.get("summary"):
            lines.append(f"- **Résumé :** { _translate_email_summary(item.get('summary', '')) }")
        lines.append("")

    lines.extend([
        "## Séquence de pré-lancement",
        "",
        "Cette séquence doit préparer des backers prêts à agir le jour J, en combinant histoire, confiance et anticipation.",
        "",
    ])
    for item in prelaunch:
        lines.append(f"### { _translate_email_name(item.get('name', 'Email')) }")
        lines.append("")
        lines.append(f"- **Timing :** { _translate_timing(item.get('timing', '')) }")
        lines.append(f"- **Objet :** { _translate_email_subject(item.get('subject', '')) }")
        lines.append(f"- **Objectif :** { _translate_email_goal(item.get('goal', '')) }")
        lines.append("")

    lines.extend([
        "## Séquence de lancement",
        "",
        "Le rythme de lancement doit rester énergique mais jamais agressif. Le ton ZackAI doit conserver sa chaleur et sa crédibilité, même quand l’urgence augmente.",
        "",
    ])
    for item in launch:
        lines.append(f"### { _translate_email_name(item.get('name', 'Email')) }")
        lines.append("")
        lines.append(f"- **Timing :** { _translate_timing(item.get('timing', '')) }")
        lines.append(f"- **Objet :** { _translate_email_subject(item.get('subject', '')) }")
        lines.append(f"- **Objectif :** { _translate_email_goal(item.get('goal', '')) }")
        if item.get("cta"):
            lines.append(f"- **CTA :** { _translate_campaign_cta(item.get('cta', '')) }")
        lines.append("")

    lines.extend([
        "## Règles de tonalité email",
        "",
        "- Toujours parler aux parents comme à des alliés déjà attentifs, jamais comme à une audience à convaincre par peur.",
        "- Garder des objets courts, humains et mémorisables.",
        "- Associer systématiquement le prix à l’absence d’abonnement quand le prix apparaît.",
        "- Utiliser la chaleur de ZackAI pour créer la relation, puis la précision produit pour créer la confiance.",
        "",
        "## Liens utiles",
        "",
        "- [Voix & ton](/fr/docs/brand/voice-tone)",
        "- [Copy de campagne](/fr/docs/marketing/campaign-copy)",
    ])
    return "\n".join(lines) + "\n"


def _render_fr_campaign_copy(outputs: Dict[str, Any]) -> str:
    campaign = outputs.get("campaign-page-copy", {})
    handoff = campaign.get("handoff", {})
    sections = handoff.get("sections", [])
    pillars = handoff.get("feature_pillars", [])
    objections = handoff.get("objections", [])
    ctas = handoff.get("cta_language", [])
    rewards = handoff.get("rewards_framing", [])
    faq = handoff.get("faq", [])
    social_proof = handoff.get("social_proof_angles", [])

    lines = [
        "# Copy de campagne",
        "",
        "Le messaging Kickstarter ZackAI doit tenir une ligne claire : partir de la fatigue écran, ouvrir une vision plus douce de la technologie, puis démontrer que le produit réunit jeu, apprentissage, confiance parentale et émotion.",
        "",
        "## Titre & sous-titre de campagne",
        "",
        f"- **Titre recommandé :** Compagnon de jeu sans écran",
        f"- **Sous-titre recommandé :** ZackAI associe le réconfort d’une peluche à une IA conversationnelle, une personnalité LED expressive et un apprentissage multilingue — sans écran ni abonnement.",
        "",
        "## Structure de page Kickstarter",
        "",
    ]
    for section in sections:
        lines.append(f"### { _translate_campaign_section_title(section.get('title', 'Section')) }")
        lines.append("")
        lines.append(_translate_campaign_section_copy(section.get("copy", "")))
        lines.append("")

    if pillars:
        lines.extend([
            "## Piliers à marteler",
            "",
        ])
        for item in pillars:
            lines.append(f"- { _translate_campaign_pillar(item) }")

    if objections:
        lines.extend([
            "",
            "## Objections à désamorcer tôt",
            "",
        ])
        for item in objections:
            lines.append(f"- { _translate_campaign_objection(item) }")

    if ctas:
        lines.extend([
            "",
            "## Langage CTA à privilégier",
            "",
        ])
        for item in ctas:
            lines.append(f"- { _translate_campaign_cta(item) }")

    if rewards:
        lines.extend([
            "",
            "## Framing des rewards",
            "",
        ])
        for item in rewards:
            lines.append(f"- **{ _translate_reward_tier(item.get('tier', 'Palier')) } :** { _translate_reward_offer(item.get('offer', '')) }")

    if faq:
        lines.extend([
            "",
            "## FAQ de base",
            "",
        ])
        for item in faq:
            lines.append(f"- **{ _translate_faq_question(item.get('q', 'Question')) }** { _translate_faq_answer(item.get('a', '')) }")

    if social_proof:
        lines.extend([
            "",
            "## Preuves sociales à faire remonter",
            "",
        ])
        for item in social_proof:
            lines.append(f"- { _translate_social_proof(item) }")

    lines.extend([
        "",
        "## Ligne éditoriale recommandée",
        "",
        "- Toujours parler à des parents déjà informés, jamais à une audience qu’il faudrait éduquer de façon paternaliste.",
        "- Garder un ton premium, chaleureux et calme — pas techno-agressif, pas trop enfantin.",
        "- Introduire l’IA comme un moyen au service du lien, de l’éveil et du rituel familial, jamais comme une performance froide.",
        "",
        "## Liens utiles",
        "",
        "- [Voir la vue d’ensemble produit](/fr/docs/product/overview)",
        "- [Ouvrir le hub NotebookLM](/fr/docs/research/notebooklm-artifacts)",
    ])
    return "\n".join(lines) + "\n"


def _render_fr_quickstart(config_path: Path, brand_dir: Path, notebooklm: Dict[str, Any]) -> str:
    lines = [
        "# Démarrage rapide",
        "",
        "Utilisez cette page pour retrouver rapidement les outputs clés du run `beta-update`, sans perdre le fil entre configuration, visuels, wiki et artefacts de recherche.",
        "",
        "## Chemins principaux",
        "",
        f"- **Configuration :** `{config_path}`",
        f"- **Outputs JSON :** `{brand_dir / '.brandmint' / 'outputs'}`",
        f"- **Visuels générés :** `{brand_dir / 'zackai' / 'generated'}`",
        f"- **Artefacts NotebookLM :** `{brand_dir / 'deliverables' / 'notebooklm' / 'artifacts'}`",
        f"- **Markdown wiki EN :** `{brand_dir / 'wiki-output'}`",
        f"- **Markdown wiki FR :** `{brand_dir / 'wiki-output-fr'}`",
        f"- **Projet Astro :** `{brand_dir / 'wiki-site'}`",
        f"- **Build publié :** `{brand_dir / 'wiki-site' / 'dist'}`",
        "",
        "## Politique de références produit",
        "",
        "- Les sources image NotebookLM du run isolé sont limitées aux photos produit configurées dans `beta-update/products/`.",
        "- Les visuels Brandmint restent distincts des assets NotebookLM pour éviter les contaminations inter-run.",
        "- Le portail Wave 8 surfacera maintenant les artefacts NotebookLM comme des objets de recherche de premier ordre, pas comme des pièces jointes secondaires.",
        "",
        "## Couverture NotebookLM",
        "",
        f"- **Rapports :** {len(notebooklm.get('reports', []))}",
        f"- **Infographies :** {len(notebooklm.get('infographics', []))}",
        f"- **Decks :** {len(notebooklm.get('decks', []))}",
        f"- **Audio :** {len(notebooklm.get('audio', []))}",
        f"- **Assets structurés :** {len(notebooklm.get('tables', [])) + len(notebooklm.get('flashcards', [])) + len(notebooklm.get('quizzes', [])) + len(notebooklm.get('mind_maps', []))}",
        "",
        "## Navigation recommandée",
        "",
        "1. Commencez par la [vue d’ensemble produit](/fr/docs/product/overview) pour recaler la promesse ZackAI.",
        "2. Ouvrez ensuite les [lignes directrices visuelles](/fr/docs/brand/visual-guidelines) pour garder la cohérence esthétique.",
        "3. Passez à la [copy de campagne](/fr/docs/marketing/campaign-copy) pour vérifier le narratif Kickstarter.",
        "4. Terminez par les [artefacts NotebookLM](/fr/docs/research/notebooklm-artifacts) pour explorer les rapports, decks et synthèses.",
    ]
    return "\n".join(lines) + "\n"


def _render_fr_social_content(outputs: Dict[str, Any]) -> str:
    social = outputs.get("social-content-engine", {}).get("handoff", {})
    outreach = outputs.get("influencer-outreach-pro", {}).get("handoff", {})

    lines = [
        "# Contenu social",
        "",
        "Cette page traduit le rythme social ZackAI en plan d’exécution français : quoi publier, où, avec quel ton et quels relais créateurs. L’objectif est de garder une présence chaude, premium et crédible, alignée avec le tempo Kickstarter.",
        "",
        "## Piliers éditoriaux",
        "",
    ]
    for item in social.get("content_pillars", []):
        lines.append(f"- { _translate_campaign_pillar(item) }")

    lines.extend([
        "",
        "## Concepts de posts à produire",
        "",
    ])
    for item in social.get("post_concepts", []):
        lines.append(f"- { _translate_post_concept(item) }")

    channel_adaptations = social.get("channel_adaptations", {})
    if channel_adaptations:
        lines.extend([
            "",
            "## Adaptation par canal",
            "",
            f"- **Instagram :** { _translate_channel_adaptation(channel_adaptations.get('instagram', '')) }",
            f"- **X :** { _translate_channel_adaptation(channel_adaptations.get('x', '')) }",
            f"- **LinkedIn :** { _translate_channel_adaptation(channel_adaptations.get('linkedin', '')) }",
            f"- **Cadence :** { _translate_channel_adaptation(social.get('publishing_cadence', '')) }",
        ])

    if social.get("cta_ideas"):
        lines.extend(["", "## CTA sociaux", ""])
        for item in social.get("cta_ideas", []):
            lines.append(f"- { _translate_social_cta(item) }")

    if social.get("community_prompts"):
        lines.extend(["", "## Prompts communauté", ""])
        for item in social.get("community_prompts", []):
            lines.append(f"- { _translate_community_prompt(item) }")

    if outreach:
        lines.extend([
            "",
            "## Créateurs & outreach",
            "",
            "La stratégie créateurs doit privilégier les communautés qui valorisent la parentalité intentionnelle, l’apprentissage, le design et la confiance. ZackAI ne doit jamais être présenté comme un gadget tendance : il doit apparaître comme un compagnon crédible et désirable.",
            "",
        ])
        for item in outreach.get("creator_segments", []):
            lines.append(f"- **Segment :** { _translate_creator_segment(item) }")
        lines.extend(["", "### Angles d’outreach", ""])
        for item in outreach.get("outreach_angles", []):
            lines.append(f"- { _translate_outreach_angle(item) }")
        sample_messages = outreach.get("sample_messages", {})
        if sample_messages:
            lines.extend([
                "",
                f"- **DM type :** { _translate_sample_outreach(sample_messages.get('dm', '')) }",
                f"- **Email type :** { _translate_sample_outreach(sample_messages.get('email', '')) }",
            ])
        if outreach.get("collaboration_concepts"):
            lines.extend(["", "### Formats de collaboration", ""])
            for item in outreach.get("collaboration_concepts", []):
                lines.append(f"- { _translate_collab_concept(item) }")
        if outreach.get("gifting_strategy"):
            lines.extend(["", f"- **Gifting :** { _translate_gifting_strategy(outreach.get('gifting_strategy', '')) }"])
        if outreach.get("measurement_ideas"):
            lines.extend(["", "### Mesures à suivre", ""])
            for item in outreach.get("measurement_ideas", []):
                lines.append(f"- { _translate_measurement_idea(item) }")

    return "\n".join(lines) + "\n"


def _render_fr_video_scripts(outputs: Dict[str, Any]) -> str:
    video = outputs.get("campaign-video-script", {}).get("handoff", {})
    lines = [
        "# Scripts vidéo",
        "",
        "Le film ZackAI doit faire sentir la tension du quotidien saturé d’écrans, puis ouvrir une alternative chaleureuse : un compagnon doux, intelligent et crédible qui accompagne l’enfant sans casser le rythme émotionnel de la maison.",
        "",
        "## Hook d’ouverture",
        "",
        f"- **Hook recommandé :** { _translate_video_hook(video.get('opening_hook', '')) }",
        "",
        "## Arc narratif",
        "",
    ]
    for item in video.get("story_arc", []):
        lines.append(f"- { _translate_story_arc(item) }")

    if video.get("scene_beats"):
        lines.extend(["", "## Découpage des scènes", ""])
        for item in video.get("scene_beats", []):
            lines.append(f"- { _translate_scene_beat(item) }")

    if video.get("voiceover"):
        lines.extend(["", "## Voix off", ""])
        for item in video.get("voiceover", []):
            lines.append(f"- { _translate_voiceover_line(item) }")

    if video.get("on_screen_text"):
        lines.extend(["", "## Texte écran", ""])
        for item in video.get("on_screen_text", []):
            lines.append(f"- { _translate_onscreen_text(item) }")

    if video.get("proof_moments"):
        lines.extend(["", "## Moments de preuve", ""])
        for item in video.get("proof_moments", []):
            lines.append(f"- { _translate_proof_moment(item) }")

    if video.get("cta"):
        lines.extend(["", f"- **CTA final :** { _translate_campaign_cta(video.get('cta', '')) }"])

    return "\n".join(lines) + "\n"


def _render_fr_ad_creative(outputs: Dict[str, Any]) -> str:
    pre = outputs.get("pre-launch-ads", {}).get("handoff", {})
    live = outputs.get("live-campaign-ads", {}).get("handoff", {})

    lines = [
        "# Création publicitaire",
        "",
        "Cette page organise les angles paid media ZackAI avant et pendant la campagne. Le cadre reste constant : montrer une alternative chaleureuse, sans écran et digne de confiance, puis convertir cette promesse en momentum réel quand la campagne est live.",
        "",
        "## Ads de pré-lancement",
        "",
        "Le pré-lancement doit construire l’envie et la qualité perçue autour d’une idée simple : ZackAI est une réponse plus douce, plus sûre et plus désirable que les technologies enfant trop centrées sur l’écran.",
        "",
    ]
    for item in pre.get("audience_segments", []):
        lines.append(f"- **Segment audience :** { _translate_audience_segment(item) }")
    if pre.get("hooks"):
        lines.extend(["", "### Hooks", ""])
        for item in pre.get("hooks", []):
            lines.append(f"- { _translate_ad_hook(item) }")
    if pre.get("headline_variants"):
        lines.extend(["", "### Titres", ""])
        for item in pre.get("headline_variants", []):
            lines.append(f"- { _translate_ad_headline(item) }")
    if pre.get("body_copy_variants"):
        lines.extend(["", "### Variantes de body copy", ""])
        for item in pre.get("body_copy_variants", []):
            lines.append(f"- { _translate_ad_body(item) }")
    if pre.get("cta_variants"):
        lines.extend(["", "### CTA", ""])
        for item in pre.get("cta_variants", []):
            lines.append(f"- { _translate_ad_cta(item) }")
    if pre.get("creative_direction"):
        lines.extend(["", "### Direction créative", ""])
        for item in pre.get("creative_direction", []):
            lines.append(f"- { _translate_creative_direction(item) }")
    if pre.get("angles_to_test"):
        lines.extend(["", "### Angles à tester", ""])
        for item in pre.get("angles_to_test", []):
            lines.append(f"- { _translate_campaign_pillar(item) }")

    lines.extend([
        "",
        "## Ads live campaign",
        "",
        "Une fois la campagne lancée, le paid doit passer d’une logique promesse à une logique momentum : des familles soutiennent déjà ZackAI, les paliers bougent, et il reste du temps pour rejoindre la première vague.",
        "",
    ])
    for item in live.get("campaign_stage_segments", []):
        lines.append(f"- **Segment de campagne :** { _translate_campaign_stage(item) }")
    if live.get("hooks"):
        lines.extend(["", "### Hooks live", ""])
        for item in live.get("hooks", []):
            lines.append(f"- { _translate_live_hook(item) }")
    if live.get("copy_variants"):
        lines.extend(["", "### Variantes de copy", ""])
        for item in live.get("copy_variants", []):
            lines.append(f"- { _translate_live_copy(item) }")
    if live.get("urgency_messages"):
        lines.extend(["", "### Messages d’urgence", ""])
        for item in live.get("urgency_messages", []):
            lines.append(f"- { _translate_urgency_message(item) }")
    if live.get("retargeting_angles"):
        lines.extend(["", "### Retargeting", ""])
        for item in live.get("retargeting_angles", []):
            lines.append(f"- { _translate_retargeting_angle(item) }")
    if live.get("creative_guidance"):
        lines.extend(["", "### Guidance créative", ""])
        for item in live.get("creative_guidance", []):
            lines.append(f"- { _translate_live_creative(item) }")

    return "\n".join(lines) + "\n"


def _render_fr_visual_assets(outputs: Dict[str, Any], notebooklm: Dict[str, Any]) -> str:
    lines = [
        "# Bibliothèque visuelle",
        "",
        "Cette bibliothèque rassemble les surfaces visuelles réellement produites pour ZackAI pendant le run beta-update. Elle sert autant de galerie que de référence de cohérence : chaque image doit prolonger la douceur, la confiance et la logique sans écran de la marque.",
        "",
        "## Assets Brandmint générés",
        "",
        "- **2A — Brand Kit Bento Grid :** pose la lecture globale du système de marque, de la palette et des codes doux/premium.",
        "- **2B — Brand Seal :** encode la crédibilité, la signature visuelle et la lecture plus institutionnelle de ZackAI.",
        "- **2C — Logo Emboss :** matérialise le langage de matière, d’empreinte et de qualité perçue.",
        "- **3A — Capsule Collection :** montre la logique de gamme et la lecture multi-coloris sans sortir du territoire ZackAI.",
        "- **3B — Hero Product :** reste l’image de référence du compagnon ZackAI dans sa lecture la plus iconique.",
        "- **3C — Product Detail :** insiste sur la matérialité, les détails rassurants et la sensation tactile.",
        "- **4A — Catalog Layout :** aide à penser les supports de présentation et de collection.",
        "- **4B — Flatlay :** donne une lecture plus cataloguée et explicite des composants visibles.",
        "",
        "## Infographies NotebookLM",
        "",
        f"- **Infographies disponibles :** {len(notebooklm.get('infographics', []))}",
        "- Elles complètent la bibliothèque comme surfaces de recherche visuelle, sans remplacer les images Brandmint de référence.",
        "- Elles doivent être utilisées pour enrichir la compréhension, pas pour redéfinir le territoire esthétique principal.",
        "",
        "## Comment utiliser cette bibliothèque",
        "",
        "- Revenir ici avant toute nouvelle déclinaison créative pour vérifier qu’on reste dans le territoire ZackAI.",
        "- Prioriser les assets qui montrent les mains, la douceur, la lumière chaude et la proximité émotionnelle.",
        "- Écarter toute lecture trop tech, trop froide, trop robotique ou trop écran-centric.",
    ]
    return "\n".join(lines) + "\n"


def _render_fr_primary_persona(outputs: Dict[str, Any]) -> str:
    persona = outputs.get("buyer-persona", {})
    demographics = persona.get("demographics", {})
    psychographics = persona.get("psychographics", {})

    lines = [
        "# Persona principal",
        "",
        "Le persona cœur ZackAI est **le parent intentionnel** : un parent informé, exigeant, souvent urbain, qui refuse de choisir entre technologie et limites saines. Il ne cherche pas un gadget enfant de plus ; il cherche un compagnon crédible, durable et émotionnellement juste.",
        "",
        "## Profil synthétique",
        "",
        f"- **Âge :** {demographics.get('age_range', '30-42')}",
        f"- **Situation familiale :** { _translate_persona_sentence(demographics.get('family_status', '')) }",
        f"- **Géographie :** { _translate_persona_sentence(demographics.get('location', '')) }",
        f"- **Rapport à la tech :** { _translate_persona_sentence(demographics.get('tech_comfort', '')) }",
        "",
        "## Valeurs profondes",
        "",
    ]
    for item in psychographics.get("values", [])[:8]:
        lines.append(f"- { _translate_value(item) }")
    lines.extend(["", "## Peurs majeures", ""])
    for item in psychographics.get("fears", [])[:6]:
        lines.append(f"- { _translate_persona_sentence(item) }")
    lines.extend(["", "## Aspirations", ""])
    for item in psychographics.get("aspirations", [])[:5]:
        lines.append(f"- { _translate_persona_sentence(item) }")
    lines.extend(["", "## Frustrations quotidiennes", ""])
    for item in psychographics.get("daily_frustrations", [])[:6]:
        lines.append(f"- { _translate_persona_sentence(item) }")
    lines.extend(["", "## Ce qui le fait acheter", ""])
    for item in persona.get("buying_triggers", [])[:8]:
        lines.append(f"- { _translate_persona_sentence(item) }")
    lines.extend(["", "## Objections à lever", ""])
    for item in persona.get("objections", [])[:4]:
        lines.append(f"- **Objection :** { _translate_persona_sentence(item.get('objection', '')) }")
        lines.append(f"  **Réponse :** { _translate_persona_sentence(item.get('counter', '')) }")
    lines.extend(["", "## Résumé utile pour l’équipe", "", _translate_persona_sentence(persona.get("persona_summary", ""))])
    return "\n".join(lines) + "\n"


def _render_fr_secondary_personas(outputs: Dict[str, Any]) -> str:
    persona = outputs.get("buyer-persona", {})
    lines = [
        "# Personas secondaires",
        "",
        "Autour du parent intentionnel, ZackAI touche plusieurs segments voisins qui n’entrent pas exactement par la même porte. Cette page sert à garder ces nuances visibles dans le récit de campagne, le paid, les creators et les angles de preuve.",
        "",
        "## Segments adjacents à privilégier",
        "",
        "- **Familles bilingues / expatriées :** voient ZackAI comme un outil de continuité linguistique et émotionnelle.",
        "- **Acheteurs cadeau premium :** recherchent un objet marquant, beau et approuvé par les parents.",
        "- **Parents Montessori-friendly :** veulent une technologie qui respecte l’autonomie, le calme et le jeu ouvert.",
        "- **Parents épuisés par le coucher :** entrent par la promesse de rituel apaisé et de compagnon rassurant.",
        "",
        "## Besoins transverses à garder visibles",
        "",
    ]
    for item in persona.get("buying_triggers", [])[:6]:
        lines.append(f"- { _translate_persona_sentence(item) }")
    lines.extend([
        "",
        "## Signaux qui parlent à ces personas",
        "",
        "- conformité RGPD / CE / EN71",
        "- sans abonnement",
        "- 40+ langues",
        "- compagnon physique, pas simple device audio",
        "- esthétique premium et rassurante",
        "",
        "## Usage stratégique",
        "",
        "- Utiliser cette page pour nuancer le paid, les creators et les pages de campagne selon les motivations d’entrée.",
        "- Ne jamais casser l’unité du récit ZackAI : les personas secondaires sont des portes d’entrée, pas des repositionnements séparés.",
    ])
    return "\n".join(lines) + "\n"


def _render_fr_competitive_landscape(outputs: Dict[str, Any]) -> str:
    analysis = outputs.get("competitor-analysis", {})
    competitors = analysis.get("competitors", [])
    differentiators = analysis.get("zackai_differentiators", [])
    gaps = analysis.get("market_gaps_exploited", [])
    recs = analysis.get("strategic_recommendations", [])

    lines = [
        "# Paysage concurrentiel",
        "",
        "Cette page synthétise la lecture concurrentielle ZackAI en français : qui occupe déjà l’espace mental des parents, où se trouvent les vraies menaces, et pourquoi ZackAI garde un territoire distinct quand il parle de douceur, de multilinguisme et de confiance.",
        "",
        "## Lecture rapide du marché",
        "",
    ]
    for item in competitors[:5]:
        lines.append(f"- **{item.get('name', 'Concurrent')} :** { _translate_competitor_summary(item) }")

    if differentiators:
        lines.extend(["", "## Différenciateurs ZackAI", ""])
        for item in differentiators:
            lines.append(f"- **{ _translate_competitive_differentiator(item.get('differentiator', '')) } :** { _translate_competitive_why(item.get('why_it_wins', '')) }")

    if gaps:
        lines.extend(["", "## Gaps de marché exploités", ""])
        for item in gaps:
            lines.append(f"- { _translate_persona_sentence(item) }")

    if analysis.get("visual_differentiation_strategy"):
        visual = analysis.get("visual_differentiation_strategy", {})
        lines.extend(["", "## Différenciation visuelle", ""])
        for item in visual.get("avoid", [])[:5]:
            lines.append(f"- **À éviter :** { _translate_persona_sentence(item) }")
        for item in visual.get("own", [])[:5]:
            lines.append(f"- **À posséder :** { _translate_persona_sentence(item) }")

    if analysis.get("pricing_analysis"):
        pricing = analysis.get("pricing_analysis", {})
        lines.extend(["", "## Lecture pricing", "", f"- **Verdict :** { _translate_persona_sentence(pricing.get('verdict', '')) }"])

    if recs:
        lines.extend(["", "## Recommandations stratégiques", ""])
        for item in recs[:6]:
            lines.append(f"- { _translate_persona_sentence(item) }")

    return "\n".join(lines) + "\n"


def _render_fr_notebooklm_artifacts(notebooklm: Dict[str, Any]) -> str:
    counts = notebooklm.get("counts", {})
    lines = [
        "# Artefacts NotebookLM",
        "",
        "Les outputs NotebookLM sont publiés comme une couche de recherche à part entière dans Wave 8. Ils complètent le récit de marque ZackAI par des rapports, decks, infographies, audio et exports structurés directement consultables depuis le wiki.",
        "",
        "## Couverture",
        "",
        f"- **Rapports :** {counts.get('reports', 0)}",
        f"- **Decks :** {counts.get('decks', 0)}",
        f"- **Audio :** {counts.get('audio', 0)}",
        f"- **Infographies :** {counts.get('infographics', 0)}",
        f"- **Tables :** {counts.get('tables', 0)}",
        f"- **Flashcards :** {counts.get('flashcards', 0)}",
        f"- **Quiz :** {counts.get('quizzes', 0)}",
        f"- **Cartes mentales :** {counts.get('mind_maps', 0)}",
        "",
        "## Rapports",
        "",
    ]

    reports = notebooklm.get("reports", [])
    if reports:
        for artifact in reports:
            doc_href = artifact.get("doc_href", "/docs/research/notebooklm-artifacts").replace("/docs/", "/fr/docs/")
            lines.append(f"### [{artifact.get('title', 'Rapport')}]({doc_href})")
            lines.append("")
            if artifact.get("summary"):
                lines.append(_translate_sentence(artifact["summary"]))
                lines.append("")
            lines.append(f"- **Page wiki :** [{doc_href}]({doc_href})")
            lines.append(f"- **Artefact brut :** `{artifact.get('route', '')}`")
            lines.append("")
    else:
        lines.extend(["_Aucun rapport NotebookLM n’a été détecté pour ce run._", ""])

    lines.extend(["## Infographies", ""])
    infographics = notebooklm.get("infographics", [])
    if infographics:
        for artifact in infographics:
            lines.append(f"### {artifact.get('title', 'Infographie')}")
            lines.append("")
            lines.append(f"![{artifact.get('title', 'Infographie')}]({artifact.get('route', '')})")
            lines.append("")
            lines.append(f"- **Téléchargement :** [{artifact.get('file', '')}]({artifact.get('route', '')})")
            lines.append("")
    else:
        lines.extend(["_Aucune infographie NotebookLM n’a été détectée pour ce run._", ""])

    lines.extend(_render_fr_artifact_group("Decks", notebooklm.get("decks", [])))
    lines.extend(_render_fr_artifact_group("Briefs audio", notebooklm.get("audio", [])))
    lines.extend(_render_fr_artifact_group("Tables de données", notebooklm.get("tables", []), show_shape=True))
    lines.extend(_render_fr_artifact_group("Flashcards", notebooklm.get("flashcards", []), show_shape=True))
    lines.extend(_render_fr_artifact_group("Quiz", notebooklm.get("quizzes", []), show_shape=True))
    lines.extend(_render_fr_artifact_group("Mind maps", notebooklm.get("mind_maps", []), show_shape=True))
    return "\n".join(lines) + "\n"


def _render_fr_artifact_group(heading: str, artifacts: List[Dict[str, Any]], show_shape: bool = False) -> List[str]:
    lines = [f"## {heading}", ""]
    if not artifacts:
        lines.append(f"_Aucun élément disponible dans la section {heading.lower()} pour ce run._")
        lines.append("")
        return lines

    for artifact in artifacts:
        lines.append(f"### {artifact.get('title', 'Artefact')}")
        lines.append("")
        lines.append(_translate_artifact_summary(artifact.get("summary", artifact.get("kind", "Artefact"))))
        lines.append("")
        if show_shape:
            if artifact.get("row_count") is not None:
                lines.append(f"- **Lignes :** {artifact['row_count']}")
            if artifact.get("columns"):
                lines.append(f"- **Colonnes :** {', '.join(artifact['columns'])}")
            if artifact.get("item_count") is not None:
                lines.append(f"- **Items :** {artifact['item_count']}")
        lines.append(f"- **Téléchargement :** [{artifact.get('file', '')}]({artifact.get('route', '')})")
        lines.append("")
    return lines


def _translate_communication_style(value: str) -> str:
    if not value:
        return value
    return (
        "Zack parle comme un grand frère bienveillant ou comme un narrateur de livre préféré : plein d’émerveillement, jamais condescendant, toujours sûr. "
        "Avec les parents, Zack devient un allié informé et empathique, qui respecte leurs valeurs autour du sans écran, du multilinguisme et d’une parentalité intentionnelle. "
        "La voix reste simple sans être simpliste, chaleureuse sans être mièvre, et confiante sans jamais devenir insistante."
    )


def _translate_personality_trait(value: str) -> str:
    translations = {
        "Warm and nurturing": "chaleureux et nourrissant",
        "Playfully curious": "curieux avec légèreté",
        "Gently encouraging": "encourageant avec douceur",
        "Reassuringly calm": "calme et rassurant",
        "Imaginatively adventurous": "imaginatif et ouvert à l’aventure",
        "Patient and inclusive": "patient et inclusif",
        "Trustworthy and transparent": "fiable et transparent",
    }
    return translations.get(value, value)


def _translate_voice_attribute_name(value: str) -> str:
    translations = {
        "Warm": "Chaleureux",
        "Playful": "Ludique",
        "Reassuring": "Rassurant",
        "Simple": "Simple",
        "Empowering": "Valorisant",
        "Inclusive": "Inclusif",
    }
    return translations.get(value, value)


def _translate_voice_attribute_definition(value: str) -> str:
    translations = {
        "Every word should feel like a cosy blanket — safe, inviting, and full of care.": "Chaque mot doit donner l’impression d’une couverture douce : sûr, accueillant et plein d’attention.",
        "Infuse delight and gentle humour into communication without undermining trust or clarity.": "Introduire de la joie et un humour léger sans jamais fragiliser la clarté ni la confiance.",
        "Parents need to feel confident that ZackAI is safe, private, and beneficial. Every parent-facing message should radiate trust.": "Les parents doivent sentir immédiatement que ZackAI est sûr, respectueux de la vie privée et réellement utile. Chaque message parent doit respirer la confiance.",
        "Clarity is kindness. Use short sentences, familiar words, and a natural rhythm that works across languages.": "La clarté est une forme de bienveillance. Utiliser des phrases courtes, un vocabulaire familier et un rythme naturel qui fonctionne d’une langue à l’autre.",
        "Position the child as the hero of every story. Zack is the sidekick, not the star.": "Toujours placer l’enfant comme héros du récit. Zack est le compagnon, jamais la vedette principale.",
        "Reflect the diversity of families, languages, and learning styles without tokenism.": "Refléter la diversité des familles, des langues et des manières d’apprendre sans tomber dans le cliché ni le signalement forcé.",
    }
    return translations.get(value, value)


def _translate_voice_example(value: str) -> str:
    replacements = {
        "Use sensory, emotionally resonant language": "Utiliser un langage sensoriel et émotionnellement résonant",
        "Use light wordplay and curiosity-driven phrasing": "Utiliser un jeu de langage léger et des formulations qui nourrissent la curiosité",
        "Lead with clarity and evidence": "Commencer par la clarté et la preuve",
        "Write at a reading age of 10–12 for parent content, 6–8 for child-facing copy": "Écrire à un niveau de lecture simple et fluide pour les parents comme pour les contenus adressés à l’enfant",
        "Centre the child's agency": "Mettre l’initiative de l’enfant au centre",
        "Use universal scenarios and gender-neutral defaults": "Utiliser des situations universelles et des formulations inclusives par défaut",
        "Don't use cold, transactional language": "Éviter un langage froid et transactionnel",
        "Don't force jokes, use sarcasm, or be silly in moments that require reassurance or safety information.": "Ne pas forcer les blagues, le sarcasme ou la bouffonnerie dans les moments qui demandent de la réassurance.",
        "Don't be defensive or legalistic": "Ne pas devenir défensif ou pseudo-juridique",
        "Don't use jargon, acronyms without explanation, or complex clause structures": "Éviter le jargon, les sigles opaques et les phrases inutilement complexes",
        "Don't make the AI the protagonist": "Ne pas faire de l’IA le protagoniste",
        "Don't assume family structure, language background, or ability": "Ne pas présumer la structure familiale, l’origine linguistique ou les capacités de l’enfant",
    }
    for src, dst in replacements.items():
        value = value.replace(src, dst)
    return value


def _translate_context_name(value: str) -> str:
    translations = {
        "Packaging & Unboxing": "Packaging & unboxing",
        "Social Media": "Réseaux sociaux",
        "Website (Hero & Product Pages)": "Site web (hero et pages produit)",
        "Advertising (Paid)": "Publicité payante",
        "Email (Lifecycle & Nurture)": "Email (lifecycle & nurture)",
        "Customer Support": "Support client",
    }
    return translations.get(value, value)


def _translate_context_tone(value: str) -> str:
    translations = {
        "Maximum wonder and delight": "merveille et joie maximales",
        "Playful, shareable, community-driven": "ludique, partageable et porté par la communauté",
        "Warm confidence with clear value propositions": "confiance chaleureuse avec proposition de valeur très lisible",
        "Emotionally compelling with a clear call to action": "émotionnellement fort avec appel à l’action clair",
        "Friendly, personal, gently informative": "amical, personnel et doucement informatif",
        "Calm, empathetic, solution-oriented": "calme, empathique et orienté solution",
    }
    return translations.get(value, value)


def _translate_context_example(value: str) -> str:
    replacements = {
        "Salut! I'm Zack. Squeeze me, talk to me, and let's explore the world together.": "Salut ! Moi, c’est Zack. Serre-moi dans tes bras, parle-moi, et partons explorer le monde ensemble.",
        "Bedtime story in three languages? Zack doesn't even need a bookmark.": "Une histoire du soir en trois langues ? Zack n’a même pas besoin de marque-page.",
        "A fluffy learning companion that speaks 40+ languages, needs no screen, and never runs out of patience.": "Un compagnon d’apprentissage tout doux qui parle 40+ langues, n’a besoin d’aucun écran et ne manque jamais de patience.",
        "Screen-free. Subscription-free. Worry-free. Meet ZackAI — EUR 99, everything included.": "Sans écran. Sans abonnement. Sans charge mentale. Découvrez ZackAI — EUR 99, tout est inclus.",
        "This week, Zack learned 3 new bedtime stories. Your little one might like the one about the cloud who wanted to be a mountain.": "Cette semaine, Zack a appris trois nouvelles histoires du soir. La vôtre aimera peut-être celle du nuage qui voulait devenir montagne.",
        "We're sorry Zack isn't responding as expected. Let's get your companion back on track — here are two quick steps.": "Nous sommes désolés : Zack ne répond pas comme prévu. Reprenons calmement — voici deux étapes simples.",
    }
    return replacements.get(value, value)


def _translate_preferred_word(value: str) -> str:
    translations = {
        "companion": "compagnon",
        "adventure": "aventure",
        "explore": "explorer",
        "discover": "découvrir",
        "imagine": "imaginer",
        "wonder": "émerveillement",
        "learn": "apprendre",
        "play": "jouer",
        "safe": "sûr",
        "together": "ensemble",
        "screen-free": "sans écran",
        "curiosity": "curiosité",
        "family": "famille",
        "story": "histoire",
        "gentle": "doux",
        "cosy": "cocon",
        "multilingual": "multilingue",
        "included": "inclus",
        "privacy-first": "respect de la vie privée d’abord",
        "grows with": "grandit avec",
    }
    return translations.get(value, value)


def _translate_avoided_word(value: str) -> str:
    translations = {
        "smart toy": "smart toy",
        "edtech": "edtech",
        "algorithm": "algorithm",
        "AI-powered": "AI-powered",
        "machine learning": "machine learning",
        "data collection": "data collection",
        "monetise": "monetise",
        "subscription": "subscription",
        "upsell": "upsell",
        "screen time": "screen time",
        "device": "device",
        "unit": "unit",
    }
    return translations.get(value, value)


def _translate_power_phrase(value: str) -> str:
    translations = {
        "Learning feels like play": "Apprendre ressemble enfin à jouer.",
        "No screen. No subscription. No worry.": "Sans écran. Sans abonnement. Sans souci.",
        "Curiosity has a new best friend": "La curiosité a trouvé son nouveau meilleur ami.",
        "Speaks their language — all 40+ of them": "Parle leur langue — et même plus de 40.",
        "Built for wonder, designed for trust": "Pensé pour l’émerveillement, conçu pour la confiance.",
        "The companion that grows with your child": "Le compagnon qui grandit avec votre enfant.",
        "Screen-free, imagination-full": "Sans écran, plein d’imagination.",
        "Privacy-first, play-always": "Vie privée d’abord, jeu toujours.",
        "One price. Endless adventures.": "Un prix. Des aventures sans fin.",
        "Where every question leads to a story": "Là où chaque question ouvre une histoire.",
        "Soft on the outside, brilliant on the inside": "Doux à l’extérieur, brillant à l’intérieur.",
        "Certified safe. Genuinely fun.": "Certifié sûr. Réellement plaisant.",
    }
    return translations.get(value, value)


def _translate_writing_rule_name(value: str) -> str:
    translations = {
        "Child as hero": "L’enfant reste le héros",
        "One idea per sentence": "Une idée par phrase",
        "Show, don't spec": "Montrer avant de spécifier",
        "EUR 99 always with context": "EUR 99 toujours avec contexte",
        "Active voice by default": "Voix active par défaut",
        "Address parents as allies": "Parler aux parents comme à des alliés",
        "Safety earns trust, not fear": "La sécurité doit nourrir la confiance, pas la peur",
        "Sensory language for the product": "Langage sensoriel pour le produit",
        "No exclamation point stacking": "Pas d’empilement de points d’exclamation",
        "Phantom Purple is the signature": "Phantom Purple reste la signature",
    }
    return translations.get(value, value)


def _translate_writing_rule_desc(value: str) -> str:
    replacements = {
        "Always position the child as the protagonist.": "Toujours positionner l’enfant comme protagoniste.",
        "Keep sentences short and rhythmic.": "Garder des phrases courtes et rythmées.",
        "Never lead with technical specifications.": "Ne jamais ouvrir avec la fiche technique.",
        "When mentioning the price, always pair it with the no-subscription promise.": "Quand le prix apparaît, l’associer systématiquement à la promesse sans abonnement.",
        "Use active, present-tense constructions.": "Préférer des phrases actives et au présent.",
        "Never lecture parents.": "Ne jamais faire la leçon aux parents.",
        "Present certifications": "Présenter les certifications",
        "Use tactile and sensory words": "Employer un vocabulaire tactile et sensoriel",
        "Maximum one exclamation mark per paragraph.": "Maximum un point d’exclamation par paragraphe.",
        "When referencing colour in copy, lead with Phantom Purple": "Quand la couleur entre dans la copy, commencer par Phantom Purple",
    }
    for src, dst in replacements.items():
        value = value.replace(src, dst)
    return value


def _translate_bilingual_rule_name(value: str) -> str:
    translations = {
        "French-first for France launch": "Français d’abord pour le lancement France",
        "Tutoiement for child-facing, vouvoiement for parent-facing": "Tutoiement côté enfant, vouvoiement côté parent",
        "No anglicisms where French alternatives exist": "Pas d’anglicismes quand un français naturel existe",
        "Brand name stays untranslated": "Le nom de marque reste intact",
        "Preserve rhythm and warmth in French": "Préserver le rythme et la chaleur en français",
        "Legal and certification terms in local format": "Employer les termes légaux et certifications au format local",
        "Bilingual packaging": "Packaging bilingue",
    }
    return translations.get(value, value)


def _translate_bilingual_rule_desc(value: str) -> str:
    replacements = {
        "All consumer-facing copy for the French market must be written natively in French, not translated from English.": "Toute copy visible par le marché France doit sembler écrite nativement en français, pas traduite après coup.",
        "Use 'tu' when Zack speaks to children.": "Utiliser « tu » quand Zack s’adresse à l’enfant.",
        "Avoid 'le learning'": "Éviter les tournures artificielles ou franglais du type « learning » ou « screen-free » quand une alternative française fonctionne.",
        "'ZackAI' and 'Zack' remain unchanged": "« ZackAI » et « Zack » ne se traduisent jamais.",
        "French copy should have the same emotional warmth as the English source.": "La version française doit garder la même chaleur émotionnelle que la source anglaise tout en sonnant naturellement française.",
        "Use 'Conforme RGPD'": "Employer « Conforme RGPD », « Marquage CE » et « Norme EN71 » quand le contexte s’y prête.",
        "Product packaging and inserts must be bilingual FR/EN.": "Le packaging et les inserts doivent rester bilingues FR/EN, avec priorité visuelle au français.",
    }
    for src, dst in replacements.items():
        value = value.replace(src, dst)
    return value


def _translate_sample_text(value: str) -> str:
    replacements = {
        "A fluffy friend who speaks their language.": "Un ami tout doux qui parle leur langue.",
        "ZackAI is the screen-free learning companion for curious kids aged 3–12. 40+ languages. No subscription. Just squeeze and explore.": "ZackAI est le compagnon d’apprentissage sans écran pour les enfants curieux de 3 à 12 ans. 40+ langues. Aucun abonnement. Il suffit de le serrer contre soi et d’explorer.",
        "Meet Zack — EUR 99, everything included": "Rencontrez Zack — EUR 99, tout est inclus",
        "Psst — Zack has a new story about a fox who counts in Japanese. Your little one might love it.": "Psst — Zack a une nouvelle histoire sur un renard qui compte en japonais. Votre enfant va peut-être l’adorer.",
        "Salut! I'm Zack — your new adventure buddy. I love stories, silly questions, and learning new words. Squeeze my paw and say hello. I already speak your language (and about 40 others). Let's explore together!": "Salut ! Moi, c’est Zack — ton nouveau compagnon d’aventure. J’adore les histoires, les questions farfelues et les nouveaux mots. Serre ma patte et dis bonjour. Je parle déjà ta langue (et environ 40 autres). On explore ensemble ?",
    }
    return replacements.get(value, value)


def _translate_feature_name(value: str) -> str:
    return {
        "Screen-free conversation": "Conversation sans écran",
        "Animated LED personality": "Personnalité LED animée",
        "40+ language support": "Support de 40+ langues",
        "Parent-trustworthy construction": "Construction pensée pour la confiance parentale",
    }.get(value, value)


def _translate_feature_benefit(value: str) -> str:
    return {
        "Children learn through dialogue rather than passive screen time.": "Les enfants apprennent par le dialogue plutôt que par une consommation passive d’écran.",
        "Expressive eyes reinforce emotional cues and delight.": "Les yeux expressifs renforcent les signaux émotionnels et la joie d’interaction.",
        "Useful for bilingual homes and playful language discovery.": "Idéal pour les foyers bilingues et la découverte ludique des langues.",
        "Warm materials, rounded hardware, and no subscription dependency.": "Des matières chaleureuses, un hardware rassurant et aucune dépendance à l’abonnement.",
    }.get(value, value)


def _translate_physical_form(value: str) -> str:
    replacements = {
        "Round, ball-shaped fluffy plush creature": "créature pelucheuse ronde, presque sphérique",
        "Muted Lilac": "Muted Lilac",
        " in ": " dans ",
        "with pointed cat-like ears": "avec oreilles félines pointues",
        "cream/beige face with rosy cheeks": "visage crème/beige avec joues rosées",
        "large animated blue LED eyes synced with voice/emotion/mood": "grands yeux LED bleus animés, synchronisés à la voix, à l’émotion et à l’humeur",
        "small red smile": "petit sourire rouge",
        "grey inner ears": "intérieur d’oreilles gris",
        "hypoallergenic fur": "fourrure hypoallergénique",
        "USB-C charging": "recharge USB-C",
    }
    for src, dst in replacements.items():
        value = value.replace(src, dst)
    return value


def _translate_email_name(value: str) -> str:
    translations = {
        "Welcome to ZackAI": "Bienvenue chez ZackAI",
        "Why ZackAI exists": "Pourquoi ZackAI existe",
        "Meet the companion": "Faire connaissance avec le compagnon",
        "The problem with screen-time solutions": "Le problème des solutions centrées sur l’écran",
        "How ZackAI is different": "Ce qui rend ZackAI différent",
        "What you’ll get on launch day": "Ce que vous recevrez le jour du lancement",
        "Tomorrow we go live": "Demain, nous passons en live",
        "Launch Morning": "Matin du lancement",
        "Launch Day Reminder": "Rappel du jour J",
        "Momentum Update": "Point d’élan",
        "Final Week Push": "Dernière ligne droite",
    }
    return translations.get(value, value)


def _translate_timing(value: str) -> str:
    translations = {
        "Immediate": "Immédiat",
        "Day 2": "Jour 2",
        "Day 4": "Jour 4",
        "T-10 days": "J-10",
        "T-7 days": "J-7",
        "T-3 days": "J-3",
        "T-1 day": "J-1",
        "Launch Day 09:00": "Jour du lancement 09:00",
        "Launch Day 18:00": "Jour du lancement 18:00",
        "Day 3": "Jour 3",
        "Final 72 hours": "Dernières 72 heures",
    }
    return translations.get(value, value)


def _translate_email_subject(value: str) -> str:
    translations = {
        "You’re in — welcome to the warm side of AI play": "Vous y êtes — bienvenue du côté chaleureux du jeu IA",
        "Why screen-free play needed a smarter companion": "Pourquoi le jeu sans écran avait besoin d’un compagnon plus intelligent",
        "Meet the plush with a glowing personality": "Découvrez la peluche à la personnalité lumineuse",
        "Why parents are searching for a better kind of play": "Pourquoi les parents cherchent une autre forme de jeu",
        "Soft intelligence, not cold tech": "Une intelligence douce, pas une techno froide",
        "Your Kickstarter reward preview": "Aperçu de votre reward Kickstarter",
        "Tomorrow: ZackAI launches on Kickstarter": "Demain : ZackAI arrive sur Kickstarter",
        "ZackAI is live on Kickstarter": "ZackAI est en ligne sur Kickstarter",
        "Your early chance to bring ZackAI home": "Votre chance de faire entrer ZackAI à la maison dès aujourd’hui",
        "Families are joining the ZackAI movement": "Les familles rejoignent le mouvement ZackAI",
        "Last chance to join the first ZackAI backers": "Dernière chance de rejoindre les premiers backers ZackAI",
    }
    return translations.get(value, value)


def _translate_email_goal(value: str) -> str:
    translations = {
        "Confirm signup and establish brand promise": "Confirmer l’inscription et poser immédiatement la promesse de marque.",
        "Tell the founding story": "Raconter l’origine de ZackAI et la tension qu’il résout.",
        "Build emotional attachment": "Créer un attachement émotionnel au compagnon.",
        "Prime the problem/solution frame": "Installer le cadre problème / solution avant le lancement.",
        "Teach differentiation and trust": "Faire comprendre la différenciation et construire la confiance.",
        "Preview rewards and create urgency": "Présenter les rewards et introduire une urgence lisible.",
        "Drive launch-day attention": "Concentrer l’attention sur le jour du lancement.",
        "Drive initial pledge surge": "Créer la première vague de pledges.",
        "Capture undecided subscribers": "Récupérer les inscrits encore hésitants.",
        "Use social proof and progress": "Utiliser la preuve sociale et la progression de campagne.",
        "Close remaining backers with urgency": "Convertir les derniers backers avec une urgence claire mais maîtrisée.",
    }
    return translations.get(value, value)


def _translate_email_summary(value: str) -> str:
    translations = {
        "Introduce ZackAI, core promise, and what subscribers can expect next.": "Introduire ZackAI, rappeler la promesse cœur et expliquer ce que l’inscrit recevra ensuite.",
        "Explain the problem ZackAI solves and position it against screen-heavy alternatives.": "Expliquer le problème que ZackAI résout et le positionner face aux alternatives trop centrées sur l’écran.",
        "Show hero product details, language support, and bedtime ritual use cases.": "Montrer le hero product, les langues supportées et les usages de rituel du soir.",
    }
    return translations.get(value, value)


def _translate_post_concept(value: str) -> str:
    translations = {
        "bedtime ritual reel": "reel autour du rituel du coucher",
        "multilingual phrase-of-the-day series": "série “phrase du jour” en mode multilingue",
        "screen-free parenting comparison post": "post de comparaison autour de la parentalité sans écran",
        "reward tier explainer carousel": "carrousel explicatif des reward tiers",
        "community quote card": "quote card communautaire",
    }
    return translations.get(value, value)


def _translate_channel_adaptation(value: str) -> str:
    replacements = {
        "emotion-first reels and warm carousel posts": "reels émotionnels d’abord et carrousels chaleureux",
        "sharp hooks, launch updates, reward urgency": "hooks courts, updates de lancement et urgence sur les rewards",
        "founder story, design credibility, category framing": "récit fondateur, crédibilité design et cadrage de catégorie",
        "daily during launch week, then 4-5 posts per week during the live campaign": "quotidien pendant la semaine de lancement, puis 4 à 5 posts par semaine pendant la campagne live",
    }
    return replacements.get(value, value)


def _translate_social_cta(value: str) -> str:
    return {
        "Join the Kickstarter": "Rejoindre Kickstarter",
        "Share with another intentional parent": "Partager avec un autre parent intentionnel",
        "Comment with your child’s favorite bedtime ritual": "Commenter avec le rituel du soir préféré de votre enfant",
    }.get(value, value)


def _translate_community_prompt(value: str) -> str:
    return {
        "What should ZackAI say at bedtime?": "Que devrait dire ZackAI au moment du coucher ?",
        "Which colorway feels most like your home?": "Quel coloris ressemble le plus à votre maison ?",
        "What makes technology feel trustworthy for kids?": "Qu’est-ce qui rend une technologie vraiment digne de confiance pour les enfants ?",
    }.get(value, value)


def _translate_creator_segment(value: str) -> str:
    return {
        "parenting creators": "créateurs parentalité",
        "Montessori educators": "éducateurs Montessori",
        "family design accounts": "comptes design & famille",
        "bilingual parenting communities": "communautés de parentalité bilingue",
    }.get(value, value)


def _translate_outreach_angle(value: str) -> str:
    return {
        "screen-free learning": "apprentissage sans écran",
        "emotional intelligence for kids": "intelligence émotionnelle pour les enfants",
        "premium plush design": "design peluche premium",
        "multilingual play rituals": "rituels de jeu multilingues",
    }.get(value, value)


def _translate_sample_outreach(value: str) -> str:
    replacements = {
        "Hi [Name], we’re launching ZackAI, a warm screen-free AI plush companion for curious kids, and your community felt like a beautiful fit for an early look.": "Bonjour [Name], nous lançons ZackAI, un compagnon IA en peluche, chaleureux et sans écran, pensé pour les enfants curieux — et votre communauté nous semble idéale pour une découverte en avant-première.",
        "We’re inviting a small group of trusted family creators to preview ZackAI ahead of Kickstarter and share what a screen-free, emotionally intelligent companion could mean for modern families.": "Nous invitons un petit groupe de créateurs famille de confiance à découvrir ZackAI avant Kickstarter et à partager ce qu’un compagnon sans écran, émotionnellement intelligent, peut apporter aux familles d’aujourd’hui.",
    }
    return replacements.get(value, value)


def _translate_collab_concept(value: str) -> str:
    return {
        "unboxing and bedtime ritual reel": "reel unboxing + rituel du coucher",
        "multilingual demo story": "story démo multilingue",
        "screen-free parenting conversation post": "post de conversation autour de la parentalité sans écran",
    }.get(value, value)


def _translate_gifting_strategy(value: str) -> str:
    return value.replace("Send hero color sample", "Envoyer un sample du coloris hero").replace("launch briefing", "briefing de lancement").replace("preferred story angles", "angles narratifs recommandés")


def _translate_measurement_idea(value: str) -> str:
    return {
        "creator code clicks": "clics sur codes créateurs",
        "Kickstarter referral traffic": "trafic de referral Kickstarter",
        "waitlist signups": "inscriptions waitlist",
        "engaged saves and shares": "saves et partages engagés",
    }.get(value, value)


def _translate_video_hook(value: str) -> str:
    return "Et si la chose la plus intelligente dans la chambre de votre enfant ressemblait à une étreinte plutôt qu’à un écran ?"


def _translate_story_arc(value: str) -> str:
    return {
        "problem": "le problème",
        "product reveal": "la révélation produit",
        "how it works": "comment cela fonctionne",
        "trust and proof": "la confiance et la preuve",
        "rewards and CTA": "les rewards et l’appel à l’action",
    }.get(value, value)


def _translate_scene_beat(value: str) -> str:
    replacements = {
        "Hands reach for a device, then pause.": "Des mains se dirigent vers un appareil, puis s’arrêtent.",
        "A soft plush with glowing eyes appears in warm afternoon light.": "Une peluche douce aux yeux lumineux apparaît dans une lumière chaude d’après-midi.",
        "Child and companion begin a multilingual story interaction.": "L’enfant et son compagnon entrent dans une histoire multilingue.",
        "Bedtime mode transitions the room into calm.": "Le mode coucher transforme la pièce en espace calme.",
        "Parents see ZackAI as a trusted ritual, not a gadget.": "Les parents comprennent que ZackAI est un rituel de confiance, pas un gadget.",
        "Final Kickstarter reward and call-to-action frame.": "Dernier plan sur les rewards Kickstarter et l’appel à agir.",
    }
    return replacements.get(value, value)


def _translate_voiceover_line(value: str) -> str:
    translations = {
        "Meet ZackAI, the screen-free playtime companion.": "Voici ZackAI, le compagnon de jeu sans écran.",
        "A screen-free plush friend that turns conversation into curiosity, comfort, and confidence.": "Un ami en peluche, sans écran, qui transforme la conversation en curiosité, en réconfort et en confiance.",
        "Built for intentional parents, and designed for children who deserve warmth in the age of AI.": "Conçu pour les parents intentionnels, pensé pour les enfants qui méritent de la chaleur à l’âge de l’IA.",
        "Back ZackAI on Kickstarter and help bring soft intelligence home.": "Soutenez ZackAI sur Kickstarter et faites entrer une intelligence douce à la maison.",
    }
    return translations.get(value, value)


def _translate_onscreen_text(value: str) -> str:
    return {
        "Screen-Free Playtime Companion": "Compagnon de jeu sans écran",
        "40+ Languages": "40+ langues",
        "Animated LED Personality": "Personnalité LED animée",
        "No Subscription Ever": "Sans abonnement, jamais",
        "Back on Kickstarter": "Soutenez sur Kickstarter",
    }.get(value, value)


def _translate_proof_moment(value: str) -> str:
    return {
        "screen-free positioning": "positionnement sans écran",
        "premium materials": "matériaux premium",
        "multilingual support": "support multilingue",
        "parent trust": "confiance parentale",
    }.get(value, value)


def _translate_audience_segment(value: str) -> str:
    return {
        "intentional parents": "parents intentionnels",
        "bilingual households": "foyers bilingues",
        "Montessori-minded families": "familles sensibles à Montessori",
        "premium toy buyers": "acheteurs de jouets premium",
    }.get(value, value)


def _translate_ad_hook(value: str) -> str:
    return {
        "A screen-free AI friend for curious kids": "Un ami IA sans écran pour les enfants curieux",
        "The plush companion that speaks 40+ languages": "Le compagnon en peluche qui parle 40+ langues",
        "Bedtime stories with emotional intelligence built in": "Des histoires du soir avec intelligence émotionnelle intégrée",
    }.get(value, value)


def _translate_ad_headline(value: str) -> str:
    return {
        "Screen-Free Playtime Companion": "Compagnon de jeu sans écran",
        "Warm intelligence for growing minds": "Une intelligence chaleureuse pour les esprits qui grandissent",
        "A smarter playtime companion—without screens": "Un compagnon de jeu plus intelligent — sans écran",
    }.get(value, value)


def _translate_ad_body(value: str) -> str:
    replacements = {
        "ZackAI brings conversational learning into a soft, glowing plush companion parents can trust.": "ZackAI fait entrer l’apprentissage conversationnel dans une peluche douce et lumineuse à laquelle les parents peuvent réellement faire confiance.",
        "Designed for playful minds, bedtime rituals, and multilingual homes—without subscriptions or screen dependency.": "Pensé pour les esprits joueurs, les rituels du soir et les foyers multilingues — sans abonnement ni dépendance à l’écran.",
    }
    return replacements.get(value, value)


def _translate_ad_cta(value: str) -> str:
    return {
        "Join the waitlist": "Rejoindre la waitlist",
        "Get early access": "Obtenir l’accès anticipé",
        "Be first on Kickstarter": "Être parmi les premiers sur Kickstarter",
    }.get(value, value)


def _translate_creative_direction(value: str) -> str:
    return {
        "warm natural light": "lumière naturelle chaude",
        "hands-only child interaction": "interaction enfant par les mains uniquement",
        "hero plush in Muted Lilac": "peluche hero en Muted Lilac",
        "soft premium textures": "textures douces et premium",
    }.get(value, value)


def _translate_campaign_stage(value: str) -> str:
    return {
        "launch surge": "poussée de lancement",
        "mid-campaign trust": "confiance en milieu de campagne",
        "final urgency": "urgence de fin de campagne",
    }.get(value, value)


def _translate_live_hook(value: str) -> str:
    return {
        "Back the plush AI families are rallying behind": "Soutenez la peluche IA que les familles commencent déjà à porter",
        "Still time to join the screen-free movement": "Il est encore temps de rejoindre le mouvement sans écran",
        "The warm, multilingual companion now live on Kickstarter": "Le compagnon chaleureux et multilingue est maintenant en live sur Kickstarter",
    }.get(value, value)


def _translate_live_copy(value: str) -> str:
    replacements = {
        "Families are backing ZackAI because it feels like the future of play—soft, safe, and screen-free.": "Les familles soutiennent ZackAI parce qu’il ressemble à l’avenir du jeu : doux, sûr et sans écran.",
        "Backers are joining for the warmth, staying for the multilingual intelligence, and sharing it for the peace of mind.": "Les backers viennent pour la chaleur du produit, restent pour son intelligence multilingue, et le partagent pour la tranquillité qu’il apporte.",
    }
    return replacements.get(value, value)


def _translate_urgency_message(value: str) -> str:
    return {
        "Early tiers are moving": "Les premiers paliers partent vite",
        "Launch pricing won’t last": "Le prix de lancement ne durera pas",
        "Join the first wave before campaign close": "Rejoignez la première vague avant la clôture de campagne",
    }.get(value, value)


def _translate_retargeting_angle(value: str) -> str:
    return {
        "waitlist visitors": "visiteurs waitlist",
        "video viewers": "visionneurs vidéo",
        "email clickers": "cliqueurs email",
        "reward-page dwellers": "visiteurs qui restent sur la page rewards",
    }.get(value, value)


def _translate_live_creative(value: str) -> str:
    return {
        "use real campaign progress": "utiliser la progression réelle de campagne",
        "highlight reward tiers": "mettre en avant les reward tiers",
        "show glowing eyes and hands-only interaction": "montrer les yeux lumineux et l’interaction par les mains uniquement",
    }.get(value, value)


def _translate_value(value: str) -> str:
    replacements = {
        "Intentional parenting over convenience parenting": "la parentalité intentionnelle plutôt que la parentalité de simple commodité",
        "Multilingualism as a gift, not a chore": "le multilinguisme comme un cadeau, pas comme une corvée",
        "Emotional intelligence matters more than academic acceleration": "l’intelligence émotionnelle avant l’accélération académique",
        "Play should be open-ended and imagination-driven": "un jeu ouvert, porté par l’imagination",
        "Safety and privacy are non-negotiable, especially with AI": "sécurité et vie privée non négociables, surtout avec l’IA",
        "Quality over quantity — fewer toys, better toys": "moins de jouets, mais de meilleurs jouets",
        "Screen-free does not mean anti-technology; it means pro-boundaries": "sans écran ne veut pas dire anti-technologie, mais pro-limites saines",
        "Children deserve to be listened to, not just entertained": "les enfants méritent d’être écoutés, pas seulement occupés",
        "Sustainability and ethical manufacturing matter": "la durabilité et l’éthique de fabrication comptent réellement",
    }
    return replacements.get(value, value)


def _translate_persona_sentence(value: str) -> str:
    if not value:
        return value
    full = {
        "Married or partnered with 1-3 children. Eldest child typically 3-7 years old (the sweet spot). May have a younger sibling on the way or recently arrived.": "En couple ou marié, avec 1 à 3 enfants. L’aîné se situe souvent dans la tranche 3-7 ans, avec parfois un plus jeune frère ou une plus jeune sœur en route ou récemment arrivé.",
        "Urban and peri-urban France — Paris/Ile-de-France, Lyon, Bordeaux, Nantes, Toulouse. Increasingly also expat families in Brussels, Geneva, Montreal.": "France urbaine et périurbaine — Paris / Île-de-France, Lyon, Bordeaux, Nantes, Toulouse — avec aussi une présence croissante chez les familles expatriées à Bruxelles, Genève ou Montréal.",
        "Comfortable with app-based parental controls.": "À l’aise avec les contrôles parentaux via application.",
        "Very comfortable with app-based parental controls.": "Très à l’aise avec les contrôles parentaux via application.",
        " Comfortable with app-based parental controls.": " Très à l’aise avec les contrôles parentaux via application.",
        "That their child is falling behind peers who have unlimited screen access": "Que leur enfant prenne du retard face à des pairs exposés sans limite aux écrans.",
        "That AI is recording, profiling, or manipulating their child": "Que l’IA enregistre, profile ou manipule leur enfant.",
        "That they are the last generation of parents who care about screen limits": "D’être parmi les derniers parents à encore défendre de vraies limites d’écran.",
        "That cheap plastic toys are training their child to be a passive consumer": "Que les jouets plastiques bon marché transforment leur enfant en consommateur passif.",
        "That their multilingual goals will fail because immersion is not enough": "Que leurs ambitions multilingues échouent faute d’immersion suffisante.",
        "That buying yet another 'educational' toy will end in a cupboard within two weeks": "Qu’un nouveau jouet dit “éducatif” finisse au placard au bout de deux semaines.",
        "Raise a curious, empathetic, multilingual child without relying on screens": "Élever un enfant curieux, empathique et multilingue sans s’appuyer sur les écrans.",
        "Find a single trusted companion object that grows with the child across years": "Trouver un compagnon de confiance unique, capable d’accompagner l’enfant pendant plusieurs années.",
        "Be seen by other parents as thoughtful and research-driven, not overprotective": "Être perçu par les autres parents comme réfléchi et documenté, pas comme excessivement protecteur.",
        "Create a home environment that feels warm, creative, and low-tech": "Créer un environnement domestique chaleureux, créatif et peu dépendant à la tech.",
        "Give their child a genuine competitive advantage through language and emotional skills": "Donner à leur enfant un véritable avantage par les langues et les compétences émotionnelles.",
        "Have peaceful bedtimes and car rides without resorting to a tablet": "Retrouver des couchers et des trajets apaisés sans avoir recours à une tablette.",
        "The 'can I watch something?' negotiation that happens 5-10 times per day": "La négociation “est-ce que je peux regarder quelque chose ?” qui revient 5 à 10 fois par jour.",
        "Learns it is GDPR-compliant and EN71/CE certified — safety-first messaging lands hard": "Découvre la conformité RGPD et les certifications EN71/CE — et la promesse sécurité touche immédiatement juste.",
        "The Intentional Parent is a well-educated, upper-middle-income parent in urban France.": "Le parent intentionnel ZackAI est un parent bien éduqué, au revenu confortable, vivant le plus souvent en France urbaine et prenant très au sérieux la qualité des objets qu’il introduit dans le quotidien familial.",
        "ZackAI at EUR 99 all-in is the best value proposition in the category.": "À EUR 99 tout compris, ZackAI présente la proposition de valeur la plus lisible de la catégorie.",
        "No AI companion in EU market offers 40+ conversational languages": "Aucun compagnon IA du marché européen n’offre aujourd’hui 40+ langues réellement conversationnelles.",
        "Lead with '40+ languages, zero screens, no subscription' as the three-pillar differentiation": "Ouvrir avec “40+ langues, zéro écran, sans abonnement” comme triptyque de différenciation.",
    }
    if value in full:
        return full[value]
    replacements = {
        "High digital literacy but deliberately tech-skeptical for children.": "Très à l’aise avec la tech pour lui-même, mais volontairement sceptique quand il s’agit des enfants.",
        "Uses smartphones and smart home devices personally but enforces strict screen rules for kids.": "Utilise smartphone et objets connectés pour lui-même, tout en maintenant des règles écrans très claires pour les enfants.",
        "Feels like the future of play": "ressemble à l’avenir du jeu",
        "grows with the child across years": "grandit avec l’enfant au fil des années",
    }
    for src, dst in replacements.items():
        value = value.replace(src, dst)
    return value


def _translate_competitive_differentiator(value: str) -> str:
    return {
        "40+ Languages with Conversational AI": "40+ langues avec IA conversationnelle",
        "Animated LED Eyes with Emotional Expression": "Yeux LED animés avec expression émotionnelle",
        "Persistent Memory — Knows Your Child": "Mémoire persistante — connaît votre enfant",
        "No Mandatory Subscription at EUR 99": "Pas d’abonnement obligatoire à EUR 99",
        "GDPR-Compliant, EN71/CE Certified Safety-First": "Conforme RGPD, EN71/CE et sécurité d’abord",
        "Cuddly Physical Form Factor": "Forme physique câline et vraiment compagnon",
    }.get(value, value)


def _translate_competitive_why(value: str) -> str:
    mapping = {
        "No competitor offers real-time conversational language learning in 40+ languages. Tonies/Yoto are pre-recorded. Bondu has limited languages. Alexa is not designed for language immersion.": "Aucun concurrent ne propose un apprentissage conversationnel en temps réel dans plus de 40 langues. Tonies et Yoto restent préenregistrés, Bondu limite l’étendue linguistique, et Alexa n’est pas pensée pour l’immersion.",
        "ZackAI's LED eyes sync with voice, emotion, and mood — creating a living companion experience. No competitor has physical emotional expression. Bondu is static plush. Tonies/Yoto are boxes.": "Les yeux LED ZackAI se synchronisent à la voix, à l’émotion et à l’humeur, ce qui crée une vraie sensation de compagnon vivant. Aucun concurrent n’offre cette expression émotionnelle physique : Bondu reste statique, Tonies et Yoto sont des boîtiers.",
        "ZackAI remembers favorite topics, stories, and conversations. Engagement deepens over months like a friendship. Alexa forgets between sessions. Tonies/Yoto have no memory. Bondu has limited recall.": "ZackAI retient les sujets, histoires et conversations préférés de l’enfant. L’engagement se creuse au fil des mois comme une relation. Alexa oublie d’une session à l’autre, Tonies et Yoto n’ont pas de mémoire, et Bondu reste limité.",
        "EUR 99 is the full price. Tonies requires EUR 14.99/figurine ongoing. Yoto requires EUR 6.99+/card. Bondu has premium subscription. Lovevery is EUR 36/month. ZackAI eliminates subscription fatigue.": "EUR 99 constitue le prix complet. Tonies implique des achats continus de figurines, Yoto des cartes, Bondu une logique d’abonnement premium et Lovevery un coût mensuel élevé. ZackAI supprime cette fatigue d’abonnement.",
        "Full GDPR compliance, EN71 + ASTM F963 + CE certified. Parents have complete control via companion app. Alexa is a privacy concern. Bondu's privacy stance is less transparent.": "Conformité RGPD complète, certifications EN71, ASTM F963 et CE. Les parents gardent le contrôle via l’app compagnon. Alexa soulève de vraies inquiétudes de vie privée, et Bondu reste moins transparent sur ce terrain.",
        "Round, ball-shaped fluffy plush with cat-like ears. Hypoallergenic fur. Can be hugged, carried to bed, taken in the car. Alexa is hard plastic. Tonies/Yoto are boxes. Only Bondu competes on cuddlability.": "ZackAI reste une peluche ronde, douce, câline et emportable dans le lit, la voiture ou le quotidien. Alexa reste un objet dur en plastique, Tonies et Yoto des boîtes. Seul Bondu rivalise partiellement sur la dimension câline.",
    }
    return mapping.get(value, _translate_persona_sentence(value))


def _translate_competitor_summary(item: Dict[str, Any]) -> str:
    name = item.get('name', 'Concurrent')
    category = item.get('category', '')
    threat = item.get('threat_level', '')
    if name.startswith('Bondu'):
        return "concurrent direct dans la peluche IA, mais plus froid visuellement, plus faible sur l’intelligence émotionnelle et moins clair sur la logique sans abonnement."
    if name.startswith('Tonies'):
        return "référence du sans-écran audio, mais non conversationnelle et vite limitée dans l’adaptation à l’enfant."
    if name.startswith('Yoto'):
        return "acteur premium du player audio, fort en design mais sans vraie conversation ni mémoire émotionnelle."
    if name.startswith('Amazon'):
        return "option prix bas et écosystème massif, mais anti-positionnée sur la confiance parentale, la vie privée et la physicalité du compagnon."
    if name.startswith('Lovevery'):
        return "très fort sur l’aspiration Montessori et la qualité perçue, mais pas sur l’indépendance, la conversation ni la logique compagnon."
    return f"{category} — {threat}"


def _translate_difference(value: str) -> str:
    translations = {
        "True conversational AI that adapts in real time to each child's age, interests, and language level": "Une IA réellement conversationnelle qui s’adapte en temps réel à l’âge, aux centres d’intérêt et au niveau de langue de l’enfant.",
        "40+ languages with native-quality pronunciation — no competitor exceeds 5": "Plus de 40 langues avec une prononciation de qualité native — très au-delà du marché actuel.",
        "Zero subscription: EUR 99 one-time purchase (50% launch discount from EUR 199) vs. Bondu's recurring fees and Tonies/Yoto's ongoing content purchases": "Zéro abonnement : EUR 99 à l’achat pendant le lancement, sans frais récurrents ni économie de lock-in.",
        "Animated LED eyes that convey emotion and engagement, creating a living character rather than a static speaker": "Des yeux LED animés qui rendent ZackAI expressif et vivant, plutôt qu’un simple haut-parleur posé dans une chambre.",
        "5 distinctive color variants led by Phantom Purple — a bold aesthetic choice that signals personality over commodity": "Cinq coloris distinctifs, menés par Phantom Purple, pour créer de l’attachement et une vraie personnalité de produit.",
        "GDPR-compliant by design with on-device privacy controls, unlike Alexa Kids": "Une architecture pensée pour la conformité RGPD et le contrôle parental, loin de la logique smart-speaker générique.",
    }
    return translations.get(value, value)


def _translate_material(value: str) -> str:
    translations = {
        "soft fluffy plush fabric": "tissu pelucheux doux et moelleux",
        "hypoallergenic fur": "fourrure hypoallergénique",
        "brushed cotton": "coton brossé",
        "sealed rounded LED components": "composants LED scellés et arrondis",
        "warm LED glow (animated eyes)": "lueur LED chaude pour les yeux animés",
        "USB-C charging dock": "recharge USB-C",
        "kraft paper packaging": "packaging papier kraft",
        "embossed cardboard": "carton embossé",
        "woven label tag": "étiquette tissée",
        "recycled polyester fill": "garnissage en polyester recyclé",
        "matte silicone accents": "accents en silicone mat",
        "soft felt lining": "doublure en feutre doux",
    }
    return translations.get(value, value)


def _translate_use_case(value: str) -> str:
    translations = {
        "bedtime storytelling": "rituels d’histoires au moment du coucher",
        "after-school decompression": "temps de décompression après l’école",
        "language practice": "pratique des langues au quotidien",
        "emotion check-ins": "moments de check-in émotionnel",
        "screen-free independent play": "jeu autonome sans écran",
    }
    return translations.get(value, value)


def _translate_objection(value: str) -> str:
    translations = {
        "Why not just use a tablet? ZackAI keeps the experience tactile and calm.": "Pourquoi ne pas simplement donner une tablette ? Parce que ZackAI conserve une expérience tactile, calme et incarnée.",
        "Is it safe? The concept emphasizes soft materials, rounded electronics, and EU-ready safety posture.": "Est-ce sûr ? Oui : la promesse s’appuie sur des matériaux doux, une électronique rassurante et une posture de conformité européenne.",
        "Will it become expensive over time? The value proposition is no subscription ever.": "Est-ce que cela coûtera plus cher dans le temps ? Non : la proposition repose justement sur l’absence totale d’abonnement.",
    }
    return translations.get(value, value)


def _translate_credibility(value: str) -> str:
    translations = {
        "GDPR, CE, and EN71 certified — the trifecta of EU child product compliance": "RGPD, CE et EN71 : le triptyque clé de conformité pour un produit enfant en Europe.",
        "40+ languages validated with native speakers": "40+ langues validées avec des locuteurs natifs.",
        "Designed and launched in France for the European market first": "Conçu et lancé d’abord pour le marché français et européen.",
        "No subscription model signals confidence in product value rather than lock-in economics": "L’absence d’abonnement signale une vraie confiance dans la valeur produit plutôt qu’une économie de verrouillage.",
        "EUR 199 full price with 50% launch discount demonstrates premium positioning with accessible entry": "Le prix public EUR 199 avec offre de lancement à -50 % soutient un positionnement premium mais accessible.",
    }
    return translations.get(value, value)


def _translate_core_message(value: str) -> str:
    return "ZackAI est le compagnon IA doux et sans écran qui parle la langue de l’enfant, retient son univers et grandit avec lui — sans abonnement, sans écran et sans compromis."


def _translate_proof_angle(value: str) -> str:
    translations = {
        "screen-free learning alternative": "alternative crédible à l’apprentissage sur écran",
        "premium materials and warm design": "matériaux premium et design chaleureux",
        "multilingual utility for modern families": "utilité multilingue pour les familles contemporaines",
        "emotionally intelligent play experience": "expérience de jeu émotionnellement intelligente",
    }
    return translations.get(value, value)


def _translate_positioning_statement(value: str) -> str:
    return "Pour les parents intentionnels en France qui veulent que leurs enfants de 3 à 12 ans apprennent, jouent et grandissent par la conversation plutôt que par les écrans, ZackAI est le compagnon IA en peluche qui associe la chaleur d’un doudou à l’intelligence d’un tuteur personnel. Là où Bondu enferme les familles dans l’abonnement, où Tonies et Yoto restent dans l’audio passif, et où les enceintes connectées n’ont jamais été pensées pour l’enfance, ZackAI apporte un apprentissage conversationnel, multilingue et adaptatif dans un format câlin, sans écran, conforme aux attentes européennes et proposé à EUR 99 sans abonnement."


def _translate_keyword(value: str) -> str:
    mapping = {
        "cozy": "cocon",
        "tactile": "tactile",
        "gentle": "doux",
        "curious": "curieux",
        "plush": "peluche",
        "warm": "chaleureux",
        "nurturing": "rassurant",
        "playful": "ludique",
    }
    return mapping.get(value, value)


def _translate_role(value: str) -> str:
    return {
        "primary": "primaire",
        "secondary": "secondaire",
        "accent": "accent",
        "support": "support",
        "signal": "signal",
    }.get(value, value)


def _translate_psychology(value: str) -> str:
    replacements = {
        "Gentle imagination and creative calm.": "Une imagination douce et un calme créatif.",
        "Clarity and openness.": "De la clarté et de l’ouverture.",
        "Energy, joy, and action.": "De l’énergie, de la joie et une invitation à l’action.",
        "Grounding warmth and tactile comfort.": "Une chaleur rassurante et un confort tactile.",
        "Growth, success, and positive reinforcement.": "La progression, la réussite et le renforcement positif.",
    }
    for src, dst in replacements.items():
        value = value.replace(src, dst)
    return value


def _translate_usage(value: str) -> str:
    return value.replace("Hero surfaces", "surfaces héro").replace("main backgrounds", "grands fonds").replace("packaging base", "base packaging").replace("Call-to-action buttons", "boutons d’action")


def _translate_sentence(value: str) -> str:
    if not value:
        return value
    replacements = {
        "Warm, soft-lit lifestyle photography in cozy home environments.": "Photographie lifestyle chaude et douce, située dans des environnements domestiques accueillants.",
        "Natural light preferred": "Lumière naturelle privilégiée",
        "Slightly warm white balance": "Balance des blancs légèrement chaude",
        "No screens visible in any imagery": "Aucun écran visible dans les images",
        "No cold, sterile, or laboratory-like environments": "Aucun environnement froid, stérile ou pseudo-laboratoire",
    }
    for src, dst in replacements.items():
        value = value.replace(src, dst)
    return value


def _translate_environment(value: str) -> str:
    translations = {
        "Cozy children's bedrooms with soft rugs and cushions": "chambres d’enfants chaleureuses avec tapis et coussins moelleux",
        "Sunny living rooms with natural wood and fabric textures": "salons lumineux avec bois naturel et textures textiles",
        "Garden and outdoor settings with soft grass and dappled light": "jardins et extérieurs doux avec herbe, ombre légère et lumière filtrée",
        "Reading nooks and pillow forts": "coins lecture et cabanes d’oreillers",
        "Kitchen tables during creative play": "tables de cuisine pendant les moments de jeu créatif",
    }
    return translations.get(value, value)


def _translate_constraint(value: str) -> str:
    translations = {
        "No children's faces shown — focus on hands, backs, silhouettes": "pas de visages d’enfants en frontal ; privilégier les mains, dos et silhouettes",
        "Hands-and-toy focus: always show physical interaction with the ZackAI plush": "toujours montrer l’interaction physique entre l’enfant et la peluche ZackAI",
        "No screens visible in any imagery — this is a screen-free product": "aucun écran visible : ZackAI est un produit sans écran et cela doit se sentir partout",
        "No cold, sterile, or laboratory-like environments": "pas d’environnements froids, stériles ou pseudo-techniques",
        "No isolated product shots on plain white — always contextualize in a warm setting": "éviter les packshots blancs isolés ; toujours réinscrire le produit dans un contexte chaleureux",
    }
    return translations.get(value, value)


def _translate_avoid(value: str) -> str:
    translations = {
        "Metallic or chrome surfaces": "surfaces métalliques ou chromées",
        "Sharp geometric angles and aggressive shapes": "angles géométriques durs et formes agressives",
        "Dark or moody color schemes": "palettes sombres ou dramatiques",
        "Neon or electric colors": "couleurs néon ou électriques",
        "Robot or humanoid AI imagery": "imaginaire robotique ou humanoïde",
        "Screens, tablets, phones, or any digital device displays": "écrans, tablettes, téléphones ou interfaces numériques visibles",
        "Photorealistic children's faces": "visages d’enfants photoréalistes en frontal",
        "Cold blue tech lighting": "éclairage techno bleu et froid",
        "Circuit board patterns or binary code visuals": "patterns de circuit imprimé ou imagerie binaire",
        "Corporate or enterprise aesthetics": "esthétique corporate ou enterprise",
    }
    return translations.get(value, value)


def _translate_campaign_section_title(value: str) -> str:
    translations = {
        "Why families need this now": "Pourquoi les familles en ont besoin maintenant",
        "What ZackAI does differently": "Ce que ZackAI fait différemment",
        "How it fits into family life": "Comment ZackAI s’insère dans la vie familiale",
        "Why parents can trust it": "Pourquoi les parents peuvent lui faire confiance",
    }
    return translations.get(value, value)


def _translate_campaign_section_copy(value: str) -> str:
    translations = {
        "Parents want less screen time and more meaningful play. ZackAI gives children a responsive companion that listens, teaches, and comforts.": "Les parents veulent moins d’écran et davantage de jeu porteur de sens. ZackAI offre aux enfants un compagnon réactif qui écoute, accompagne, enseigne et rassure.",
        "Unlike passive audio products or screen-first assistants, ZackAI is tactile, expressive, multilingual, and designed for children.": "Contrairement aux produits audio passifs ou aux assistants pensés d’abord pour l’écran, ZackAI est tactile, expressif, multilingue et conçu pour le monde émotionnel de l’enfant.",
        "Use ZackAI for bedtime rituals, playful learning, and cozy curiosity moments throughout the day.": "ZackAI s’intègre dans les rituels du coucher, les moments d’éveil et les instants de curiosité douce tout au long de la journée.",
        "The product story emphasizes safety, emotional intelligence, premium materials, and a one-time purchase.": "Le récit produit doit faire remonter quatre preuves : sécurité, intelligence émotionnelle, qualité des matières et achat unique sans abonnement.",
    }
    return translations.get(value, value)


def _translate_campaign_pillar(value: str) -> str:
    translations = {
        "screen-free learning": "apprentissage sans écran",
        "emotional intelligence": "intelligence émotionnelle",
        "multilingual play": "jeu multilingue",
        "parent trust": "confiance parentale",
        "animated LED personality": "personnalité LED animée",
    }
    return translations.get(value, value)


def _translate_campaign_objection(value: str) -> str:
    translations = {
        "No subscription": "Pas d’abonnement",
        "No screens": "Pas d’écran",
        "Warm design instead of cold tech": "Un design chaleureux plutôt qu’une techno froide",
    }
    return translations.get(value, value)


def _translate_campaign_cta(value: str) -> str:
    translations = {
        "Back ZackAI on Kickstarter": "Soutenir ZackAI sur Kickstarter",
        "Reserve your colorway": "Réserver votre coloris",
        "Join the first wave of screen-free families": "Rejoindre la première vague de familles sans écran",
    }
    return translations.get(value, value)


def _translate_reward_tier(value: str) -> str:
    translations = {
        "Early Bird": "Early Bird",
        "Standard Backer": "Backer standard",
        "Family Bundle": "Pack famille",
    }
    return translations.get(value, value)


def _translate_reward_offer(value: str) -> str:
    translations = {
        "Hero color at launch price": "Le coloris hero au prix de lancement.",
        "Choose from full color lineup": "Choix libre parmi toute la gamme de coloris.",
        "Two companions for sibling households or gifting": "Deux compagnons pour les fratries ou pour offrir.",
    }
    return translations.get(value, value)


def _translate_faq_question(value: str) -> str:
    translations = {
        "Is ZackAI screen-free?": "ZackAI est-il vraiment sans écran ?",
        "Does it require a subscription?": "Faut-il un abonnement ?",
        "Who is it for?": "À qui ZackAI s’adresse-t-il ?",
    }
    return translations.get(value, value)


def _translate_faq_answer(value: str) -> str:
    translations = {
        "Yes. The core interaction is voice, plush touch, and expressive LED feedback.": "Oui. L’interaction centrale repose sur la voix, le toucher de la peluche et le feedback LED expressif.",
        "No. The product position explicitly promises no subscription ever.": "Non. La proposition ZackAI repose explicitement sur l’absence totale d’abonnement.",
        "Intentional parents of children 3–12 who want calm, curious, screen-free play.": "Aux parents intentionnels d’enfants de 3 à 12 ans qui recherchent un jeu calme, curieux et sans écran.",
    }
    return translations.get(value, value)


def _translate_social_proof(value: str) -> str:
    translations = {
        "intentional parenting": "parentalité intentionnelle",
        "language learning": "apprentissage des langues",
        "bedtime ritual improvement": "amélioration des rituels du coucher",
        "parent trust": "confiance parentale",
    }
    return translations.get(value, value)


def _translate_artifact_summary(value: str) -> str:
    replacements = {
        "Presentation-ready NotebookLM export in PDF format.": "Export NotebookLM prêt à présenter, au format PDF.",
        "NotebookLM-generated audio briefing for listening review.": "Brief audio généré par NotebookLM pour une revue à l’écoute.",
        "NotebookLM flashcard deck with": "Deck de flashcards NotebookLM avec",
        "NotebookLM quiz set with": "Jeu de quiz NotebookLM avec",
        "NotebookLM mind-map export.": "Export mind map NotebookLM.",
        "CSV export with": "Export CSV avec",
        "rows": "lignes",
        "columns": "colonnes",
        " and ": " et ",
    }
    for src, dst in replacements.items():
        value = value.replace(src, dst)
    return value
