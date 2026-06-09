"""APDSL (APDU Scripting Language) Compiler.

This module provides a DSL for defining and executing
predefined APDU sequences.

APDSL Syntax Example:
```
# Read IMSI sequence
sequence read_imsi:
  SELECT 3F00
  SELECT 7F20
  SELECT 6F07
  READ_BINARY 0 9
  PARSE imsi_bcd

# Verify PIN sequence
sequence verify_pin:
  VERIFY PIN1 "1234"
  CHECK SW == 9000
```
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class CommandType(Enum):
    """APDSL command types."""

    SELECT = "SELECT"
    READ_BINARY = "READ_BINARY"
    READ_RECORD = "READ_RECORD"
    VERIFY = "VERIFY"
    GET_RESPONSE = "GET_RESPONSE"
    AUTHENTICATE = "AUTHENTICATE"
    PARSE = "PARSE"
    CHECK = "CHECK"
    WAIT = "WAIT"
    COMMENT = "COMMENT"


@dataclass
class APDSLCommand:
    """Single APDSL command."""

    command_type: CommandType
    params: Dict[str, Any]
    line_number: int
    comment: Optional[str] = None


@dataclass
class APDSLSequence:
    """APDSL sequence definition."""

    name: str
    commands: List[APDSLCommand]
    description: Optional[str] = None
    expected_sw: str = "9000"


class APDSLCompiler:
    """Compiler for APDSL scripts.

    Parses APDSL text and compiles into executable sequences.

    Example:
        compiler = APDSLCompiler()
        sequence = compiler.compile("""
            sequence read_imsi:
              SELECT 3F00
              SELECT 7F20
              SELECT 6F07
              READ_BINARY 0 9
        """)
        apdus = sequence.to_apdus()
    """

    def __init__(self):
        """Initialize compiler."""
        self.sequences: Dict[str, APDSLSequence] = {}

    def compile(self, script: str) -> APDSLSequence:
        """Compile APDSL script into sequence.

        Args:
            script: APDSL script text

        Returns:
            APDSLSequence instance.

        Raises:
            SyntaxError: If script has syntax errors.
        """
        lines = script.strip().split("\n")
        commands: List[APDSLCommand] = []
        sequence_name = "unnamed"
        description = None

        for i, line in enumerate(lines):
            line = line.strip()

            # Skip empty lines
            if not line:
                continue

            # Sequence header
            if line.startswith("sequence"):
                parts = line.split(":")
                sequence_name = parts[0].replace("sequence", "").strip()
                if len(parts) > 1:
                    description = parts[1].strip()
                continue

            # Comment
            if line.startswith("#"):
                continue

            # Parse command
            command = self._parse_command(line, i + 1)
            if command:
                commands.append(command)

        sequence = APDSLSequence(
            name=sequence_name,
            commands=commands,
            description=description,
        )

        self.sequences[sequence_name] = sequence
        return sequence

    def _parse_command(self, line: str, line_number: int) -> Optional[APDSLCommand]:
        """Parse a single command line.

        Args:
            line: Command line text
            line_number: Line number for error reporting

        Returns:
            APDSLCommand or None.
        """
        parts = line.split()

        if not parts:
            return None

        cmd_name = parts[0].upper()

        try:
            cmd_type = CommandType(cmd_name)
        except ValueError:
            raise SyntaxError(f"Unknown command: {cmd_name} at line {line_number}")

        params = {}

        # Parse parameters based on command type
        if cmd_type == CommandType.SELECT:
            params["fid"] = parts[1]

        elif cmd_type == CommandType.READ_BINARY:
            params["offset"] = int(parts[1]) if len(parts) > 1 else 0
            params["length"] = int(parts[2]) if len(parts) > 2 else 0

        elif cmd_type == CommandType.READ_RECORD:
            params["record_number"] = int(parts[1]) if len(parts) > 1 else 1
            params["length"] = int(parts[2]) if len(parts) > 2 else 0

        elif cmd_type == CommandType.VERIFY:
            params["pin_ref"] = parts[1]  # PIN1, PIN2, etc.
            params["pin"] = parts[2] if len(parts) > 2 else ""

        elif cmd_type == CommandType.PARSE:
            params["format"] = parts[1]  # imsi_bcd, iccid_bcd, etc.

        elif cmd_type == CommandType.CHECK:
            params["condition"] = line.replace("CHECK", "").strip()

        elif cmd_type == CommandType.WAIT:
            params["duration"] = float(parts[1]) if len(parts) > 1 else 0.1

        return APDSLCommand(
            command_type=cmd_type,
            params=params,
            line_number=line_number,
        )

    def get_sequence(self, name: str) -> Optional[APDSLSequence]:
        """Get compiled sequence by name.

        Args:
            name: Sequence name

        Returns:
            APDSLSequence or None.
        """
        return self.sequences.get(name)

    def list_sequences(self) -> List[str]:
        """List all compiled sequence names.

        Returns:
            List of sequence names.
        """
        return list(self.sequences.keys())

    def clear(self) -> None:
        """Clear all compiled sequences."""
        self.sequences.clear()


class APDSLExecutor:
    """Executor for APDSL sequences.

    Executes compiled sequences on smart card.

    Example:
        executor = APDSLExecutor(pcsc_client)
        result = executor.execute(sequence)
    """

    def __init__(self, pcsc_client: Any):
        """Initialize executor.

        Args:
            pcsc_client: PCSC client for card communication
        """
        self.pcsc = pcsc_client
        self.execution_log: List[Dict[str, Any]] = []

    async def execute(
        self,
        sequence: APDSLSequence,
        runtime_ctx: Any = None,
    ) -> Dict[str, Any]:
        """Execute an APDSL sequence.

        Args:
            sequence: APDSLSequence to execute
            runtime_ctx: Runtime context for state tracking

        Returns:
            Execution result dictionary.
        """
        results = []
        success = True
        final_data = None

        for command in sequence.commands:
            result = await self._execute_command(command, runtime_ctx)
            results.append(result)

            if not result.get("success"):
                success = False
                break

            if result.get("data"):
                final_data = result["data"]

        self.execution_log = results

        return {
            "sequence_name": sequence.name,
            "success": success,
            "results": results,
            "final_data": final_data,
        }

    async def _execute_command(
        self,
        command: APDSLCommand,
        runtime_ctx: Any = None,
    ) -> Dict[str, Any]:
        """Execute a single APDSL command.

        Args:
            command: APDSLCommand to execute
            runtime_ctx: Runtime context

        Returns:
            Command execution result.
        """
        from apdu.builders.select_builder import build_select_file
        from apdu.builders.read_builder import build_read_binary, build_read_record
        from apdu.builders.auth_builder import build_verify_pin

        result = {
            "command": command.command_type.value,
            "params": command.params,
            "line": command.line_number,
        }

        try:
            apdu = None

            if command.command_type == CommandType.SELECT:
                apdu = build_select_file(command.params["fid"])
                response = self.pcsc.send_apdu(list(apdu), check_sw=False)
                result["sw"] = response.sw
                result["success"] = response.success

                # Update runtime context (connection state only)
                if runtime_ctx and response.success:
                    # File selection is managed by APDU commands
                    pass

            elif command.command_type == CommandType.READ_BINARY:
                apdu = build_read_binary(
                    command.params.get("offset", 0),
                    command.params.get("length", 0),
                )
                response = self.pcsc.send_apdu(list(apdu), check_sw=False)
                result["sw"] = response.sw
                result["data"] = response.data
                result["success"] = response.success

            elif command.command_type == CommandType.READ_RECORD:
                apdu = build_read_record(
                    command.params.get("record_number", 1),
                    length=command.params.get("length", 0),
                )
                response = self.pcsc.send_apdu(list(apdu), check_sw=False)
                result["sw"] = response.sw
                result["data"] = response.data
                result["success"] = response.success

            elif command.command_type == CommandType.VERIFY:
                pin_ref = self._parse_pin_ref(command.params["pin_ref"])
                apdu = build_verify_pin(pin_ref, command.params.get("pin", ""))
                response = self.pcsc.send_apdu(list(apdu), check_sw=False)
                result["sw"] = response.sw
                result["success"] = response.success

            elif command.command_type == CommandType.PARSE:
                # Parse data from previous command
                result["success"] = True
                result["parsed"] = self._parse_data(
                    result.get("data", b""),
                    command.params["format"],
                )

            elif command.command_type == CommandType.CHECK:
                # Check condition (not implemented yet)
                result["success"] = True

            elif command.command_type == CommandType.WAIT:
                import asyncio
                await asyncio.sleep(command.params.get("duration", 0.1))
                result["success"] = True

            if apdu:
                result["apdu"] = apdu.hex().upper()

        except Exception as e:
            result["success"] = False
            result["error"] = str(e)

        return result

    def _parse_pin_ref(self, pin_ref_str: str) -> int:
        """Parse PIN reference string.

        Args:
            pin_ref_str: PIN reference (PIN1, PIN2, etc.)

        Returns:
            PIN reference number.
        """
        if pin_ref_str.startswith("PIN"):
            return int(pin_ref_str.replace("PIN", ""))
        elif pin_ref_str.startswith("ADM"):
            return int(pin_ref_str.replace("ADM", "")) + 9
        else:
            return int(pin_ref_str)

    def _parse_data(self, data: bytes, format_name: str) -> Any:
        """Parse data according to format.

        Args:
            data: Data bytes
            format_name: Format name (imsi_bcd, iccid_bcd, etc.)

        Returns:
            Parsed value.
        """
        if format_name == "imsi_bcd":
            from skills.composite.read_imsi import parse_imsi
            return parse_imsi(data)

        elif format_name == "iccid_bcd":
            from skills.composite.read_iccid import parse_iccid
            return parse_iccid(data)

        elif format_name == "raw":
            return data.hex().upper()

        return data


# Predefined sequences
PREDEFINED_SEQUENCES = {
    "read_imsi": """
sequence read_imsi:
  # Read IMSI from SIM/USIM card
  SELECT 3F00
  SELECT 7F20
  SELECT 6F07
  READ_BINARY 0 9
  PARSE imsi_bcd
""",
    "read_iccid": """
sequence read_iccid:
  # Read ICCID from card
  SELECT 3F00
  SELECT 2FE2
  READ_BINARY 0 10
  PARSE iccid_bcd
""",
    "discover_card": """
sequence discover_card:
  # Basic card discovery
  SELECT 3F00
  READ_BINARY 0 0
  PARSE raw
""",
}


def load_predefined_sequences(compiler: APDSLCompiler) -> None:
    """Load predefined sequences into compiler.

    Args:
        compiler: APDSLCompiler instance
    """
    for name, script in PREDEFINED_SEQUENCES.items():
        compiler.compile(script)