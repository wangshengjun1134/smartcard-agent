"""Discovery Primitive Skills - Card capability detection.

This module provides skills for discovering and identifying
card type, capabilities, and supported features.
"""

from typing import Dict, Any, List
from skills.base.base_skill import BaseSkill, SkillResult
from apdu.constants.file_ids import AID_USIM, AID_ISIM, AID_CSIM


class DetectCardType(BaseSkill):
    """Detect card type (SIM, USIM, ISIM, eUICC, etc.).

    Analyzes ATR and probes for applications to determine card type.

    Parameters:
        probe_applications: Probe for applications (default: True)

    Returns:
        SkillResult with card type and capabilities.

    Example:
        result = await skill.run(ctx, {})
        card_type = result.metadata["card_type"]
    """

    name = "detect_card_type"
    description = "Detect card type (SIM/USIM/ISIM/eUICC)"
    dangerous = False
    requires_pin = False
    requires_secure_channel = False

    # Known ATR patterns
    ATR_PATTERNS = {
        "USIM": ["3B9F96801F878031E073FE211B67"],
        "eUICC": ["3B9F96801F87828031E073FE211B"],
        "JavaCard": ["3B7F9500008031B8"],
        "SIM": ["3B9B950081"],
    }

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute detect card type skill."""
        probe_applications = params.get("probe_applications", True)
        
        card_type = "Unknown"
        capabilities = []
        
        # Analyze ATR
        atr = ctx.pcsc.atr
        if atr:
            atr_hex = atr.hex().upper()
            
            for type_name, patterns in self.ATR_PATTERNS.items():
                for pattern in patterns:
                    if atr_hex.startswith(pattern.upper()):
                        card_type = type_name
                        capabilities.append(f"atr_match_{type_name.lower()}")
                        break
        
        ctx.runtime_ctx.card_type = card_type
        
        # Probe applications
        if probe_applications:
            from skills.filesystem import DiscoverApplications
            
            discover_skill = DiscoverApplications()
            apps_result = await discover_skill.run(ctx, {})
            
            if apps_result.success:
                apps = apps_result.metadata.get("applications", [])
                
                # Determine card type from applications
                for app in apps:
                    app_name = app.get("name", "")
                    aid = app.get("aid", "")
                    
                    if app_name == "USIM" or aid == AID_USIM:
                        card_type = "USIM"
                        capabilities.append("usim_app")
                    elif app_name == "ISIM" or aid == AID_ISIM:
                        card_type = "ISIM"
                        capabilities.append("isim_app")
                    elif app_name == "CSIM" or aid == AID_CSIM:
                        card_type = "CSIM"
                        capabilities.append("csim_app")
        
        ctx.runtime_ctx.card_type = card_type
        for cap in capabilities:
            ctx.runtime_ctx.add_capability(cap)
        
        return SkillResult(
            success=True,
            metadata={
                "card_type": card_type,
                "capabilities": capabilities,
                "atr": atr.hex().upper() if atr else None,
            }
        )


class DetectUSIM(BaseSkill):
    """Detect if card is USIM.

    Specifically probes for USIM application.

    Parameters:
        None

    Returns:
        SkillResult with USIM detection status.

    Example:
        result = await skill.run(ctx, {})
        if result.metadata["is_usim"]:
            # Card is USIM
    """

    name = "detect_usim"
    description = "Detect USIM application"
    dangerous = False
    requires_pin = False
    requires_secure_channel = False

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute detect USIM skill."""
        from skills.primitive.iso7816 import SelectSkill
        
        select_skill = SelectSkill()
        result = await select_skill.run(ctx, {"aid": AID_USIM})
        
        is_usim = result.success
        
        if is_usim:
            ctx.runtime_ctx.add_capability("usim")
        
        return SkillResult(
            success=True,
            metadata={
                "is_usim": is_usim,
                "aid": AID_USIM,
            }
        )


class DetectISIM(BaseSkill):
    """Detect if card is ISIM.

    Specifically probes for ISIM application (IMS support).

    Parameters:
        None

    Returns:
        SkillResult with ISIM detection status.

    Example:
        result = await skill.run(ctx, {})
    """

    name = "detect_isim"
    description = "Detect ISIM application"
    dangerous = False
    requires_pin = False
    requires_secure_channel = False

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute detect ISIM skill."""
        from skills.primitive.iso7816 import SelectSkill
        
        select_skill = SelectSkill()
        result = await select_skill.run(ctx, {"aid": AID_ISIM})
        
        is_isim = result.success
        
        if is_isim:
            ctx.runtime_ctx.add_capability("isim")
        
        return SkillResult(
            success=True,
            metadata={"is_isim": is_isim}
        )


class DetectEUICC(BaseSkill):
    """Detect if card is eUICC.

    Probes for eUICC characteristics and applications.

    Parameters:
        None

    Returns:
        SkillResult with eUICC detection status.

    Example:
        result = await skill.run(ctx, {})
    """

    name = "detect_euicc"
    description = "Detect eUICC card"
    dangerous = False
    requires_pin = False
    requires_secure_channel = False

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute detect eUICC skill."""
        # Check ATR for eUICC patterns
        atr = ctx.pcsc.atr
        atr_hex = atr.hex().upper() if atr else ""
        
        # eUICC typically has specific ATR pattern
        is_euicc = "7828" in atr_hex or "E073FE211B" in atr_hex
        
        # Also check for eUICC AID
        from skills.primitive.iso7816 import SelectSkill
        
        # eUICC AID: A0000005591010FFFFFFFF8900000100
        euicc_aid = "A0000005591010FFFFFFFF8900000100"
        
        select_skill = SelectSkill()
        result = await select_skill.run(ctx, {"aid": euicc_aid})
        
        if result.success:
            is_euicc = True
        
        if is_euicc:
            ctx.runtime_ctx.add_capability("euicc")
            ctx.runtime_ctx.card_type = "eUICC"
        
        return SkillResult(
            success=True,
            metadata={"is_euicc": is_euicc}
        )


class DetectSCP(BaseSkill):
    """Detect SCP support level.

    Determines which Secure Channel Protocols are supported.

    Parameters:
        None

    Returns:
        SkillResult with SCP support info.

    Example:
        result = await skill.run(ctx, {})
        scp_versions = result.metadata["scp_versions"]
    """

    name = "detect_scp"
    description = "Detect SCP support level"
    dangerous = False
    requires_pin = False
    requires_secure_channel = False

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute detect SCP skill."""
        scp_versions = []
        
        # Try SCP03 initialization
        from skills.scp03 import SCP03InitializeUpdate
        
        scp03_skill = SCP03InitializeUpdate()
        result = await scp03_skill.run(ctx, {"key_set": 1, "key_version": 1})
        
        if result.success:
            scp_versions.append("scp03")
            ctx.runtime_ctx.add_capability("scp03")
        
        # SCP80 detection would require OTA-specific probing
        # (placeholder for future implementation)
        
        return SkillResult(
            success=True,
            metadata={
                "scp_versions": scp_versions,
                "scp03": "scp03" in scp_versions,
                "scp80": False,  # Placeholder
            }
        )


class DetectGP(BaseSkill):
    """Detect GlobalPlatform support.

    Determines if card is a GlobalPlatform-compliant card.

    Parameters:
        None

    Returns:
        SkillResult with GP support status.

    Example:
        result = await skill.run(ctx, {})
    """

    name = "detect_gp"
    description = "Detect GlobalPlatform support"
    dangerous = False
    requires_pin = False
    requires_secure_channel = False

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute detect GP skill."""
        from skills.primitive.iso7816 import SelectSkill
        
        # Try to select ISD (Issuer Security Domain)
        # ISD AID: A0000001510000
        isd_aid = "A0000001510000"
        
        select_skill = SelectSkill()
        result = await select_skill.run(ctx, {"aid": isd_aid})
        
        is_gp = result.success
        
        if is_gp:
            ctx.runtime_ctx.add_capability("globalplatform")
        
        return SkillResult(
            success=True,
            metadata={
                "is_gp": is_gp,
                "isd_aid": isd_aid,
            }
        )


class ProbeCapabilities(BaseSkill):
    """Probe card capabilities.

    Comprehensive capability probing including:
    - Logical channels
    - Secure messaging
    - File system structure
    - Supported commands

    Parameters:
        probe_depth: Depth of probing (quick, normal, full)

    Returns:
        SkillResult with full capability list.

    Example:
        result = await skill.run(ctx, {"probe_depth": "normal"})
    """

    name = "probe_capabilities"
    description = "Probe card capabilities comprehensively"
    dangerous = False
    requires_pin = False
    requires_secure_channel = False

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute probe capabilities skill."""
        probe_depth = params.get("probe_depth", "normal")
        
        capabilities = []
        
        # Logical channel support
        from skills.primitive.iso7816 import ManageChannelSkill
        
        channel_skill = ManageChannelSkill()
        result = await channel_skill.run(ctx, {"action": "open"})
        
        if result.success:
            capabilities.append("logical_channels")
            ctx.runtime_ctx.add_capability("logical_channels")
            # Close the channel
            channel_skill.run(ctx, {"action": "close"})
        
        # Secure channel support
        scp_result = await DetectSCP().run(ctx, {})
        capabilities.extend(scp_result.metadata.get("scp_versions", []))
        
        # GP support
        gp_result = await DetectGP().run(ctx, {})
        if gp_result.metadata.get("is_gp"):
            capabilities.append("globalplatform")
        
        # Card type
        type_result = await DetectCardType().run(ctx, {"probe_applications": True})
        capabilities.append(f"card_type_{type_result.metadata.get('card_type', 'unknown').lower()}")
        
        return SkillResult(
            success=True,
            metadata={
                "capabilities": capabilities,
                "probe_depth": probe_depth,
                "card_type": type_result.metadata.get("card_type"),
            }
        )


class FingerprintCard(BaseSkill):
    """Fingerprint card for identification.

    Creates a unique fingerprint from card characteristics
    for tracking and logging purposes.

    Parameters:
        None

    Returns:
        SkillResult with card fingerprint.

    Example:
        result = await skill.run(ctx, {})
        fingerprint = result.metadata["fingerprint"]
    """

    name = "fingerprint_card"
    description = "Fingerprint card for identification"
    dangerous = False
    requires_pin = False
    requires_secure_channel = False

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute fingerprint card skill."""
        import hashlib
        
        # Collect fingerprint data
        atr = ctx.pcsc.atr.hex().upper() if ctx.pcsc.atr else ""
        
        # Get applications
        from skills.filesystem import DiscoverApplications
        
        discover_skill = DiscoverApplications()
        apps_result = await discover_skill.run(ctx, {})
        apps = [app.get("aid", "") for app in apps_result.metadata.get("applications", [])]
        
        # Create fingerprint hash
        fingerprint_data = atr + "".join(apps)
        fingerprint = hashlib.sha256(fingerprint_data.encode()).hexdigest()[:16]
        
        return SkillResult(
            success=True,
            metadata={
                "fingerprint": fingerprint,
                "atr": atr,
                "applications": apps,
            }
        )


def register_discovery_skills(registry: Any) -> None:
    """Register all Discovery Primitive skills."""
    registry.register(DetectCardType(), "primitive")
    registry.register(DetectUSIM(), "primitive")
    registry.register(DetectISIM(), "primitive")
    registry.register(DetectEUICC(), "primitive")
    registry.register(DetectSCP(), "primitive")
    registry.register(DetectGP(), "primitive")
    registry.register(ProbeCapabilities(), "primitive")
    registry.register(FingerprintCard(), "primitive")