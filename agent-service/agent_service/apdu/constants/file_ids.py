"""File IDs (FID) for smart card file system.

This module defines common File IDs used in SIM/USIM/eUICC cards
according to ISO 7816, ETSI TS 102 221, and 3GPP TS 31.102.
"""

# Master File (MF)
FID_MF = "3F00"

# Dedicated Files (DF)
FID_DF_GSM = "7F20"  # GSM DF (USIM)
FID_DF_TELECOM = "7F10"  # Telecom DF
FID_DF_GRAPHICS = "7F21"  # Graphics DF
FID_DF_PHONEBOOK = "7F22"  # Phonebook DF
FID_DF_MULTIMEDIA = "7F23"  # Multimedia DF
FID_DF_WLAN = "7F24"  # WLAN DF
FID_DF_USIM = "7F25"  # USIM Application DF

# Elementary Files (EF) under MF
FID_EF_ICCID = "2FE2"  # ICCID (Integrated Circuit Card ID)
FID_EF_DIR = "2F00"  # EF DIR (Application Directory)
FID_EF_PL = "2F05"  # Preferred Languages
FID_EF_ARR = "2F06"  # Access Rule Reference

# Elementary Files (EF) under DF_GSM/DF_USIM
FID_EF_IMSI = "6F07"  # IMSI (International Mobile Subscriber Identity)
FID_EF_KC = "6F20"  # KC (Ciphering Key)
FID_EF_KCGPRS = "6F22"  # KC GPRS
FID_EF_LOCIGPRS = "6F23"  # Location Information GPRS
FID_EF_AD = "6FAD"  # Administrative Data
FID_EF_PHASE = "6FAE"  # Phase Identification
FID_EF_SPN = "6F46"  # Service Provider Name
FID_EF_PNN = "6F45"  # Network Name
FID_EF_OPL = "6F47"  # Operator PLMN List
FID_EF_MBI = "6FC9"  # Mailbox Identifier
FID_EF_MBDN = "6FC7"  # Mailbox Dialing Number
FID_EF_MWIS = "6FCA"  # Messaging Waiting Indication Status

# Elementary Files (EF) - USIM specific
FID_EF_PUCT = "6F41"  # Price per Unit and Currency Table
FID_EF_CFPLMN = "6F30"  # Call Forwarding PLMN
FID_EF_ADN = "6F3A"  # Abbreviated Dialing Numbers
FID_EF_FDN = "6F3B"  # Fixed Dialing Numbers
FID_EF_SMS = "6F3C"  # Short Messages
FID_EF_GID1 = "6F3E"  # Group Identifier Level 1
FID_EF_GID2 = "6F3F"  # Group Identifier Level 2
FID_EF_MSISDN = "6F40"  # MSISDN (Mobile Station ISDN Number)
FID_EF_SMSP = "6F42"  # Short Message Service Parameters
FID_EF_SMSS = "6F43"  # Short Message Service Status
FID_EF_LI = "6F05"  # Language Indication
FID_EF_ACC = "6F78"  # Access Control Class
FID_EF_FPLMN = "6F7B"  # Forbidden PLMN List
FID_EF_LOCI = "6F7E"  # Location Information
FID_EF_AD = "6FAD"  # Administrative Data
FID_EF_CMI = "6FB7"  # Card Management Info

# Elementary Files (EF) - eUICC specific
FID_EF_EUICC_INFO1 = "2F22"
FID_EF_EUICC_INFO2 = "2F23"
FID_EF_EUICC_PROFILE_INFO = "2F24"
FID_EUICC_CONFIGURED_NAA = "2F25"


# Application IDs (AID)
AID_USIM = "A0000000871001"  # USIM Application
AID_ISIM = "A0000000871002"  # ISIM Application
AID_CSIM = "A0000000871003"  # CSIM Application
AID_ARA_C = "A0000001510000"  # ARA-C (Access Rule Applet)
AID_GLOBALPLATFORM = "A0000001510000"  # GlobalPlatform Card Manager
AID_JAVACARD = "A0000000620001"  # JavaCard


# File types
FILE_TYPE_MF = "01"  # Master File
FILE_TYPE_DF = "02"  # Dedicated File
FILE_TYPE_EF_TRANSPARENT = "04"  # Transparent EF
FILE_TYPE_EF_LINEAR_FIXED = "06"  # Linear Fixed EF
FILE_TYPE_EF_CYCLIC = "08"  # Cyclic EF


# File descriptors
FILE_DESCRIPTOR_TRANSPARENT = "00"
FILE_DESCRIPTOR_LINEAR_FIXED = "01"
FILE_DESCRIPTOR_CYCLIC = "03"