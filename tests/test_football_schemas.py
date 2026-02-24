"""Tests for football Pydantic schemas."""

from datetime import date

import pytest
from pydantic import ValidationError

from dataflow.football.schemas.deloitte import ClubFinanceRecord
from dataflow.football.schemas.mlspa import MLSPASalaryRecord
from dataflow.football.schemas.salimt import (
    LeagueRecord,
    PlayerMarketValueRecord,
    PlayerRecord,
    TransferHistoryRecord,
)


class TestLeagueRecord:
    """Test LeagueRecord schema validation."""

    def test_valid_league(self):
        """Test valid league record."""
        record = LeagueRecord(
            league_id="GB1",
            league_name="Premier League",
            country="England",
            season_start_year=2023,
        )
        assert record.league_id == "GB1"
        assert record.league_name == "Premier League"

    def test_invalid_season_year(self):
        """Test that invalid season year raises ValidationError."""
        with pytest.raises(ValidationError):
            LeagueRecord(
                league_id="GB1",
                league_name="Premier League",
                country="England",
                season_start_year=1800,  # Too old
            )


class TestTransferHistoryRecord:
    """Test TransferHistoryRecord with various fee formats."""

    def test_valid_transfer_with_fee(self):
        """Test valid transfer with fee."""
        record = TransferHistoryRecord(
            player_id="123",
            from_club_id="456",
            to_club_id="789",
            transfer_date=date(2023, 6, 15),
            fee_eur=12500000,
            is_loan=False,
            season=2023,
        )
        assert record.fee_eur == 12500000
        assert record.is_loan is False

    def test_loan_transfer(self):
        """Test loan transfer (fee_eur=None, is_loan=True)."""
        record = TransferHistoryRecord(
            player_id="123",
            from_club_id="456",
            to_club_id="789",
            transfer_date=date(2023, 6, 15),
            fee_eur=None,
            is_loan=True,
        )
        assert record.fee_eur is None
        assert record.is_loan is True

    def test_free_transfer(self):
        """Test free transfer (fee_eur=0, is_loan=False)."""
        record = TransferHistoryRecord(
            player_id="123",
            from_club_id=None,
            to_club_id="789",
            transfer_date=date(2023, 6, 15),
            fee_eur=0,
            is_loan=False,
        )
        assert record.fee_eur == 0


class TestPlayerMarketValueRecord:
    """Test PlayerMarketValueRecord schema."""

    def test_valid_market_value(self):
        """Test valid market value record."""
        record = PlayerMarketValueRecord(
            player_id="123",
            club_id="456",
            value_eur=10000000,
            market_value_date=date(2023, 1, 1),
            season=2023,
        )
        assert record.value_eur == 10000000
        assert record.market_value_date == date(2023, 1, 1)

    def test_market_value_without_club(self):
        """Test market value when player has no club."""
        record = PlayerMarketValueRecord(
            player_id="123",
            club_id=None,
            value_eur=5000000,
            market_value_date=date(2023, 1, 1),
        )
        assert record.club_id is None


class TestMLSPASalaryRecord:
    """Test MLSPASalaryRecord schema."""

    def test_valid_mls_salary(self):
        """Test valid MLS salary record."""
        record = MLSPASalaryRecord(
            player_id="123",
            player_name="Test Player",
            club_id="LA",
            club_name="LA Galaxy",
            season=2023,
            salary_usd=500000,
            guaranteed_compensation_usd=450000,
        )
        assert record.salary_usd == 500000
        assert record.guaranteed_compensation_usd == 450000

    def test_mls_salary_without_guarantee(self):
        """Test MLS salary without guaranteed compensation."""
        record = MLSPASalaryRecord(
            player_id="123",
            player_name="Test Player",
            club_id="LA",
            club_name="LA Galaxy",
            season=2023,
            salary_usd=300000,
            guaranteed_compensation_usd=None,
        )
        assert record.guaranteed_compensation_usd is None


class TestPlayerRecord:
    """Test PlayerRecord with height parsing."""

    def test_valid_player(self):
        """Test valid player record."""
        record = PlayerRecord(
            player_id="123",
            player_name="Test Player",
            height_cm=185,
            position="Forward",
        )
        assert record.height_cm == 185

    def test_player_without_optional_fields(self):
        """Test player with minimal data."""
        record = PlayerRecord(
            player_id="123",
            player_name="Test Player",
        )
        assert record.date_of_birth is None
        assert record.height_cm is None


class TestClubFinanceRecord:
    """Test ClubFinanceRecord schema."""

    def test_valid_club_finance(self):
        """Test valid club finance record."""
        record = ClubFinanceRecord(
            club_id="123",
            club_name="Test Club",
            season=2023,
            revenue_eur=500000000,
            operating_profit_eur=50000000,
        )
        assert record.revenue_eur == 500000000
        assert record.operating_profit_eur == 50000000

    def test_club_finance_with_loss(self):
        """Test club with operating loss."""
        record = ClubFinanceRecord(
            club_id="123",
            club_name="Test Club",
            season=2023,
            revenue_eur=300000000,
            operating_profit_eur=-10000000,
        )
        assert record.operating_profit_eur == -10000000
