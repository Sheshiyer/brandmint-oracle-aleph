from brandmint.core.agent_scaffolder import AgentScaffolder
from brandmint.models.product import BudgetTier
from brandmint.models.scenario import ExecutionContext
from brandmint.models.skill import SkillSource, UnifiedSkill


def _context() -> ExecutionContext:
    return ExecutionContext(
        budget_tier=BudgetTier.STANDARD,
        tone="internal strategic",
        output_format="standard",
        depth_level="exhaustive",
        quality_bar="premium",
    )


def _skill() -> UnifiedSkill:
    return UnifiedSkill(
        id="positioning",
        name="Positioning",
        source=SkillSource.ORCHESTRATOR,
        description="Create product positioning.",
    )


def test_prompt_includes_brand_config_source_of_truth() -> None:
    prompt = AgentScaffolder().generate_context_prompt(
        skill=_skill(),
        context=_context(),
        brand_config={
            "brand": {"name": "Klear Karma"},
            "source_context": {"primary_reader": "internal founders and investor prep"},
            "_brandmint": {"approval": {"fingerprint_value": "secret-ish metadata"}},
        },
    )

    assert "BRAND CONFIG SOURCE OF TRUTH" in prompt
    assert "Klear Karma" in prompt
    assert "internal founders and investor prep" in prompt
    assert "_brandmint" not in prompt
    assert "secret-ish metadata" not in prompt


def test_prompt_omits_brand_section_when_config_missing() -> None:
    prompt = AgentScaffolder().generate_context_prompt(
        skill=_skill(),
        context=_context(),
    )

    assert "BRAND CONFIG SOURCE OF TRUTH" not in prompt


def test_prompt_recursively_redacts_brandmint_metadata() -> None:
    brand_config = {
        "brand": {
            "name": "Klear Karma",
            "details": {
                "safe": "keep nested value",
                "_brandmint": {"approval": "nested dictionary metadata"},
            },
        },
        "products": [
            {
                "name": "Mirror",
                "_brandmint": {"approval": "list item metadata"},
            },
            [
                {
                    "safe": "keep deeply nested value",
                    "_brandmint": {"approval": "deep list metadata"},
                }
            ],
        ],
    }

    prompt = AgentScaffolder().generate_context_prompt(
        skill=_skill(),
        context=_context(),
        brand_config=brand_config,
    )

    assert "_brandmint" not in prompt
    assert "dictionary metadata" not in prompt
    assert "list item metadata" not in prompt
    assert "deep list metadata" not in prompt
    assert "keep nested value" in prompt
    assert "keep deeply nested value" in prompt
    assert "_brandmint" in brand_config["products"][0]
