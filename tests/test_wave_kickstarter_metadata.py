from brandmint.core.wave_planner import compute_wave_plan


SAMPLE_CONFIG = {
    "brand": {
        "name": "Prototype Brand",
        "domain_tags": ["dtc", "crowdfunding"],
    }
}


def test_compute_wave_plan_populates_kickstarter_metadata() -> None:
    waves = compute_wave_plan(SAMPLE_CONFIG, depth="exhaustive")
    by_number = {wave.number: wave for wave in waves}

    assert by_number[1].kickstarter_sections == ["market-understanding"]
    assert by_number[1].kickstarter_artifacts == [
        "market-buyer-persona",
        "competitor-summary",
    ]

    assert by_number[2].kickstarter_sections == ["product-detailing"]
    assert by_number[2].kickstarter_artifacts == [
        "detailed-product-description",
        "product-positioning-summary",
        "mds",
        "voice-and-tone",
    ]

    assert by_number[4].kickstarter_sections == [
        "crafting-compelling-copy",
        "campaign-messaging",
    ]
    assert by_number[4].kickstarter_artifacts == [
        "landing-page-copy",
        "campaign-page-copy",
        "campaign-video-script",
        "pre-launch-ads-copy",
    ]

    assert by_number[5].kickstarter_sections == ["email-strategy"]
    assert by_number[6].kickstarter_sections == ["driving-continual-interest"]
    assert by_number[7].kickstarter_sections == []
    assert by_number[8].kickstarter_sections == []
    assert by_number[8].post_hook == "brand_docs"



def test_wave_to_dict_includes_kickstarter_metadata() -> None:
    wave = compute_wave_plan(SAMPLE_CONFIG, depth="surface")[0]

    payload = wave.to_dict()

    assert payload["kickstarter_sections"] == ["market-understanding"]
    assert payload["kickstarter_artifacts"] == [
        "market-buyer-persona",
        "competitor-summary",
    ]
    assert payload["post_hook"] is None
