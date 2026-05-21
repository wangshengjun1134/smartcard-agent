"""Discover Card Skill - discover card capabilities and type.

This exploratory skill identifies the card type and capabilities
by analyzing the ATR and probing for applications.
"""

from typing import Dict, Any, List
from skills.base.base_skill import BaseSkill, SkillResult
from apdu.constants.file_ids import AID_USIM, AID_ISIM, AID_CSIM, AID_ARA_C


class DiscoverCardSkill(BaseSkill):
    """Exploratory skill for discovering card capabilities.

    This skill:
    1. Analyzes the ATR to identify card type
    2. Probes for common applications (USIM, ISIM, CSIM)
    3. Updates runtime context with discovered capabilities

    Example:
        result = await skill.run(ctx, {})
        card_type = result.metadata["card_type"]
        capabilities = result.metadata["capabilities"]
    """

    name = "discover_card"
    description = "Discover card type and capabilities"
    dangerous = False
    requires_pin = False
    requires_secure_channel = False

    # Known ATR patterns
    ATR_PATTERNS = {
        # USIM cards
        "3B9F96801F878031E073FE211B674A3575303502": "USIM",
        "3B9F96801F878031E073FE211F672FA575730030": "USIM",
        # eUICC cards
        "3B9F96801F87828031E073FE211B67": "eUICC",
        # JavaCard
        "3B7F9500008031B8": "JavaCard",
        # Generic SIM
        "3B9B950081": "SIM",
    }

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute DISCOVER CARD skill.

        Args:
            ctx: Skill execution context
            params: {} (no parameters required)

        Returns:
            SkillResult with card info.
        """
        try:
            capabilities: List[str] = []
            discovered_apps: List[str] = []
            card_type = "Unknown"

            # Step 1: Analyze ATR
            atr = ctx.pcsc.atr
            if atr:
                atr_hex = atr.hex().upper()
                card_type = analyze_atr(atr_hex, self.ATR_PATTERNS)

                # Add basic capabilities based on ATR
                capabilities.append("atr_analysis")
                capabilities.append("pcsc_connection")

            # Update context with initial info
            ctx.runtime_ctx.card_type = card_type

            # Step 2: Probe for applications
            apps_to_probe = [
                (AID_USIM, "USIM"),
                (AID_ISIM, "ISIM"),
                (AID_CSIM, "CSIM"),
                (AID_ARA_C, "ARA-C"),
            ]

            for aid, app_name in apps_to_probe:
                try:
                    # Try to select by AID
                    result = await ctx.execute_skill("select_by_aid", {"aid": aid})
                    if result.success:
                        discovered_apps.append(aid)
                        capabilities.append(f"app_{app_name.lower()}")
                except Exception:
                    # Application not found - continue
                    pass

            # Update runtime context
            for cap in capabilities:
                ctx.runtime_ctx.add_capability(cap)
            for app in discovered_apps:
                ctx.runtime_ctx.add_discovered_app(app)

            # Determine final card type
            if "app_usim" in capabilities:
                card_type = "USIM"
            elif "app_isim" in capabilities:
                card_type = "ISIM"
            elif "app_csim" in capabilities:
                card_type = "CSIM"
            elif "eUICC" in card_type:
                card_type = "eUICC"

            ctx.runtime_ctx.card_type = card_type

            return SkillResult(
                success=True,
                metadata={
                    "card_type": card_type,
                    "capabilities": capabilities,
                    "discovered_apps": discovered_apps,
                    "atr": atr.hex().upper() if atr else None,
                }
            )

        except Exception as e:
            return SkillResult(success=False, error=str(e))


def analyze_atr(atr_hex: str, patterns: Dict[str, str]) -> str:
    """Analyze ATR to determine card type.

    Args:
        atr_hex: ATR as hex string
        patterns: Known ATR patterns

    Returns:
        Card type string.
    """
    # Try exact match first
    for pattern, card_type in patterns.items():
        if atr_hex.startswith(pattern.upper()) or atr_hex.upper().startswith(pattern.upper()):
            return card_type

    # Analyze ATR structure for hints
    # Check for specific indicators in ATR
    atr_upper = atr_hex.upper()

    # Check for GlobalPlatform indicators
    if "8031" in atr_upper or "81" in atr_upper:
        # Likely JavaCard or GlobalPlatform card
        if "9680" in atr_upper:
            return "USIM"
        return "JavaCard"

    # Check for eUICC indicators
    if "7828" in atr_upper:
        return "eUICC"

    # Default
    return "Unknown"