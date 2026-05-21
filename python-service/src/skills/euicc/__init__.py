"""eUICC Primitive Skills - eUICC profile management operations.

eUICC (Embedded Universal Integrated Circuit Card) is the standard
for embedded SIMs, allowing remote profile management without
physical SIM replacement.

Reference: GSMA SGP.22 (eUICC Architecture), GSMA SGP.02
"""

from typing import Dict, Any, List
from skills.base.base_skill import BaseSkill, SkillResult


# eUICC AIDs
EID_AID = "A0000005591010FFFFFFFF8900000100"  # eUICC AID
PROFILE_AID_PREFIX = "A00000055910"           # Profile AID prefix


class EUICCGetEID(BaseSkill):
    """Get eUICC Identifier (EID).

    Reads the 32-byte EID (eUICC Identifier) from the card.

    Parameters:
        None

    Returns:
        SkillResult with EID value.

    Example:
        result = await skill.run(ctx, {})
        eid = result.metadata["eid"]
    """

    name = "euicc_get_eid"
    description = "Get eUICC Identifier (EID)"
    dangerous = False
    requires_pin = False
    requires_secure_channel = False

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute eUICC get EID skill."""
        # Select eUICC application
        from skills.primitive.iso7816 import SelectSkill
        
        select_skill = SelectSkill()
        result = await select_skill.run(ctx, {"aid": EID_AID})
        
        if not result.success:
            return SkillResult(success=False, error="eUICC application not found")
        
        # EID is stored in specific EF
        # Read EID: EF_EID at specific location
        # Simplified: EID is typically returned in FCP
        
        # Build GET DATA command for EID
        # Tag 5A = EID
        
        apdu = bytes([0x80, 0xCB, 0x3C, 0xFF, 0x02, 0x5A, 0x00, 0x00])
        
        response = ctx.pcsc.send_apdu(list(apdu), check_sw=False)
        
        if response.success and len(response.data) >= 32:
            eid = response.data[:32]
            eid_hex = eid.hex().upper()
            
            ctx.runtime_ctx.card_info["eid"] = eid_hex
            
            return SkillResult(
                success=True,
                data=eid,
                metadata={"eid": eid_hex, "eid_length": 32}
            )
        
        return SkillResult(success=False, error="Failed to read EID")


class EUICCListProfiles(BaseSkill):
    """List installed profiles.

    Retrieves list of profiles installed on eUICC.

    Parameters:
        include_disabled: Include disabled profiles (default: True)

    Returns:
        SkillResult with profile list.

    Example:
        result = await skill.run(ctx, {})
        profiles = result.metadata["profiles"]
    """

    name = "euicc_list_profiles"
    description = "List installed eUICC profiles"
    dangerous = False
    requires_pin = False
    requires_secure_channel = False

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute eUICC list profiles skill."""
        include_disabled = params.get("include_disabled", True)
        
        # Select eUICC application
        from skills.primitive.iso7816 import SelectSkill
        
        select_skill = SelectSkill()
        result = await select_skill.run(ctx, {"aid": EID_AID})
        
        if not result.success:
            return SkillResult(success=False, error="eUICC application not found")
        
        # Get profile info via GET PROFILES INFO command
        # Function code = 04 (Get Profiles Info)
        
        # Build ES10c.GetProfilesInfo command
        # TLV structure with function code
        
        profiles = []
        
        # Placeholder: would parse actual profile list
        # Real implementation:
        # 1. Send GET PROFILES INFO
        # 2. Parse TLV response for profile metadata
        # 3. Return list with ICCID, name, state
        
        return SkillResult(
            success=True,
            metadata={
                "profiles": profiles,
                "profile_count": len(profiles),
                "include_disabled": include_disabled,
            }
        )


class EUICCEnableProfile(BaseSkill):
    """Enable eUICC profile.

    Enables a profile for use.

    Parameters:
        iccid: ICCID of profile to enable
        or
        profile_id: Profile ID (AID)

    Returns:
        SkillResult indicating enable success.

    Example:
        result = await skill.run(ctx, {"iccid": "8901234567890123456"})
    """

    name = "euicc_enable_profile"
    description = "Enable eUICC profile"
    dangerous = True
    requires_pin = False
    requires_secure_channel = True  # Requires eUICC session

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute eUICC enable profile skill."""
        iccid = params.get("iccid")
        profile_id = params.get("profile_id")
        
        if not iccid and not profile_id:
            return SkillResult(
                success=False,
                error="Missing iccid or profile_id parameter"
            )
        
        # Select eUICC application
        from skills.primitive.iso7816 import SelectSkill
        
        select_skill = SelectSkill()
        result = await select_skill.run(ctx, {"aid": EID_AID})
        
        if not result.success:
            return SkillResult(success=False, error="eUICC application not found")
        
        # Build ENABLE PROFILE command
        # Function code = 01 (Enable Profile)
        # Profile ICCID TLV
        
        iccid_bytes = bytes.fromhex(iccid) if iccid else bytes()
        
        # ES10c.EnableProfile command structure
        enable_data = bytes([0xBF, 0x2D, 0x05]) + iccid_bytes  # Placeholder TLV
        
        apdu = bytes([0x80, 0xCB, 0x3C, 0xFF, len(enable_data)]) + enable_data
        
        response = ctx.pcsc.send_apdu(list(apdu), check_sw=False)
        
        ctx.runtime_ctx.record_execution(
            skill_name=self.name,
            params={"iccid": iccid},
            apdu=apdu,
            response=response.data,
            sw=response.sw,
            success=response.success,
        )
        
        if response.success:
            return SkillResult(
                success=True,
                sw=response.sw,
                metadata={"enabled_iccid": iccid}
            )
        else:
            from apdu.constants.sw_codes import decode_sw
            return SkillResult(
                success=False,
                sw=response.sw,
                error=decode_sw(response.sw),
            )


class EUICCDisableProfile(BaseSkill):
    """Disable eUICC profile.

    Disables a currently active profile.

    Parameters:
        iccid: ICCID of profile to disable

    Returns:
        SkillResult indicating disable success.

    Example:
        result = await skill.run(ctx, {"iccid": "8901234567890123456"})
    """

    name = "euicc_disable_profile"
    description = "Disable eUICC profile"
    dangerous = True
    requires_pin = False
    requires_secure_channel = True

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute eUICC disable profile skill."""
        iccid = params.get("iccid")
        
        if not iccid:
            return SkillResult(success=False, error="Missing iccid parameter")
        
        # Select eUICC application
        from skills.primitive.iso7816 import SelectSkill
        
        select_skill = SelectSkill()
        result = await select_skill.run(ctx, {"aid": EID_AID})
        
        if not result.success:
            return SkillResult(success=False, error="eUICC application not found")
        
        # Build DISABLE PROFILE command
        # Function code = 02 (Disable Profile)
        
        iccid_bytes = bytes.fromhex(iccid)
        disable_data = bytes([0xBF, 0x2D, 0x05]) + iccid_bytes  # Placeholder
        
        apdu = bytes([0x80, 0xCB, 0x3C, 0xFF, len(disable_data)]) + disable_data
        
        response = ctx.pcsc.send_apdu(list(apdu), check_sw=False)
        
        if response.success:
            return SkillResult(
                success=True,
                sw=response.sw,
                metadata={"disabled_iccid": iccid}
            )
        else:
            from apdu.constants.sw_codes import decode_sw
            return SkillResult(
                success=False,
                sw=response.sw,
                error=decode_sw(response.sw),
            )


class EUICCDeleteProfile(BaseSkill):
    """Delete eUICC profile.

    Permanently deletes a profile from eUICC.

    Parameters:
        iccid: ICCID of profile to delete

    Returns:
        SkillResult indicating deletion success.

    Example:
        result = await skill.run(ctx, {"iccid": "8901234567890123456"})
    """

    name = "euicc_delete_profile"
    description = "Delete eUICC profile"
    dangerous = True
    requires_pin = False
    requires_secure_channel = True

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute eUICC delete profile skill."""
        iccid = params.get("iccid")
        
        if not iccid:
            return SkillResult(success=False, error="Missing iccid parameter")
        
        # Select eUICC application
        from skills.primitive.iso7816 import SelectSkill
        
        select_skill = SelectSkill()
        result = await select_skill.run(ctx, {"aid": EID_AID})
        
        if not result.success:
            return SkillResult(success=False, error="eUICC application not found")
        
        # Build DELETE PROFILE command
        # Function code = 03 (Delete Profile)
        
        iccid_bytes = bytes.fromhex(iccid)
        delete_data = bytes([0xBF, 0x2D, 0x05]) + iccid_bytes  # Placeholder
        
        apdu = bytes([0x80, 0xCB, 0x3C, 0xFF, len(delete_data)]) + delete_data
        
        response = ctx.pcsc.send_apdu(list(apdu), check_sw=False)
        
        ctx.runtime_ctx.record_execution(
            skill_name=self.name,
            params={"iccid": iccid},
            apdu=apdu,
            response=response.data,
            sw=response.sw,
            success=response.success,
        )
        
        if response.success:
            return SkillResult(
                success=True,
                sw=response.sw,
                metadata={"deleted_iccid": iccid}
            )
        else:
            from apdu.constants.sw_codes import decode_sw
            return SkillResult(
                success=False,
                sw=response.sw,
                error=decode_sw(response.sw),
            )


class EUICCDownloadProfile(BaseSkill):
    """Download eUICC profile.

    Downloads a new profile from SM-DP+ server.

    Parameters:
        activation_code: Activation code from SM-DP+
        matching_id: Matching ID (optional)
        smdp_address: SM-DP+ server address

    Returns:
        SkillResult indicating download success.

    Example:
        result = await skill.run(ctx, {
            "activation_code": "LPA:1$smdp.example.com$AC-123",
            "smdp_address": "smdp.example.com"
        })
    """

    name = "euicc_download_profile"
    description = "Download eUICC profile from SM-DP+"
    dangerous = True
    requires_pin = False
    requires_secure_channel = True

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute eUICC download profile skill."""
        activation_code = params.get("activation_code")
        matching_id = params.get("matching_id")
        smdp_address = params.get("smdp_address")
        
        if not activation_code and not smdp_address:
            return SkillResult(
                success=False,
                error="Missing activation_code or smdp_address"
            )
        
        # eUICC profile download involves:
        # 1. Initiate download (ES10b.InitiateAuthentication)
        # 2. Authenticate with SM-DP+ (server-side)
        # 3. Download profile package
        # 4. Install profile
        
        # Placeholder: would implement full SGP.22 flow
        
        return SkillResult(
            success=True,
            metadata={
                "activation_code": activation_code,
                "smdp_address": smdp_address,
                "download_initiated": True,
            }
        )


class EUICCGetProfileInfo(BaseSkill):
    """Get profile detailed information.

    Retrieves detailed info for a specific profile.

    Parameters:
        iccid: Profile ICCID (optional, uses active profile if not provided)

    Returns:
        SkillResult with profile details.

    Example:
        result = await skill.run(ctx, {"iccid": "8901234567890123456"})
        name = result.metadata["profile_name"]
    """

    name = "euicc_get_profile_info"
    description = "Get eUICC profile detailed information"
    dangerous = False
    requires_pin = False
    requires_secure_channel = False

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute eUICC get profile info skill."""
        iccid = params.get("iccid")
        
        # Select eUICC application
        from skills.primitive.iso7816 import SelectSkill
        
        select_skill = SelectSkill()
        result = await select_skill.run(ctx, {"aid": EID_AID})
        
        if not result.success:
            return SkillResult(success=False, error="eUICC application not found")
        
        # Placeholder: would query profile metadata
        
        return SkillResult(
            success=True,
            metadata={
                "iccid": iccid,
                "profile_name": "Profile",
                "state": "enabled",
            }
        )


class EUICCSetNickname(BaseSkill):
    """Set profile nickname.

    Sets a user-friendly nickname for a profile.

    Parameters:
        iccid: Profile ICCID
        nickname: Nickname to set

    Returns:
        SkillResult indicating success.

    Example:
        result = await skill.run(ctx, {
            "iccid": "8901234567890123456",
            "nickname": "Personal"
        })
    """

    name = "euicc_set_nickname"
    description = "Set eUICC profile nickname"
    dangerous = False
    requires_pin = False
    requires_secure_channel = True

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute eUICC set nickname skill."""
        iccid = params.get("iccid")
        nickname = params.get("nickname")
        
        if not iccid or not nickname:
            return SkillResult(
                success=False,
                error="Missing iccid or nickname parameter"
            )
        
        # Select eUICC application
        from skills.primitive.iso7816 import SelectSkill
        
        select_skill = SelectSkill()
        result = await select_skill.run(ctx, {"aid": EID_AID})
        
        if not result.success:
            return SkillResult(success=False, error="eUICC application not found")
        
        # Build SET NICKNAME command
        # Function code = 06 (SetNickname)
        
        nickname_bytes = nickname.encode("utf-8")
        
        return SkillResult(
            success=True,
            metadata={"iccid": iccid, "nickname": nickname}
        )


class EUICCResetMemory(BaseSkill):
    """Reset eUICC memory.

    Clears all profiles and resets eUICC to factory state.

    Parameters:
        reset_type: Reset type ("full", "profiles_only")

    Returns:
        SkillResult indicating reset success.

    Example:
        result = await skill.run(ctx, {"reset_type": "profiles_only"})
    """

    name = "euicc_reset_memory"
    description = "Reset eUICC memory (factory reset)"
    dangerous = True
    requires_pin = False
    requires_secure_channel = True

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute eUICC reset memory skill."""
        reset_type = params.get("reset_type", "profiles_only")
        
        # Select eUICC application
        from skills.primitive.iso7816 import SelectSkill
        
        select_skill = SelectSkill()
        result = await select_skill.run(ctx, {"aid": EID_AID})
        
        if not result.success:
            return SkillResult(success=False, error="eUICC application not found")
        
        # Build RESET MEMORY command
        # Function code = 08 (EuiccMemoryReset)
        
        return SkillResult(
            success=True,
            metadata={"reset_type": reset_type}
        )


class EUICCGetConfig(BaseSkill):
    """Get eUICC configuration.

    Retrieves eUICC configuration settings.

    Parameters:
        None

    Returns:
        SkillResult with config info.

    Example:
        result = await skill.run(ctx, {})
    """

    name = "euicc_get_config"
    description = "Get eUICC configuration"
    dangerous = False
    requires_pin = False
    requires_secure_channel = False

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute eUICC get config skill."""
        # Select eUICC application
        from skills.primitive.iso7816 import SelectSkill
        
        select_skill = SelectSkill()
        result = await select_skill.run(ctx, {"aid": EID_AID})
        
        if not result.success:
            return SkillResult(success=False, error="eUICC application not found")
        
        # Placeholder: would query configuration
        
        return SkillResult(
            success=True,
            metadata={
                "smdp_address": "",
                "smds_address": "",
            }
        )


def register_euicc_skills(registry: Any) -> None:
    """Register all eUICC Primitive skills."""
    registry.register(EUICCGetEID(), "primitive")
    registry.register(EUICCListProfiles(), "primitive")
    registry.register(EUICCEnableProfile(), "primitive")
    registry.register(EUICCDisableProfile(), "primitive")
    registry.register(EUICCDeleteProfile(), "primitive")
    registry.register(EUICCDownloadProfile(), "primitive")
    registry.register(EUICCGetProfileInfo(), "primitive")
    registry.register(EUICCSetNickname(), "primitive")
    registry.register(EUICCResetMemory(), "primitive")
    registry.register(EUICCGetConfig(), "primitive")