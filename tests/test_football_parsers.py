"""Tests for football parser utility functions."""

from datetime import date

from dataflow.football.parsers.salimt import (
    parse_transfer_fee,
    parse_date_unix,
    parse_height,
    parse_season,
)


class TestParseTransferFee:
    """Test transfer fee parsing with various formats."""

    def test_parse_fee_in_millions(self):
        """Parse fee in millions (€12.5m format)."""
        fee_eur, is_loan = parse_transfer_fee("€12.5m")
        assert fee_eur == 12500000
        assert is_loan is False

    def test_parse_fee_in_thousands(self):
        """Parse fee in thousands (€500k format)."""
        fee_eur, is_loan = parse_transfer_fee("€500k")
        assert fee_eur == 500000
        assert is_loan is False

    def test_parse_free_transfer(self):
        """Parse free transfer."""
        fee_eur, is_loan = parse_transfer_fee("free transfer")
        assert fee_eur == 0
        assert is_loan is False

    def test_parse_loan(self):
        """Parse loan transfer."""
        fee_eur, is_loan = parse_transfer_fee("Loan")
        assert fee_eur is None
        assert is_loan is True

    def test_parse_unknown_fee(self):
        """Parse unknown fee (? or -)."""
        fee_eur, is_loan = parse_transfer_fee("?")
        assert fee_eur is None
        assert is_loan is False

        fee_eur, is_loan = parse_transfer_fee("-")
        assert fee_eur is None
        assert is_loan is False

    def test_parse_none_fee(self):
        """Parse None fee."""
        fee_eur, is_loan = parse_transfer_fee(None)
        assert fee_eur is None
        assert is_loan is False

    def test_parse_empty_string(self):
        """Parse empty string."""
        fee_eur, is_loan = parse_transfer_fee("")
        assert fee_eur is None
        assert is_loan is False


class TestParseDateUnix:
    """Test Unix timestamp parsing."""

    def test_parse_valid_timestamp(self):
        """Parse valid Unix timestamp."""
        # 1609459200 = 2021-01-01 00:00:00 UTC (timezone-safe)
        parsed_date = parse_date_unix(1609459200)
        assert parsed_date is not None
        assert isinstance(parsed_date, date)

    def test_parse_none_timestamp(self):
        """Parse None timestamp."""
        parsed_date = parse_date_unix(None)
        assert parsed_date is None

    def test_parse_float_timestamp(self):
        """Parse float timestamp."""
        parsed_date = parse_date_unix(1672531200.5)
        assert isinstance(parsed_date, date)


class TestParseHeight:
    """Test height parsing with various formats."""

    def test_parse_height_european_format(self):
        """Parse height in European format (1,85 m)."""
        height_cm = parse_height("1,85 m")
        assert height_cm == 185

    def test_parse_height_us_format(self):
        """Parse height in US format (1.80 m)."""
        height_cm = parse_height("1.80 m")
        assert height_cm == 180

    def test_parse_height_integer(self):
        """Parse height as integer (cm)."""
        height_cm = parse_height("185")
        assert height_cm == 185

    def test_parse_height_none(self):
        """Parse None height."""
        height_cm = parse_height(None)
        assert height_cm is None

    def test_parse_height_empty_string(self):
        """Parse empty height string."""
        height_cm = parse_height("")
        assert height_cm is None

    def test_parse_height_invalid_range(self):
        """Parse height outside valid range (100-250cm)."""
        # Too short
        height_cm = parse_height("0.50 m")
        assert height_cm is None

        # Too tall
        height_cm = parse_height("3.00 m")
        assert height_cm is None


class TestParseSeason:
    """Test season parsing with various formats."""

    def test_parse_season_two_digit(self):
        """Parse 2-digit season format (23/24 → 2023)."""
        season = parse_season("23/24")
        assert season == 2023

    def test_parse_season_four_digit(self):
        """Parse 4-digit season format (2023/24 → 2023)."""
        season = parse_season("2023/24")
        assert season == 2023

    def test_parse_season_none(self):
        """Parse None season."""
        season = parse_season(None)
        assert season is None

    def test_parse_season_empty_string(self):
        """Parse empty season string."""
        season = parse_season("")
        assert season is None

    def test_parse_season_invalid_format(self):
        """Parse invalid season format."""
        season = parse_season("invalid")
        assert season is None
