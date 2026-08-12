from brandmint.core.scenario_recommender import ScenarioRecommender


def test_klear_karma_combined_scenario_is_registered() -> None:
    scenario = ScenarioRecommender().get_scenario("klear-karma-combined")

    assert scenario.id == "klear-karma-combined"
    assert scenario.best_for_channels == ["organic", "saas"]
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
