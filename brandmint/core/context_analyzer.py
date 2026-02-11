"""
Context Analyzer - Detects business context from product data
Phase 1 implementation
"""

import re
from typing import Optional, Dict, Any
from pathlib import Path

from ..models.product import (
    ProductData,
    LaunchContext,
    BudgetTier,
    LaunchChannel,
    MaturityStage,
    TimelineUrgency,
    TeamSize,
)


class ContextAnalyzer:
    """
    Analyzes product data to infer business context
    """
    
    def __init__(self):
        self.channel_keywords = {
            LaunchChannel.KICKSTARTER: ["kickstarter", "crowdfunding", "backer"],
            LaunchChannel.INDIEGOGO: ["indiegogo", "crowdfunding", "campaign"],
            LaunchChannel.DTC: ["shopify", "dtc", "direct-to-consumer", "ecommerce", "online store"],
            LaunchChannel.ENTERPRISE: ["enterprise", "b2b", "saas", "corporate"],
            LaunchChannel.SAAS: ["saas", "software", "subscription", "platform", "api"],
            LaunchChannel.ORGANIC: ["organic", "bootstrap", "self-funded", "lean"],
        }
    
    def analyze(self, product: ProductData) -> LaunchContext:
        """
        Analyze product data and detect launch context
        
        Returns fully populated LaunchContext
        """
        context = product.launch_context
        
        # Detect each dimension
        if context.channel == LaunchChannel.UNKNOWN:
            context.channel = self.detect_channel(product)
        
        if context.budget_tier == BudgetTier.STANDARD and not context.budget_amount:
            context.budget_tier = self.detect_budget_tier(product)
        
        if context.maturity_stage == MaturityStage.LAUNCH_READY:
            context.maturity_stage = self.detect_maturity(product)
        
        if context.timeline_urgency == TimelineUrgency.STANDARD:
            context.timeline_urgency = self.detect_urgency(product)
        
        if context.team_size == TeamSize.SMALL:
            context.team_size = self.detect_team_size(product)
        
        return context
    
    def detect_channel(self, product: ProductData) -> LaunchChannel:
        """
        Detect launch channel from category, messaging, and context
        """
        # Check explicit launch context
        if product.launch_context.channel != LaunchChannel.UNKNOWN:
            return product.launch_context.channel
        
        # Check category and messaging for keywords
        search_text = " ".join([
            product.brand.category.lower(),
            product.positioning_statement.lower(),
            str(product.messaging).lower(),
        ])
        
        # Score each channel
        channel_scores = {}
        for channel, keywords in self.channel_keywords.items():
            score = sum(1 for kw in keywords if kw in search_text)
            if score > 0:
                channel_scores[channel] = score
        
        if channel_scores:
            return max(channel_scores, key=channel_scores.get)
        
        # Default heuristics
        if "smart" in search_text or "hardware" in search_text or "wearable" in search_text:
            return LaunchChannel.KICKSTARTER
        
        if "software" in search_text or "app" in search_text:
            return LaunchChannel.SAAS
        
        return LaunchChannel.DTC
    
    def detect_budget_tier(self, product: ProductData) -> BudgetTier:
        """
        Detect budget tier from explicit budget or context clues
        """
        # Explicit budget amount
        if product.launch_context.budget_amount:
            amount = product.launch_context.budget_amount
            if amount < 5000:
                return BudgetTier.BOOTSTRAPPED
            elif amount < 20000:
                return BudgetTier.LEAN
            elif amount < 100000:
                return BudgetTier.STANDARD
            else:
                return BudgetTier.PREMIUM
        
        # Infer from team size
        if product.launch_context.team_size == TeamSize.SOLO:
            return BudgetTier.BOOTSTRAPPED
        elif product.launch_context.team_size == TeamSize.AGENCY:
            return BudgetTier.PREMIUM
        
        # Infer from product price
        if product.price:
            if product.price < 50:
                return BudgetTier.BOOTSTRAPPED
            elif product.price < 200:
                return BudgetTier.LEAN
            elif product.price < 500:
                return BudgetTier.STANDARD
            else:
                return BudgetTier.PREMIUM
        
        # Infer from channel
        channel = self.detect_channel(product)
        if channel in [LaunchChannel.ORGANIC, LaunchChannel.DTC]:
            return BudgetTier.LEAN
        elif channel == LaunchChannel.ENTERPRISE:
            return BudgetTier.PREMIUM
        
        return BudgetTier.STANDARD
    
    def detect_maturity(self, product: ProductData) -> MaturityStage:
        """
        Detect brand maturity from existing assets
        """
        # Check for existing brand signals
        has_brand = product.launch_context.has_existing_brand
        has_content = product.launch_context.has_existing_content
        
        if not has_brand and not has_content:
            return MaturityStage.PRE_LAUNCH
        
        if has_brand and not has_content:
            return MaturityStage.LAUNCH_READY
        
        if has_brand and has_content:
            # Check if they have traction
            if product.target_regions and len(product.target_regions) > 2:
                return MaturityStage.ESTABLISHED
            return MaturityStage.GROWTH
        
        return MaturityStage.LAUNCH_READY
    
    def detect_urgency(self, product: ProductData) -> TimelineUrgency:
        """
        Detect timeline urgency from context
        """
        if product.launch_context.timeline_weeks:
            weeks = product.launch_context.timeline_weeks
            if weeks < 2:
                return TimelineUrgency.RUSHED
            elif weeks <= 8:
                return TimelineUrgency.STANDARD
            else:
                return TimelineUrgency.THOROUGH
        
        # Default based on budget (tight budget = rushed timeline)
        budget = self.detect_budget_tier(product)
        if budget == BudgetTier.BOOTSTRAPPED:
            return TimelineUrgency.RUSHED
        elif budget == BudgetTier.PREMIUM:
            return TimelineUrgency.THOROUGH
        
        return TimelineUrgency.STANDARD
    
    def detect_team_size(self, product: ProductData) -> TeamSize:
        """
        Detect team size from context
        """
        if product.launch_context.team_count:
            count = product.launch_context.team_count
            if count == 1:
                return TeamSize.SOLO
            elif count <= 5:
                return TeamSize.SMALL
            else:
                return TeamSize.AGENCY
        
        # Infer from budget
        budget = self.detect_budget_tier(product)
        if budget == BudgetTier.BOOTSTRAPPED:
            return TeamSize.SOLO
        elif budget == BudgetTier.PREMIUM:
            return TeamSize.AGENCY
        
        return TeamSize.SMALL
    
    def explain_detection(self, product: ProductData, context: LaunchContext) -> Dict[str, str]:
        """
        Explain how context was detected (for debugging/transparency)
        """
        return {
            "channel": f"Detected '{context.channel.value}' from category keywords",
            "budget_tier": f"Detected '{context.budget_tier.value}' from {self._budget_reason(product, context)}",
            "maturity": f"Detected '{context.maturity_stage.value}' from brand assets",
            "urgency": f"Detected '{context.timeline_urgency.value}' from {self._urgency_reason(product, context)}",
            "team_size": f"Detected '{context.team_size.value}' from {self._team_reason(product, context)}",
        }
    
    def _budget_reason(self, product: ProductData, context: LaunchContext) -> str:
        if context.budget_amount:
            return f"explicit budget (${context.budget_amount:,})"
        elif product.price:
            return f"product price (${product.price})"
        else:
            return "team size and channel"
    
    def _urgency_reason(self, product: ProductData, context: LaunchContext) -> str:
        if context.timeline_weeks:
            return f"explicit timeline ({context.timeline_weeks} weeks)"
        else:
            return "budget tier"
    
    def _team_reason(self, product: ProductData, context: LaunchContext) -> str:
        if context.team_count:
            return f"explicit team count ({context.team_count} people)"
        else:
            return "budget tier"
