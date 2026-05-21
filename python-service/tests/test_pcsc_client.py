"""Tests for PCSC client (with mocks)."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from tools.pcsc.client import PcscClient, APDUResponse
from tools.pcsc.exceptions import ReaderNotFoundError, CardNotFoundError


class TestPcscClient:
    """Tests for PCSC client."""

    def test_list_readers_mock(self):
        """Test list readers with mock."""
        client = PcscClient()

        with patch("smartcard.System.readers") as mock_readers:
            mock_reader = Mock()
            mock_reader.__str__ = lambda self: "Mock Reader"
            mock_readers.return_value = [mock_reader]

            readers = client.list_readers()
            assert len(readers) == 1
            assert readers[0].name == "Mock Reader"

    def test_connect_no_reader(self):
        """Test connect when no reader available."""
        client = PcscClient()

        with patch("smartcard.System.readers") as mock_readers:
            mock_readers.return_value = []

            with pytest.raises(ReaderNotFoundError):
                client.connect()

    def test_send_apdu_mock(self):
        """Test send APDU with mock."""
        client = PcscClient()
        client.connection = Mock()
        client._connected = True

        # Mock transmit response
        client.connection.transmit = Mock(return_value=([0x62, 0x82], 0x90, 0x00))

        apdu = [0x00, 0xA4, 0x00, 0x00, 0x02, 0x3F, 0x00]
        response = client.send_apdu(apdu, check_sw=False)

        assert response.sw == "9000"
        assert response.success == True

    def test_disconnect(self):
        """Test disconnect."""
        client = PcscClient()
        client.connection = Mock()
        client._connected = True
        client.atr = bytes.fromhex("3B9F96801F")

        client.disconnect()

        assert client._connected == False
        assert client.connection is None
        assert client.atr is None


class TestAPDUResponse:
    """Tests for APDU response."""

    def test_sw_property(self):
        """Test SW property."""
        response = APDUResponse(data=bytes(), sw1=0x90, sw2=0x00)
        assert response.sw == "9000"

    def test_success_property(self):
        """Test success property."""
        response = APDUResponse(data=bytes(), sw1=0x90, sw2=0x00)
        assert response.success == True

        response2 = APDUResponse(data=bytes(), sw1=0x69, sw2=0x82)
        assert response2.success == False

    def test_data_with_response(self):
        """Test response with data."""
        data = bytes.fromhex("622382027F21")
        response = APDUResponse(data=data, sw1=0x90, sw2=0x00)
        assert response.data == data
        assert len(response.data) == 6


class TestExceptions:
    """Tests for PCSC exceptions."""

    def test_reader_not_found(self):
        """Test ReaderNotFoundError."""
        exc = ReaderNotFoundError()
        assert "No smart card reader" in str(exc)

    def test_card_not_found(self):
        """Test CardNotFoundError."""
        exc = CardNotFoundError("ACS ACR38")
        assert "ACS ACR38" in str(exc)

    def test_apdu_error(self):
        """Test APDUError."""
        exc = APDUError("6982", "Security condition not satisfied")
        assert exc.sw == "6982"
        assert "6982" in exc.description