"""JavaCard Primitive Skills - JavaCard applet operations.

JavaCard is a Java platform for smart cards, allowing applets
to run on card in a secure, sandboxed environment.

Reference: JavaCard Specification v3.1
"""

from typing import Dict, Any
from skills.base.base_skill import BaseSkill, SkillResult


class JCInstallApplet(BaseSkill):
    """Install JavaCard applet.

    Installs a JavaCard applet using GlobalPlatform INSTALL command.

    Parameters:
        cap_file: CAP file data (compiled applet)
        applet_aid: Applet AID
        package_aid: Package AID
        install_params: Installation parameters (optional)

    Returns:
        SkillResult indicating installation success.

    Example:
        result = await skill.run(ctx, {
            "package_aid": "A0000000010002",
            "applet_aid": "A0000000010001",
            "cap_file": cap_data
        })
    """

    name = "jc_install_applet"
    description = "Install JavaCard applet"
    dangerous = True
    requires_pin = False
    requires_secure_channel = True

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute JC install applet skill."""
        package_aid = params.get("package_aid")
        applet_aid = params.get("applet_aid")
        cap_file = params.get("cap_file")
        
        if not package_aid or not applet_aid:
            return SkillResult(
                success=False,
                error="Missing package_aid or applet_aid"
            )
        
        # JavaCard installation requires:
        # 1. LOAD the CAP file (package)
        # 2. INSTALL the applet
        
        from skills.globalplatform import GPLoad, GPInstall
        
        # Step 1: Load CAP file
        if cap_file:
            load_skill = GPLoad()
            load_result = await load_skill.run(ctx, {
                "executable_aid": package_aid,
                "load_file_data": cap_file,
            })
            
            if not load_result.success:
                return SkillResult(
                    success=False,
                    error=f"Failed to load CAP file: {load_result.error}"
                )
        
        # Step 2: Install applet
        install_skill = GPInstall()
        install_result = await install_skill.run(ctx, {
            "aid": applet_aid,
            "executable_aid": package_aid,
        })
        
        if install_result.success:
            ctx.runtime_ctx.add_discovered_app(applet_aid)
        
        return install_result


class JCDeleteApplet(BaseSkill):
    """Delete JavaCard applet.

    Deletes an installed applet and optionally its package.

    Parameters:
        applet_aid: Applet AID to delete
        delete_package: Also delete package (default: False)

    Returns:
        SkillResult indicating deletion success.

    Example:
        result = await skill.run(ctx, {
            "applet_aid": "A0000000010001",
            "delete_package": True
        })
    """

    name = "jc_delete_applet"
    description = "Delete JavaCard applet"
    dangerous = True
    requires_pin = False
    requires_secure_channel = True

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute JC delete applet skill."""
        applet_aid = params.get("applet_aid")
        delete_package = params.get("delete_package", False)
        
        if not applet_aid:
            return SkillResult(success=False, error="Missing applet_aid")
        
        from skills.globalplatform import GPDelete
        
        # Delete applet
        delete_skill = GPDelete()
        result = await delete_skill.run(ctx, {"aid": applet_aid})
        
        if result.success:
            # Remove from discovered apps
            ctx.runtime_ctx.remove_discovered_app(applet_aid)
            
            # Optionally delete package
            if delete_package:
                # Package AID is typically applet_aid with one byte removed
                package_aid = applet_aid[:len(applet_aid) - 2]
                await delete_skill.run(ctx, {"aid": package_aid})
        
        return result


class JCSelectApplet(BaseSkill):
    """Select JavaCard applet.

    Selects an installed applet for subsequent operations.

    Parameters:
        applet_aid: Applet AID to select

    Returns:
        SkillResult with applet FCI.

    Example:
        result = await skill.run(ctx, {"applet_aid": "A0000000010001"})
    """

    name = "jc_select_applet"
    description = "Select JavaCard applet"
    dangerous = False
    requires_pin = False
    requires_secure_channel = False

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute JC select applet skill."""
        applet_aid = params.get("applet_aid")
        
        if not applet_aid:
            return SkillResult(success=False, error="Missing applet_aid")
        
        from skills.primitive.iso7816 import SelectSkill
        
        select_skill = SelectSkill()
        result = await select_skill.run(ctx, {"aid": applet_aid})
        
        if result.success:
            ctx.runtime_ctx.current_application = applet_aid
        
        return result


class JCSendAPDU(BaseSkill):
    """Send APDU to selected applet.

    Sends command APDU to the currently selected applet.

    Parameters:
        apdu: Command APDU bytes

    Returns:
        SkillResult with applet response.

    Example:
        result = await skill.run(ctx, {"apdu": "00A0000000"})
    """

    name = "jc_send_apdu"
    description = "Send APDU to JavaCard applet"
    dangerous = False
    requires_pin = False
    requires_secure_channel = False

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute JC send APDU skill."""
        apdu = params.get("apdu")
        
        if not apdu:
            return SkillResult(success=False, error="Missing apdu parameter")
        
        from skills.primitive.iso7816 import SendAPDUSkill
        
        send_skill = SendAPDUSkill()
        return await send_skill.run(ctx, {"apdu": apdu})


class JCGetAppletInfo(BaseSkill):
    """Get JavaCard applet information.

    Queries applet metadata and capabilities.

    Parameters:
        applet_aid: Applet AID (optional if already selected)

    Returns:
        SkillResult with applet info.

    Example:
        result = await skill.run(ctx, {})
        version = result.metadata["version"]
    """

    name = "jc_get_applet_info"
    description = "Get JavaCard applet information"
    dangerous = False
    requires_pin = False
    requires_secure_channel = False

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute JC get applet info skill."""
        applet_aid = params.get("applet_aid") or ctx.runtime_ctx.current_application
        
        if not applet_aid:
            return SkillResult(success=False, error="No applet selected")
        
        # Select applet if needed
        if ctx.runtime_ctx.current_application != applet_aid:
            from skills.javacard import JCSelectApplet
            
            select_skill = JCSelectApplet()
            result = await select_skill.run(ctx, {"applet_aid": applet_aid})
            
            if not result.success:
                return result
        
        # Query applet info via GET DATA or proprietary commands
        # Placeholder: would send applet-specific query commands
        
        return SkillResult(
            success=True,
            metadata={
                "aid": applet_aid,
                "selected": True,
            }
        )


def register_javacard_skills(registry: Any) -> None:
    """Register all JavaCard Primitive skills."""
    registry.register(JCInstallApplet(), "primitive")
    registry.register(JCDeleteApplet(), "primitive")
    registry.register(JCSelectApplet(), "primitive")
    registry.register(JCSendAPDU(), "primitive")
    registry.register(JCGetAppletInfo(), "primitive")