"""FileSystem Primitive Skills - File system navigation and operations.

This module provides skills for navigating and managing the smart card
file system structure (MF, DF, EF) according to ISO7816-4 and ETSI TS 102 221.
"""

from typing import Dict, Any
from skills.base.base_skill import BaseSkill, SkillResult
from apdu.constants.file_ids import FID_MF, FID_DF_GSM, FID_DF_TELECOM


class SelectMF(BaseSkill):
    """Select Master File (MF).

    Navigates to the root of the card file system.
    Equivalent to SELECT 3F00.

    Parameters:
        None

    Returns:
        SkillResult with FCI/FCP of MF.

    Example:
        result = await skill.run(ctx, {})
    """

    name = "select_mf"
    description = "Select Master File (MF) - root of file system"
    dangerous = False
    requires_pin = False
    requires_secure_channel = False

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute select MF skill."""
        from skills.primitive.iso7816 import SelectSkill
        
        select_skill = SelectSkill()
        result = await select_skill.run(ctx, {"fid": FID_MF})
        
        if result.success:
            # Reset selected path to MF
            ctx.runtime_ctx.selected_path = ["3F00"]
            
        return SkillResult(
            success=result.success,
            data=result.data,
            sw=result.sw,
            error=result.error,
            metadata={"path": ctx.runtime_ctx.get_current_path()}
        )


class SelectDF(BaseSkill):
    """Select Dedicated File (DF) by name.

    Selects a DF by its FID or name.
    Common DFs: DF_GSM (7F20), DF_TELECOM (7F10), DF_USIM (7F25).

    Parameters:
        df_fid: DF File ID (e.g., "7F20")
        or
        df_name: DF name ("gsm", "telecom", "usim")

    Returns:
        SkillResult with FCI/FCP of DF.

    Example:
        result = await skill.run(ctx, {"df_name": "gsm"})
        result = await skill.run(ctx, {"df_fid": "7F20"})
    """

    name = "select_df"
    description = "Select Dedicated File (DF) by FID or name"
    dangerous = False
    requires_pin = False
    requires_secure_channel = False

    DF_MAPPING = {
        "gsm": FID_DF_GSM,
        "telecom": FID_DF_TELECOM,
        "usim": "7F25",
        "df_gsm": FID_DF_GSM,
        "df_telecom": FID_DF_TELECOM,
    }

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute select DF skill."""
        from skills.primitive.iso7816 import SelectSkill
        
        df_fid = params.get("df_fid")
        df_name = params.get("df_name")
        
        # Resolve DF name to FID
        if df_name and not df_fid:
            df_fid = self.DF_MAPPING.get(df_name.lower())
            if not df_fid:
                return SkillResult(
                    success=False,
                    error=f"Unknown DF name: {df_name}"
                )
        
        if not df_fid:
            return SkillResult(success=False, error="Missing df_fid or df_name parameter")
        
        select_skill = SelectSkill()
        result = await select_skill.run(ctx, {"fid": df_fid})
        
        return result


class SelectEF(BaseSkill):
    """Select Elementary File (EF) by FID.

    Selects an EF within the current DF.
    Common EFs: EF_IMSI (6F07), EF_ICCID (2FE2), EF_ADN (6F3A).

    Parameters:
        ef_fid: EF File ID (e.g., "6F07")
        or
        ef_name: EF name ("imsi", "iccid", "adn")

    Returns:
        SkillResult with FCI/FCP of EF.

    Example:
        result = await skill.run(ctx, {"ef_name": "imsi"})
    """

    name = "select_ef"
    description = "Select Elementary File (EF) by FID or name"
    dangerous = False
    requires_pin = False
    requires_secure_channel = False

    EF_MAPPING = {
        "imsi": "6F07",
        "iccid": "2FE2",
        "adn": "6F3A",
        "fdn": "6F3B",
        "sms": "6F3C",
        "msisdn": "6F40",
        "spn": "6F46",
        "loci": "6F7E",
        "acci": "6F78",
        "fplmn": "6F7B",
    }

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute select EF skill."""
        from skills.primitive.iso7816 import SelectSkill
        
        ef_fid = params.get("ef_fid")
        ef_name = params.get("ef_name")
        
        if ef_name and not ef_fid:
            ef_fid = self.EF_MAPPING.get(ef_name.lower())
            if not ef_fid:
                return SkillResult(
                    success=False,
                    error=f"Unknown EF name: {ef_name}"
                )
        
        if not ef_fid:
            return SkillResult(success=False, error="Missing ef_fid or ef_name parameter")
        
        select_skill = SelectSkill()
        result = await select_skill.run(ctx, {"fid": ef_fid})
        
        return result


class ResolvePath(BaseSkill):
    """Resolve and navigate to a file path.

    Navigates through multiple DFs/EFs to reach a target file.
    Handles path resolution with both absolute and relative paths.

    Parameters:
        path: File path (e.g., "3F00/7F20/6F07" or "MF/DF_GSM/EF_IMSI")

    Returns:
        SkillResult indicating navigation success.

    Example:
        result = await skill.run(ctx, {"path": "3F00/7F20/6F07"})
    """

    name = "resolve_path"
    description = "Navigate to file by path"
    dangerous = False
    requires_pin = False
    requires_secure_channel = False

    PATH_MAPPING = {
        "MF": "3F00",
        "DF_GSM": "7F20",
        "DF_TELECOM": "7F10",
        "DF_USIM": "7F25",
        "EF_IMSI": "6F07",
        "EF_ICCID": "2FE2",
        "EF_ADN": "6F3A",
    }

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute resolve path skill."""
        from skills.primitive.iso7816 import SelectSkill
        
        path = params.get("path")
        
        if not path:
            return SkillResult(success=False, error="Missing path parameter")
        
        # Parse path components
        components = path.split("/")
        
        # Resolve names to FIDs
        fids = []
        for comp in components:
            fid = self.PATH_MAPPING.get(comp.upper()) or comp
            if not self._validate_fid(fid):
                return SkillResult(
                    success=False,
                    error=f"Invalid FID in path: {comp}"
                )
            fids.append(fid.upper())
        
        # Navigate through path
        select_skill = SelectSkill()
        for fid in fids:
            result = await select_skill.run(ctx, {"fid": fid})
            if not result.success:
                return SkillResult(
                    success=False,
                    error=f"Failed to select {fid}: {result.error}",
                    metadata={"failed_at": fid, "path": path}
                )
        
        return SkillResult(
            success=True,
            metadata={
                "path": path,
                "resolved_path": ctx.runtime_ctx.get_current_path(),
                "fids": fids,
            }
        )

    def _validate_fid(self, fid: str) -> bool:
        """Validate FID format."""
        import re
        return re.match(r"^[0-9A-Fa-f]{4}$", fid) is not None


class ReadTransparentEF(BaseSkill):
    """Read complete transparent EF.

    Reads entire contents of a transparent EF.
    Combines SELECT + READ_BINARY.

    Parameters:
        ef_fid: EF FID (optional if already selected)
        or
        path: Full path to EF

    Returns:
        SkillResult with complete EF data.

    Example:
        result = await skill.run(ctx, {"path": "3F00/2FE2"})  # Read ICCID
    """

    name = "read_transparent_ef"
    description = "Read complete transparent Elementary File"
    dangerous = False
    requires_pin = False
    requires_secure_channel = False

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute read transparent EF skill."""
        from skills.primitive.iso7816 import SelectSkill, ReadBinarySkill
        
        path = params.get("path")
        ef_fid = params.get("ef_fid")
        
        # Navigate to EF if path provided
        if path:
            resolve_skill = ResolvePath()
            result = await resolve_skill.run(ctx, {"path": path})
            if not result.success:
                return result
        elif ef_fid:
            select_skill = SelectSkill()
            result = await select_skill.run(ctx, {"fid": ef_fid})
            if not result.success:
                return result
        
        # Get file size from FCP
        fcp = ctx.runtime_ctx.execution_history[-1].response if ctx.runtime_ctx.execution_history else None
        file_size = 256  # Default max
        
        if fcp:
            from apdu.parsers.fcp_parser import parse_fcp
            fcp_info = parse_fcp(fcp)
            file_size = fcp_info.get("file_size", 256)
        
        # Read binary
        read_skill = ReadBinarySkill()
        result = await read_skill.run(ctx, {"offset": 0, "length": file_size})
        
        return result


class ReadLinearFixedEF(BaseSkill):
    """Read records from linear fixed EF.

    Reads all or specific records from a linear fixed EF.
    Handles record iteration.

    Parameters:
        ef_fid: EF FID (optional if already selected)
        start_record: Starting record number (default: 1)
        count: Number of records to read (0 = all)

    Returns:
        SkillResult with list of records.

    Example:
        result = await skill.run(ctx, {"ef_fid": "6F3A", "count": 5})
    """

    name = "read_linear_fixed_ef"
    description = "Read records from linear fixed Elementary File"
    dangerous = False
    requires_pin = False
    requires_secure_channel = False

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute read linear fixed EF skill."""
        from skills.primitive.iso7816 import SelectSkill, ReadRecordSkill
        
        ef_fid = params.get("ef_fid")
        start_record = params.get("start_record", 1)
        count = params.get("count", 0)  # 0 = read all
        
        # Select EF if needed
        if ef_fid:
            select_skill = SelectSkill()
            result = await select_skill.run(ctx, {"fid": ef_fid})
            if not result.success:
                return result
        
        # Read records
        records = []
        read_skill = ReadRecordSkill()
        
        record_num = start_record
        max_records = count if count > 0 else 100  # Safety limit
        
        for i in range(max_records):
            result = await read_skill.run(ctx, {"record_number": record_num})
            if not result.success:
                if result.sw == "6A83":  # Record not found - end of file
                    break
                return result
            
            records.append({
                "record_number": record_num,
                "data": result.data,
            })
            
            record_num += 1
            
            if count > 0 and i >= count - 1:
                break
        
        return SkillResult(
            success=True,
            metadata={
                "records": records,
                "record_count": len(records),
                "ef_fid": ef_fid,
            }
        )


class DiscoverApplications(BaseSkill):
    """Discover applications on card.

    Scans for applications by probing common AIDs.
    Updates runtime context with discovered applications.

    Parameters:
        probe_common: Probe common AIDs (default: True)
        probe_list: Custom list of AIDs to probe

    Returns:
        SkillResult with list of discovered applications.

    Example:
        result = await skill.run(ctx, {})
        apps = result.metadata["applications"]
    """

    name = "discover_applications"
    description = "Discover applications (AIDs) on card"
    dangerous = False
    requires_pin = False
    requires_secure_channel = False

    COMMON_AIDS = [
        ("USIM", "A0000000871001"),
        ("ISIM", "A0000000871002"),
        ("CSIM", "A0000000871003"),
        ("ARA-C", "A0000001510000"),
        ("GP-ISD", "A0000001510000"),
        ("SIM", "A0000000010001"),
    ]

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute discover applications skill."""
        from skills.primitive.iso7816 import SelectSkill
        
        probe_common = params.get("probe_common", True)
        probe_list = params.get("probe_list", [])
        
        aids_to_probe = []
        
        if probe_common:
            aids_to_probe.extend(self.COMMON_AIDS)
        
        for aid in probe_list:
            aids_to_probe.append(("Custom", aid))
        
        discovered_apps = []
        select_skill = SelectSkill()
        
        for app_name, aid in aids_to_probe:
            result = await select_skill.run(ctx, {"aid": aid})
            if result.success:
                discovered_apps.append({
                    "name": app_name,
                    "aid": aid,
                    "fcp": result.metadata.get("fcp", {}),
                })
                ctx.runtime_ctx.add_discovered_app(aid)
        
        return SkillResult(
            success=True,
            metadata={
                "applications": discovered_apps,
                "count": len(discovered_apps),
            }
        )


def register_filesystem_skills(registry: Any) -> None:
    """Register all FileSystem Primitive skills."""
    registry.register(SelectMF(), "primitive")
    registry.register(SelectDF(), "primitive")
    registry.register(SelectEF(), "primitive")
    registry.register(ResolvePath(), "primitive")
    registry.register(ReadTransparentEF(), "primitive")
    registry.register(ReadLinearFixedEF(), "primitive")
    registry.register(DiscoverApplications(), "primitive")