"""GlobalPlatform Primitive Skills - GP card management operations.

GlobalPlatform (GP) is the standard for secure application management
on smart cards, defining commands for installing, loading, deleting,
and managing applets and applications.

Reference: GlobalPlatform Card Specification v2.3
"""

from typing import Dict, Any
from skills.base.base_skill import BaseSkill, SkillResult


class GPSelectISD(BaseSkill):
    """Select Issuer Security Domain (ISD).

    The ISD is the root security domain on GP-compliant cards.

    Parameters:
        None (uses standard ISD AID: A0000001510000)

    Returns:
        SkillResult with ISD FCI.

    Example:
        result = await skill.run(ctx, {})
    """

    name = "gp_select_isd"
    description = "Select Issuer Security Domain (ISD)"
    dangerous = False
    requires_pin = False
    requires_secure_channel = False

    ISD_AID = "A0000001510000"

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute GP select ISD skill."""
        from skills.primitive.iso7816 import SelectSkill
        
        select_skill = SelectSkill()
        result = await select_skill.run(ctx, {"aid": self.ISD_AID})
        
        if result.success:
            ctx.runtime_ctx.current_application = self.ISD_AID
            ctx.runtime_ctx.add_capability("isd_selected")
        
        return result


class GPGetStatus(BaseSkill):
    """GP GET STATUS command.

    Retrieves status information about applications, applets,
    or security domains on the card.

    Parameters:
        status_type: Type of status query
            - 0x80: Applications
            - 0x40: Executable Load Files
            - 0x20: Security Domains
        aid_filter: Optional AID filter pattern

    Returns:
        SkillResult with status data.

    Example:
        result = await skill.run(ctx, {"status_type": 0x80})
        apps = result.metadata["applications"]
    """

    name = "gp_get_status"
    description = "GP GET STATUS - list applications"
    dangerous = False
    requires_pin = False
    requires_secure_channel = True

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute GP GET STATUS skill."""
        status_type = params.get("status_type", 0x80)
        aid_filter = params.get("aid_filter", "")
        
        # Build GET STATUS APDU
        # CLA = 0x80 or 0x84 (secure messaging)
        # INS = 0xF2
        # P1 = status_type | 0x01 (next)
        # P2 = 0x00 (get all) or 0x02 (filter)
        
        aid_bytes = bytes.fromhex(aid_filter) if aid_filter else bytes()
        
        apdu = bytes([0x80, 0xF2, status_type | 0x01, 0x00, len(aid_bytes)]) + aid_bytes + bytes([0x00])
        
        response = ctx.pcsc.send_apdu(list(apdu), check_sw=False)
        
        ctx.runtime_ctx.record_execution(
            skill_name=self.name,
            params={"status_type": status_type},
            apdu=apdu,
            response=response.data,
            sw=response.sw,
            success=response.success,
        )
        
        if response.success:
            # Parse status data
            applications = self._parse_status_data(response.data)
            
            return SkillResult(
                success=True,
                data=response.data,
                sw=response.sw,
                metadata={
                    "applications": applications,
                    "status_type": status_type,
                }
            )
        else:
            from apdu.constants.sw_codes import decode_sw
            return SkillResult(
                success=False,
                sw=response.sw,
                error=decode_sw(response.sw),
            )

    def _parse_status_data(self, data: bytes) -> list:
        """Parse GET STATUS response data."""
        applications = []
        
        # Status data format:
        # TLV structure with application AIDs and life cycle states
        
        from apdu.parsers.tlv_parser import parse_tlv
        
        if data:
            tlv = parse_tlv(data)
            # Would parse actual TLV structure
            # Placeholder: return empty list
            
        return applications


class GPInstall(BaseSkill):
    """GP INSTALL command.

    Installs an applet or application on the card.

    Parameters:
        aid: AID of applet to install
        executable_aid: AID of executable load file
        install_parameters: Installation parameters (optional)
        privileges: Privileges to assign (optional)

    Returns:
        SkillResult indicating installation success.

    Example:
        result = await skill.run(ctx, {
            "aid": "A0000000010001",
            "executable_aid": "A0000000010002"
        })
    """

    name = "gp_install"
    description = "GP INSTALL - install applet"
    dangerous = True
    requires_pin = False
    requires_secure_channel = True

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute GP INSTALL skill."""
        aid = params.get("aid")
        executable_aid = params.get("executable_aid")
        
        if not aid or not executable_aid:
            return SkillResult(
                success=False,
                error="Missing aid or executable_aid parameter"
            )
        
        aid_bytes = bytes.fromhex(aid)
        exec_aid_bytes = bytes.fromhex(executable_aid)
        
        # Build INSTALL APDU
        # INSTALL [for install] = 0x01
        # INSTALL [for load] = 0x02
        # INSTALL [for make selectable] = 0x04
        # INSTALL [for extradition] = 0x08
        
        # Simplified INSTALL for install
        install_data = bytes([0x01]) + bytes([len(exec_aid_bytes)]) + exec_aid_bytes + bytes([len(aid_bytes)]) + aid_bytes
        
        apdu = bytes([0x80, 0xE6, 0x01, 0x00, len(install_data)]) + install_data
        
        response = ctx.pcsc.send_apdu(list(apdu), check_sw=False)
        
        ctx.runtime_ctx.record_execution(
            skill_name=self.name,
            params={"aid": aid},
            apdu=apdu,
            response=response.data,
            sw=response.sw,
            success=response.success,
        )
        
        if response.success:
            return SkillResult(
                success=True,
                sw=response.sw,
                metadata={"installed_aid": aid}
            )
        else:
            from apdu.constants.sw_codes import decode_sw
            return SkillResult(
                success=False,
                sw=response.sw,
                error=decode_sw(response.sw),
            )


class GPLoad(BaseSkill):
    """GP LOAD command.

    Loads an executable load file (applet code) onto the card.

    Parameters:
        executable_aid: AID of executable load file
        load_file_data: Load file content (CAP file data)
        block_number: Block number for segmented load

    Returns:
        SkillResult indicating load success.

    Example:
        result = await skill.run(ctx, {
            "executable_aid": "A0000000010002",
            "load_file_data": cap_file_bytes
        })
    """

    name = "gp_load"
    description = "GP LOAD - load executable file"
    dangerous = True
    requires_pin = False
    requires_secure_channel = True

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute GP LOAD skill."""
        executable_aid = params.get("executable_aid")
        load_file_data = params.get("load_file_data")
        block_number = params.get("block_number", 0x00)
        
        if not executable_aid:
            return SkillResult(success=False, error="Missing executable_aid")
        
        if not load_file_data:
            return SkillResult(success=False, error="Missing load_file_data")
        
        if isinstance(load_file_data, str):
            load_data_bytes = bytes.fromhex(load_file_data)
        else:
            load_data_bytes = bytes(load_file_data)
        
        # Build LOAD APDU
        exec_aid_bytes = bytes.fromhex(executable_aid)
        
        # Load header: AID length + AID + block number + data
        load_data = bytes([len(exec_aid_bytes)]) + exec_aid_bytes + bytes([block_number]) + load_data_bytes
        
        apdu = bytes([0x80, 0xE8, block_number, 0x00, len(load_data)]) + load_data
        
        response = ctx.pcsc.send_apdu(list(apdu), check_sw=False)
        
        ctx.runtime_ctx.record_execution(
            skill_name=self.name,
            params={"executable_aid": executable_aid},
            apdu=apdu,
            response=response.data,
            sw=response.sw,
            success=response.success,
        )
        
        if response.success:
            return SkillResult(
                success=True,
                sw=response.sw,
                metadata={"loaded_aid": executable_aid}
            )
        else:
            from apdu.constants.sw_codes import decode_sw
            return SkillResult(
                success=False,
                sw=response.sw,
                error=decode_sw(response.sw),
            )


class GPDelete(BaseSkill):
    """GP DELETE command.

    Deletes an application, applet, or load file from the card.

    Parameters:
        aid: AID of object to delete
        delete_type: Type of object (applet, load file, package)

    Returns:
        SkillResult indicating deletion success.

    Example:
        result = await skill.run(ctx, {"aid": "A0000000010001"})
    """

    name = "gp_delete"
    description = "GP DELETE - delete application"
    dangerous = True
    requires_pin = False
    requires_secure_channel = True

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute GP DELETE skill."""
        aid = params.get("aid")
        
        if not aid:
            return SkillResult(success=False, error="Missing aid parameter")
        
        aid_bytes = bytes.fromhex(aid)
        
        # Build DELETE APDU
        # P1 = 0x00 (delete object)
        # P2 = 0x00 (single object)
        
        delete_data = bytes([0x4F, len(aid_bytes)]) + aid_bytes  # AID TLV
        
        apdu = bytes([0x80, 0xE4, 0x00, 0x00, len(delete_data)]) + delete_data
        
        response = ctx.pcsc.send_apdu(list(apdu), check_sw=False)
        
        ctx.runtime_ctx.record_execution(
            skill_name=self.name,
            params={"aid": aid},
            apdu=apdu,
            response=response.data,
            sw=response.sw,
            success=response.success,
        )
        
        if response.success:
            return SkillResult(
                success=True,
                sw=response.sw,
                metadata={"deleted_aid": aid}
            )
        else:
            from apdu.constants.sw_codes import decode_sw
            return SkillResult(
                success=False,
                sw=response.sw,
                error=decode_sw(response.sw),
            )


class GPPutKey(BaseSkill):
    """GP PUT KEY command.

    Replaces or adds keys in the card's key store.

    Parameters:
        key_set: Key set identifier (KID)
        key_version: Key version (KV)
        key_type: Key type (DES, AES)
        key_data: Key data bytes

    Returns:
        SkillResult indicating key replacement success.

    Example:
        result = await skill.run(ctx, {
            "key_set": 0x01,
            "key_version": 0x01,
            "key_data": encrypted_key_bytes
        })
    """

    name = "gp_put_key"
    description = "GP PUT KEY - replace/add keys"
    dangerous = True
    requires_pin = False
    requires_secure_channel = True

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute GP PUT KEY skill."""
        key_set = params.get("key_set", 0x01)
        key_version = params.get("key_version", 0x01)
        key_data = params.get("key_data")
        
        if not key_data:
            return SkillResult(success=False, error="Missing key_data parameter")
        
        # Build PUT KEY APDU
        # Key header: KID | KV | key type
        
        key_header = bytes([key_set, key_version])
        
        if isinstance(key_data, str):
            key_data_bytes = bytes.fromhex(key_data)
        else:
            key_data_bytes = bytes(key_data)
        
        put_data = key_header + key_data_bytes
        
        apdu = bytes([0x80, 0xD8, key_set, 0x81, len(put_data)]) + put_data
        
        response = ctx.pcsc.send_apdu(list(apdu), check_sw=False)
        
        ctx.runtime_ctx.record_execution(
            skill_name=self.name,
            params={"key_set": key_set},
            apdu=apdu,
            response=response.data,
            sw=response.sw,
            success=response.success,
        )
        
        if response.success:
            return SkillResult(
                success=True,
                sw=response.sw,
                metadata={"key_set": key_set, "key_version": key_version}
            )
        else:
            from apdu.constants.sw_codes import decode_sw
            return SkillResult(
                success=False,
                sw=response.sw,
                error=decode_sw(response.sw),
            )


class GPStoreData(BaseSkill):
    """GP STORE DATA command.

    Stores data in the card's secure storage.

    Parameters:
        data: Data to store
        tag: Optional TLV tag

    Returns:
        SkillResult indicating storage success.

    Example:
        result = await skill.run(ctx, {"data": "00010203"})
    """

    name = "gp_store_data"
    description = "GP STORE DATA - store data securely"
    dangerous = False
    requires_pin = False
    requires_secure_channel = True

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute GP STORE DATA skill."""
        data = params.get("data")
        
        if not data:
            return SkillResult(success=False, error="Missing data parameter")
        
        if isinstance(data, str):
            data_bytes = bytes.fromhex(data)
        else:
            data_bytes = bytes(data)
        
        # Build STORE DATA APDU
        apdu = bytes([0x80, 0xE2, 0x80, 0x00, len(data_bytes)]) + data_bytes
        
        response = ctx.pcsc.send_apdu(list(apdu), check_sw=False)
        
        ctx.runtime_ctx.record_execution(
            skill_name=self.name,
            params={},
            apdu=apdu,
            response=response.data,
            sw=response.sw,
            success=response.success,
        )
        
        if response.success:
            return SkillResult(success=True, sw=response.sw)
        else:
            from apdu.constants.sw_codes import decode_sw
            return SkillResult(
                success=False,
                sw=response.sw,
                error=decode_sw(response.sw),
            )


class GPSetStatus(BaseSkill):
    """GP SET STATUS command.

    Changes the life cycle status of an application.

    Parameters:
        aid: AID of application
        status: New status (0x07=installed, 0x0F=selectable)

    Returns:
        SkillResult indicating status change success.

    Example:
        result = await skill.run(ctx, {
            "aid": "A0000000010001",
            "status": 0x0F
        })
    """

    name = "gp_set_status"
    description = "GP SET STATUS - change application status"
    dangerous = True
    requires_pin = False
    requires_secure_channel = True

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute GP SET STATUS skill."""
        aid = params.get("aid")
        status = params.get("status", 0x0F)
        
        if not aid:
            return SkillResult(success=False, error="Missing aid parameter")
        
        aid_bytes = bytes.fromhex(aid)
        
        # Build SET STATUS APDU
        status_data = bytes([0x4F, len(aid_bytes)]) + aid_bytes + bytes([status])
        
        apdu = bytes([0x80, 0xF0, 0x80, 0x00, len(status_data)]) + status_data
        
        response = ctx.pcsc.send_apdu(list(apdu), check_sw=False)
        
        if response.success:
            return SkillResult(
                success=True,
                sw=response.sw,
                metadata={"aid": aid, "new_status": status}
            )
        else:
            from apdu.constants.sw_codes import decode_sw
            return SkillResult(
                success=False,
                sw=response.sw,
                error=decode_sw(response.sw),
            )


def register_globalplatform_skills(registry: Any) -> None:
    """Register all GlobalPlatform Primitive skills."""
    registry.register(GPSelectISD(), "primitive")
    registry.register(GPGetStatus(), "primitive")
    registry.register(GPInstall(), "primitive")
    registry.register(GPLoad(), "primitive")
    registry.register(GPDelete(), "primitive")
    registry.register(GPPutKey(), "primitive")
    registry.register(GPStoreData(), "primitive")
    registry.register(GPSetStatus(), "primitive")