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

        Raises:
            NotImplementedError: Deloitte parser not yet implemented.
        """
        raise NotImplementedError(
            "Deloitte Money League parser not yet implemented. "
            "Phase 2+ feature requiring PDF extraction. "
            "See RFC Section 4 for extraction strategy."
        )
