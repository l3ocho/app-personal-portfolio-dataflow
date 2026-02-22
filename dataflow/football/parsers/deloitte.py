"""Stub parser for Deloitte Money League revenue data.

Deloitte revenue extraction requires PDF parsing which is not yet implemented.
This stub is reserved for Phase 2+ implementation.
"""

import logging
from pathlib import Path

from dataflow.football.schemas.deloitte import ClubFinanceRecord

logger = logging.getLogger(__name__)


class DeloitteParser:
    """Stub parser for Deloitte Money League data.

    Phase 2+ implementation required for actual PDF extraction.
    """

    def __init__(self, data_root: Path) -> None:
        """Initialize parser.

        Args:
            data_root: Path to data root (for Phase 2+ PDF location)
        """
        self.data_root = Path(data_root)

    def parse(self) -> list[ClubFinanceRecord]:
        """Parse Deloitte revenue data.

        Phase 2 placeholder: Returns empty list until Deloitte data is available.
        Deloitte Money League reports are PDFs that require manual extraction or PDF parsing.

        Returns:
            Empty list (Deloitte data not yet available)
        """
        logger.info("Deloitte Money League parser: No data available in Phase 2")
        logger.debug(
            "Deloitte parser not yet implemented. Future implementation required for PDF extraction. "
            "Expected data: club revenue, operating profit, debt, etc. from Deloitte Money League reports"
        )
        return []
