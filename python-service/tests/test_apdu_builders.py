"""Tests for APDU builders."""

import pytest
from apdu.builders.select_builder import build_select_file, build_select_by_aid
from apdu.builders.read_builder import build_read_binary, build_read_record
from apdu.builders.auth_builder import build_verify_pin, build_get_challenge


class TestSelectBuilder:
    """Tests for SELECT APDU builder."""

    def test_build_select_file_mf(self):
        """Test SELECT MF (3F00)."""
        apdu = build_select_file("3F00")
        assert apdu == bytes.fromhex("00A40000023F00")

    def test_build_select_file_ef(self):
        """Test SELECT EF (6F07)."""
        apdu = build_select_file("6F07")
        assert apdu == bytes.fromhex("00A40000026F07")

    def test_build_select_by_aid(self):
        """Test SELECT by AID."""
        aid = "A0000000871001"  # USIM AID
        apdu = build_select_by_aid(aid)
        assert apdu == bytes.fromhex("00A4040007A0000000871001")

    def test_build_select_file_lowercase(self):
        """Test SELECT with lowercase FID."""
        apdu = build_select_file("3f00")
        assert apdu == bytes.fromhex("00A40000023f00")


class TestReadBuilder:
    """Tests for READ APDU builders."""

    def test_build_read_binary(self):
        """Test READ BINARY."""
        apdu = build_read_binary(0, 9)
        assert apdu == bytes.fromhex("00B0000009")

    def test_build_read_binary_with_offset(self):
        """Test READ BINARY with offset."""
        apdu = build_read_binary(10, 5)
        # P1-P2 = offset (000A), Le = 5
        assert apdu == bytes.fromhex("00B0000A05")

    def test_build_read_binary_all(self):
        """Test READ BINARY with Le=0 (read all)."""
        apdu = build_read_binary(0, 0)
        assert apdu == bytes.fromhex("00B0000000")

    def test_build_read_record(self):
        """Test READ RECORD."""
        apdu = build_read_record(1)
        assert apdu[0] == 0x00  # CLA
        assert apdu[1] == 0xB2  # INS


class TestAuthBuilder:
    """Tests for authentication APDU builders."""

    def test_build_verify_pin(self):
        """Test VERIFY PIN."""
        apdu = build_verify_pin(1, "1234")
        assert apdu[0] == 0x00  # CLA
        assert apdu[1] == 0x20  # INS VERIFY
        assert apdu[2] == 0x00  # P1
        assert apdu[3] == 0x01  # P2 (PIN1)

    def test_build_verify_pin_empty(self):
        """Test VERIFY PIN without PIN value."""
        apdu = build_verify_pin(1)
        assert len(apdu) == 4  # No Lc or data

    def test_build_get_challenge(self):
        """Test GET CHALLENGE."""
        apdu = build_get_challenge(8)
        assert apdu == bytes.fromhex("0084000008")


class TestSWParser:
    """Tests for SW parser."""

    def test_decode_sw_success(self):
        """Test decode success SW."""
        from apdu.constants.sw_codes import decode_sw
        result = decode_sw("9000")
        assert "正常完成" in result

    def test_decode_sw_error(self):
        """Test decode error SW."""
        from apdu.constants.sw_codes import decode_sw
        result = decode_sw("6982")
        assert "安全条件" in result

    def test_is_success(self):
        """Test is_success function."""
        from apdu.constants.sw_codes import is_success
        assert is_success("9000") == True
        assert is_success("61XX") == True
        assert is_success("6982") == False


class TestTLVParser:
    """Tests for TLV parser."""

    def test_parse_simple_tlv(self):
        """Test parse simple TLV."""
        from apdu.parsers.tlv_parser import parse_tlv
        # Tag 80, Length 02, Value 0001
        data = bytes.fromhex("80020001")
        result = parse_tlv(data)
        assert "80" in result
        assert result["80"] == bytes.fromhex("0001")

    def test_parse_constructed_tlv(self):
        """Test parse constructed TLV."""
        from apdu.parsers.tlv_parser import parse_tlv
        # Tag 6F (constructed), Length 05, containing 80 02 0001
        data = bytes.fromhex("6F0580020001")
        result = parse_tlv(data)
        assert "6F" in result
        assert isinstance(result["6F"], dict)

    def test_build_tlv(self):
        """Test build TLV."""
        from apdu.parsers.tlv_parser import build_tlv
        result = build_tlv("80", bytes.fromhex("0001"))
        assert result == bytes.fromhex("80020001")