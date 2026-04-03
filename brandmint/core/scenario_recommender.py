"""
Scenario Recommender - Generates context-aware execution scenarios
Phase 1 implementation
"""

from typing import List, Dict, Any
from ..models.product import ProductData, LaunchContext, BudgetTier, LaunchChannel, MaturityStage
from ..models.scenario import (
    Scenario,
    ScenarioType,
    ExecutionContext,
    ScenarioMatch,
)


class ScenarioRecommender:
    """
    Generates and recommends scenarios based on detected context
    """
    
    def __init__(self):
        self.scenarios = self._build_scenario_catalog()
    
    def recommend(
        self,
        product: ProductData,
        context: LaunchContext,
        limit: int = 4,
    ) -> List[ScenarioMatch]:
        """
        Recommend top scenarios for the given context
        
        Returns ranked list of scenario matches
        """
        matches = []
        
        for scenario in self.scenarios:
            score = scenario.matches_context(
                context.budget_tier,
                context.channel,
                context.maturity_stage,
            )
            
            reasoning, pros, cons = self._explain_match(scenario, context)
            
            matches.append(ScenarioMatch(
                scenario_id=scenario.id,
                match_score=score,
                reasoning=reasoning,
                pros=pros,
                cons=cons,
            ))
        
        # Sort by score descending
        matches.sort(key=lambda m: m.match_score, reverse=True)
        
        return matches[:limit]
    
    def get_scenario(self, scenario_id: ScenarioType) -> Scenario:
        """Get a scenario by ID"""
        for scenario in self.scenarios:
            if scenario.id == scenario_id:
                return scenario
        raise ValueError(f"Scenario not found: {scenario_id}")
    
    def _explain_match(
        self,
        scenario: Scenario,
        context: LaunchContext,
    ) -> tuple[str, List[str], List[str]]:
        """
        Generate reasoning for why a scenario matches
        
        Returns: (reasoning, pros, cons)
        """
        pros = []
        cons = []
        
        # Budget analysis
        budget_diff = abs(
            list(BudgetTier).index(context.budget_tier) -
            list(BudgetTier).index(scenario.best_for_budget)
        )
        
        if budget_diff == 0:
            pros.append(f"Perfect budget match (${scenario.estimated_cost_usd:,})")
        elif budget_diff == 1:
            if list(BudgetTier).index(context.budget_tier) < list(BudgetTier).index(scenario.best_for_budget):
                cons.append(f"Would exceed budget by ~${scenario.estimated_cost_usd // 2:,}")
            else:
                pros.append("Under budget - room for upgrades")
        else:
            cons.append(f"Budget mismatch (${scenario.estimated_cost_usd:,} needed)")
        
        # Channel analysis
        if context.channel in scenario.best_for_channels:
            pros.append(f"Optimized for {context.channel.value}")
        elif scenario.best_for_channels:
            cons.append(f"Better for {', '.join(c.value for c in scenario.best_for_channels)}")
        
        # Maturity analysis
        if context.maturity_stage in scenario.best_for_maturity:
            pros.append(f"Designed for {context.maturity_stage.value} stage")
        elif scenario.best_for_maturity:
            if context.maturity_stage == MaturityStage.PRE_LAUNCH:
                cons.append("Assumes existing brand assets")
        
        # Timeline analysis
        if context.timeline_urgency.value == "rushed" and scenario.estimated_timeline_days.startswith("2-3"):
            pros.append("Fast execution (2-3 days)")
        elif context.timeline_urgency.value == "thorough" and scenario.estimated_timeline_days.startswith("4-5"):
            pros.append("Comprehensive timeline (4-5 days)")
        
        # Build reasoning
        reasoning = f"Optimized for {context.budget_tier.value} budget"
        if context.channel in scenario.best_for_channels:
            reasoning += f" and {context.channel.value} launch"
        
        return reasoning, pros, cons
    
    def _build_scenario_catalog(self) -> List[Scenario]:
        """
        Build the catalog of available scenarios
        """
        return [
            self._build_brand_genesis(),
            self._build_crowdfunding_lean(),
            self._build_crowdfunding_full(),
            self._build_bootstrapped_dtc(),
            self._build_enterprise_gtm(),
            self._build_custom_hybrid(),
        ]
    
    def _build_brand_genesis(self) -> Scenario:
        """Brand Genesis scenario for pre-launch, bootstrapped"""
        return Scenario(
            id=ScenarioType.BRAND_GENESIS,
            name="🏗️ Brand Genesis (Lean)",
            emoji="🏗️",
            description="Foundation-building for pre-launch brands with minimal budget. Focus on core identity and positioning.",
            best_for_budget=BudgetTier.BOOTSTRAPPED,
            best_for_channels=[
                LaunchChannel.ORGANIC,
                LaunchChannel.DTC,
            ],
            best_for_maturity=[MaturityStage.PRE_LAUNCH],
            skill_ids=[
                "niche-validator",
                "competitor-analysis",
                "brand-name-studio",
                "buyer-persona",
                "product-positioning-summary",
                "mds-messaging-direction-summary",
                "voice-and-tone",
                "visual-identity-core",
            ],
            execution_context=ExecutionContext(
                budget_tier=BudgetTier.BOOTSTRAPPED,
                tone="scrappy, authentic, founder-led",
                output_format="minimal",
                depth_level="surface",
                quality_bar="mvp",
                token_limit_per_skill=3000,
                prioritize="speed",
            ),
            estimated_cost_usd=4000,
            estimated_tokens=24000,
            estimated_timeline_days="1-2 days",
            deliverables=[
                "Brand name options",
                "Buyer persona (abbreviated)",
                "Positioning statement",
                "Messaging direction",
                "Voice & tone guide (lean)",
                "Visual identity direction",
            ],
            skip_deliverables=[
                "Campaign page",
                "Video script",
                "Email sequences",
                "Paid ads",
                "Press release",
            ],
            tags=["foundation", "pre-launch", "bootstrap", "minimal"],
        )
    
    def _build_crowdfunding_lean(self) -> Scenario:
        """Lean crowdfunding scenario"""
        return Scenario(
            id=ScenarioType.CROWDFUNDING_LEAN,
            name="🎯 Crowdfunding Lean",
            emoji="🎯",
            description="Budget-optimized Kickstarter/Indiegogo campaign with essential assets. Focus on conversion and launch velocity.",
            best_for_budget=BudgetTier.LEAN,
            best_for_channels=[
                LaunchChannel.KICKSTARTER,
                LaunchChannel.INDIEGOGO,
            ],
            best_for_maturity=[
                MaturityStage.LAUNCH_READY,
            ],
            skill_ids=[
                "buyer-persona",
                "competitor-analysis",
                "detailed-product-description",
                "product-positioning-summary",
                "mds-messaging-direction-summary",
                "voice-and-tone",
                "campaign-page-copy",
                "pre-launch-ads",
                "campaign-video-script",
                "pre-launch-email-sequence",
                "live-campaign-ads",
                "press-release-copy",
            ],
            execution_context=ExecutionContext(
                budget_tier=BudgetTier.LEAN,
                tone="conversion-focused, urgent, social-proof-heavy",
                output_format="standard",
                depth_level="focused",
                quality_bar="standard",
                token_limit_per_skill=5000,
                platform_constraints=[
                    "kickstarter_page_structure",
                    "60s_video_max",
                    "mobile_first_ads",
                ],
                prioritize="balanced",
            ),
            estimated_cost_usd=12500,
            estimated_tokens=60000,
            estimated_timeline_days="2-3 days",
            deliverables=[
                "Campaign page (30-section format)",
                "60s video script",
                "Pre-launch ads (Meta focus)",
                "Pre-launch email sequence",
                "Live campaign ads",
                "Press release",
            ],
            skip_deliverables=[
                "Welcome emails",
                "Packaging design",
                "Community management",
                "Affiliate program",
            ],
            tags=["crowdfunding", "lean", "conversion", "kickstarter"],
        )
    
    def _build_crowdfunding_full(self) -> Scenario:
        """Full crowdfunding scenario"""
        return Scenario(
            id=ScenarioType.CROWDFUNDING_FULL,
            name="🚀 Crowdfunding Full",
            emoji="🚀",
            description="Complete crowdfunding campaign with all assets. Agency-grade quality for premium positioning.",
            best_for_budget=BudgetTier.STANDARD,
            best_for_channels=[
                LaunchChannel.KICKSTARTER,
                LaunchChannel.INDIEGOGO,
            ],
            best_for_maturity=[
                MaturityStage.LAUNCH_READY,
                MaturityStage.GROWTH,
            ],
            skill_ids=[
                "buyer-persona",
                "competitor-analysis",
                "detailed-product-description",
                "product-positioning-summary",
                "mds-messaging-direction-summary",
                "voice-and-tone",
                "campaign-page-copy",
                "pre-launch-ads",
                "campaign-video-script",
                "welcome-email-sequence",
                "pre-launch-email-sequence",
                "launch-email-sequence",
                "live-campaign-ads",
                "press-release-copy",
                "social-content-engine",
                "influencer-outreach-pro",
                "affiliate-program-designer",
                "packaging-experience-designer",
                "unboxing-journey-guide",
                "update-strategy-sequencer",
            ],
            execution_context=ExecutionContext(
                budget_tier=BudgetTier.STANDARD,
                tone="premium, aspirational, community-driven",
                output_format="maximum",
                depth_level="comprehensive",
                quality_bar="premium",
                token_limit_per_skill=10000,
                platform_constraints=[
                    "kickstarter_page_structure",
                    "a_b_test_variants",
                    "convertkit_integration",
                ],
                prioritize="quality",
            ),
            estimated_cost_usd=28000,
            estimated_tokens=140000,
            estimated_timeline_days="4-5 days",
            deliverables=[
                "Campaign page (A/B variants)",
                "Video script (90s, full production notes)",
                "Full email suite (welcome, pre-launch, launch)",
                "Multi-platform ads",
                "Press release (AP style)",
                "Social content calendar",
                "Influencer outreach",
                "Affiliate program",
                "Packaging design brief",
                "Unboxing experience",
                "Campaign updates strategy",
            ],
            skip_deliverables=[],
            tags=["crowdfunding", "full", "premium", "comprehensive"],
        )
    
    def _build_bootstrapped_dtc(self) -> Scenario:
        """Bootstrapped DTC scenario"""
        return Scenario(
            id=ScenarioType.BOOTSTRAPPED_DTC,
            name="🛒 Bootstrapped DTC",
            emoji="🛒",
            description="Self-funded direct-to-consumer launch via Shopify/WooCommerce. Focus on organic marketing and founder-led growth.",
            best_for_budget=BudgetTier.BOOTSTRAPPED,
            best_for_channels=[
                LaunchChannel.DTC,
                LaunchChannel.ORGANIC,
            ],
            best_for_maturity=[
                MaturityStage.PRE_LAUNCH,
                MaturityStage.LAUNCH_READY,
            ],
            skill_ids=[
                "buyer-persona",
                "competitor-analysis",
                "product-positioning-summary",
                "mds-messaging-direction-summary",
                "voice-and-tone",
                "campaign-page-copy",
                "social-content-engine",
                "short-form-hook-generator",
                "welcome-email-sequence",
            ],
            execution_context=ExecutionContext(
                budget_tier=BudgetTier.BOOTSTRAPPED,
                tone="authentic, founder-led, community-first",
                output_format="standard",
                depth_level="focused",
                quality_bar="standard",
                token_limit_per_skill=4000,
                platform_constraints=[
                    "shopify_liquid_templates",
                    "instagram_reels_hooks",
                    "tiktok_viral_patterns",
                    "klaviyo_flows",
                ],
                prioritize="cost",
            ),
            estimated_cost_usd=8000,
            estimated_tokens=36000,
            estimated_timeline_days="1-2 days",
            deliverables=[
                "Product page copy (Shopify format)",
                "Social content calendar (30 days)",
                "Viral hooks (TikTok/Reels)",
                "Welcome email sequence (Klaviyo)",
            ],
            skip_deliverables=[
                "Paid ads",
                "Video production",
                "Press release",
                "Packaging design",
            ],
            tags=["dtc", "bootstrap", "organic", "founder-led"],
        )
    
    def _build_enterprise_gtm(self) -> Scenario:
        """Enterprise SaaS GTM scenario"""
        return Scenario(
            id=ScenarioType.ENTERPRISE_GTM,
            name="🏢 Enterprise GTM",
            emoji="🏢",
            description="B2B SaaS go-to-market with enterprise-grade positioning. Focus on data-driven messaging and compliance.",
            best_for_budget=BudgetTier.PREMIUM,
            best_for_channels=[
                LaunchChannel.ENTERPRISE,
                LaunchChannel.SAAS,
            ],
            best_for_maturity=[
                MaturityStage.LAUNCH_READY,
                MaturityStage.GROWTH,
                MaturityStage.ESTABLISHED,
            ],
            skill_ids=[
                "buyer-persona",
                "competitor-analysis",
                "product-positioning-summary",
                "mds-messaging-direction-summary",
                "voice-and-tone",
                "campaign-page-copy",
                "press-release-copy",
                # "pitchdeck-skill",  # TODO: Enable after Phase 4 skill migration
                "welcome-email-sequence",
                "launch-email-sequence",
                "social-content-engine",
                "influencer-outreach-pro",
            ],
            execution_context=ExecutionContext(
                budget_tier=BudgetTier.PREMIUM,
                tone="authoritative, data-driven, enterprise-grade",
                output_format="maximum",
                depth_level="exhaustive",
                quality_bar="enterprise",
                token_limit_per_skill=15000,
                platform_constraints=[
                    "gdpr_compliant_copy",
                    "accessibility_wcag_aa",
                    "security_claims_substantiated",
                    "marketo_integration",
                ],
                prioritize="quality",
            ),
            estimated_cost_usd=45000,
            estimated_tokens=180000,
            estimated_timeline_days="5-7 days",
            deliverables=[
                "Landing page (legal-review ready)",
                "Press release (substantiated claims)",
                "Pitch deck (investor-grade)",
                "Email sequences (Marketo)",
                "LinkedIn content strategy",
                "Analyst relations outreach",
            ],
            skip_deliverables=[
                "Physical product assets",
                "Packaging design",
                "Video production",
            ],
            tags=["enterprise", "b2b", "saas", "gtm"],
        )
    
    def _build_custom_hybrid(self) -> Scenario:
        """Custom hybrid scenario"""
        return Scenario(
            id=ScenarioType.CUSTOM_HYBRID,
            name="⚙️ Custom Hybrid",
            emoji="⚙️",
            description="Pick and choose skills with smart recommendations. System analyzes selections and suggests optimal configuration.",
            best_for_budget=BudgetTier.STANDARD,
            best_for_channels=[],  # Supports all
            best_for_maturity=[],  # Supports all
            skill_ids=[],  # User selects
            execution_context=ExecutionContext(
                budget_tier=BudgetTier.STANDARD,
                tone="balanced",
                output_format="standard",
                depth_level="focused",
                quality_bar="standard",
                token_limit_per_skill=5000,
                prioritize="balanced",
            ),
            estimated_cost_usd=0,  # Calculated dynamically
            estimated_tokens=0,
            estimated_timeline_days="Varies",
            deliverables=["Varies based on selection"],
            skip_deliverables=[],
            tags=["custom", "flexible", "hybrid"],
        )
