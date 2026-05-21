"""Verify PIN Skill - verify a PIN on the smart card.

This skill verifies a PIN (CHV) on the smart card.
"""

from typing import Dict, Any
from skills.base.base_skill import BaseSkill, SkillResult
from apdu.builders.auth_builder import build_verify_pin
from apdu.constants.instructions import PIN_REF_PIN1, PIN_REF_PIN2


class VerifyPinSkill(BaseSkill):
    """Skill for verifying a PIN.

    Parameters:
        pin: PIN value as string (4-8 digits)
        pin_ref: PIN reference number (default: 1 for PIN1)

    Updates runtime context:
        - pin_verified: Sets the PIN as verified

    Example:
        await skill.run(ctx, {"pin": "1234", "pin_ref": 1})
    """

    name = "verify_pin"
    description = "Verify a PIN on the smart card"
    dangerous = False
    requires_pin = False  # This skill verifies PIN, doesn't require it
    requires_secure_channel = False

    async def run(self, ctx: Any, params: Dict[str, Any]) -> SkillResult:
        """Execute VERIFY PIN skill.

        Args:
            ctx: Skill execution context
            params: {"pin": "1234", "pin_ref": 1}

        Returns:
            SkillResult with verification status.
        """
        pin = params.get("pin", "")
        pin_ref = params.get("pin_ref", PIN_REF_PIN1)

        # Validate PIN format
        import re
        if pin and not re.match(r"^[0-9]{4,8}$", pin):
            return SkillResult(success=False, error=f"Invalid PIN format: must be 4-8 digits")

        try:
            # Build VERIFY PIN APDU
            apdu = build_verify_pin(pin_ref, pin)
            apdu_bytes = bytes(apdu)

            # Send APDU
            response = ctx.pcsc.send_apdu(list(apdu), check_sw=False)

            # Record execution
            ctx.runtime_ctx.record_execution(
                skill_name=self.name,
                params={"pin_ref": pin_ref},  # Don't record actual PIN
                apdu=apdu_bytes,
                response=response.data,
                sw=response.sw,
                success=response.success,
            )

            if response.success:
                # Update runtime context - PIN is now verified
                ctx.runtime_ctx.verify_pin(pin_ref)

                return SkillResult(
                    success=True,
                    sw=response.sw,
                    metadata={"pin_ref": pin_ref, "verified": True}
                )
            else:
                # Check for retry count
                from apdu.parsers.sw_parser import get_retry_count
                retry_count = get_retry_count(response.sw)

                from apdu.constants.sw_codes import decode_sw
                return SkillResult(
                    success=False,
                    sw=response.sw,
                    error=decode_sw(response.sw),
                    metadata={"pin_ref": pin_ref, "retry_count": retry_count}
                )

        except Exception as e:
            return SkillResult(success=False, error=str(e))

    def validate_params(self, params: Dict[str, Any]) -> tuple[bool, str]:
        """Validate PIN parameter.

        Args:
            params: Parameters

        Returns:
            Tuple of (valid, error).
        """
        pin = params.get("pin", "")
        pin_ref = params.get("pin_ref", PIN_REF_PIN1)

        import re
        if pin and not re.match(r"^[0-9]{4,8}$", pin):
            return False, "PIN must be 4-8 digits"

        if not isinstance(pin_ref, int) or pin_ref < 1 or pin_ref > 10:
            return False, f"Invalid pin_ref: {pin_ref}"

        return True, ""