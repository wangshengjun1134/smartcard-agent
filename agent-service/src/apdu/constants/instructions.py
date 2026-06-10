"""APDU instruction codes (INS) for ISO 7816.

This module defines APDU instruction codes used in smart card commands.
"""

# ISO 7816-4 Instructions
INS_SELECT = 0xA4
INS_READ_BINARY = 0xB0
INS_READ_RECORD = 0xB2
INS_WRITE_BINARY = 0xD0
INS_WRITE_RECORD = 0xD2
INS_UPDATE_BINARY = 0xD6
INS_UPDATE_RECORD = 0xDC
INS_APPEND_RECORD = 0xE2
INS_DELETE_FILE = 0xE4
INS_VERIFY = 0x20
INS_CHANGE = 0x24
INS_UNBLOCK = 0x2C
INS_GET_RESPONSE = 0xC0
INS_GET_CHALLENGE = 0x84
INS_MANAGE_CHANNEL = 0x70
INS_EXTERNAL_AUTHENTICATE = 0x82
INS_INTERNAL_AUTHENTICATE = 0x88
INS_ENVELOPE = 0xC2

# GSM/USIM Instructions (ETSI TS 102 221)
INS_RUN_GSM_ALGORITHM = 0x88
INS_USIM_AUTHENTICATE = 0x88
INS_TERMINAL_PROFILE = 0x10
INS_ENVELOPE = 0xC2
INS_FETCH = 0x12
INS_TERMINAL_RESPONSE = 0x14

# GlobalPlatform Instructions
INS_INITIALIZE_UPDATE = 0x50
INS_EXTERNAL_AUTHENTICATE_GP = 0x82
INS_DELETE_FILE_GP = 0xE4
INS_GET_STATUS = 0xF2
INS_INSTALL = 0xE6
INS_LOAD = 0xE8
INS_PUT_KEY = 0xD8

# Class bytes (CLA)
CLA_ISO7816 = 0x00
CLA_GSM = 0xA0
CLA_USIM = 0x00  # USIM uses standard CLA with secure messaging
CLA_GLOBALPLATFORM = 0x80
CLA_SECURE_MESSAGING = 0x0C

# Select modes (P1)
SELECT_MODE_BY_FID = 0x00  # Select by File ID
SELECT_MODE_BY_DF_NAME = 0x04  # Select by DF name (AID)
SELECT_MODE_FROM_MF = 0x00  # From MF
SELECT_MODE_FROM_CURRENT_DF = 0x03  # From current DF
SELECT_MODE_PARENT_DF = 0x03  # Parent DF

# Select types (P2)
SELECT_TYPE_NO_DATA = 0x00  # No FCI returned
SELECT_TYPE_FCI = 0x04  # Return FCI template
SELECT_TYPE_FCP = 0x04  # Return FCP template
SELECT_TYPE_FMD = 0x08  # Return FMD template

# Read options (P1)
READ_BINARY_P1_CURRENT_EF = 0x00
READ_BINARY_P1_SHORT_EF = 0x80  # Short EF identifier in P1

# Record read modes (P1)
READ_RECORD_P1_FIRST = 0x00
READ_RECORD_P1_LAST = 0x01
READ_RECORD_P1_NEXT = 0x02
READ_RECORD_P1_PREVIOUS = 0x03
READ_RECORD_P1_ABSOLUTE = 0x04


# PIN reference numbers
PIN_REF_PIN1 = 0x01  # PIN 1 (Universal PIN)
PIN_REF_PIN2 = 0x02  # PIN 2 (CHV1)
PIN_REF_PUK1 = 0x05  # PUK1 (Unblock PIN1)
PIN_REF_PUK2 = 0x06  # PUK2 (Unblock PIN2)
PIN_REF_ADM1 = 0x0A  # Administrative PIN


def build_cla(cla: int, secure_messaging: bool = False) -> int:
    """Build CLA byte with optional secure messaging.

    Args:
        cla: Base CLA byte
        secure_messaging: Whether to add secure messaging indicator

    Returns:
        Complete CLA byte.
    """
    if secure_messaging:
        return cla | 0x0C
    return cla