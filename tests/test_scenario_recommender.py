from brandmint.core.scenario_recommender import ScenarioRecommender
from brandmint.models.product import (
    BudgetTier,
    LaunchChannel,
    LaunchContext,
    MaturityStage,
    ProductBrand,
    ProductData,
)


def _product(brand_name: str) -> ProductData:
    return ProductData(
        brand=ProductBrand(
            name=brand_name,
            category="B2B SaaS",
            primary_promise="Automate business workflows",
        )
    )


def _saas_context() -> LaunchContext:
    return LaunchContext(
        channel=LaunchChannel.SAAS,
        budget_tier=BudgetTier.STANDARD,
        maturity_stage=MaturityStage.LAUNCH_READY,
    )


def test_klear_karma_combined_scenario_is_registered() -> None:
    scenario = ScenarioRecommender().get_scenario("klear-karma-combined")

    assert scenario.id == "klear-karma-combined"
    assert scenario.best_for_channels == ["organic", "saas"]
    assert scenario.eligible_brand_names == ["Klear Karma"]
    assert "kickstarter_page_structure" not in scenario.execution_context.platform_constraints
    assert scenario.skill_ids == [
        "niche-validator",
        "buyer-persona",
        "competitor-analysis",
        "detailed-product-description",
        "product-positioning-summary",
        "mds-messaging-direction-summary",
        "voice-and-tone",
        "visual-identity-core",
        "campaign-page-copy",
        "campaign-video-script",
        "welcome-email-sequence",
        "pre-launch-email-sequence",
        "launch-email-sequence",
        "pre-launch-ads",
        "live-campaign-ads",
        "press-release-copy",
        "social-content-engine",
        "short-form-hook-generator",
        "influencer-outreach-pro",
        "review-response-strategist",
    ]


def test_generic_b2b_saas_does_not_recommend_klear_karma_scenario() -> None:
    matches = ScenarioRecommender().recommend(_product("Acme Cloud"), _saas_context())

    assert "klear-karma-combined" not in {match.scenario_id for match in matches}


def test_klear_karma_product_recommends_combined_scenario() -> None:
    matches = ScenarioRecommender().recommend(_product("Klear Karma"), _saas_context())

    assert "klear-karma-combined" in {match.scenario_id for match in matches}
