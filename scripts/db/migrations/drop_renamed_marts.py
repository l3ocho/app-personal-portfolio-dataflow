#!/usr/bin/env python3
"""Drop mart tables that were renamed in dbt.

dbt does not automatically drop tables when models are renamed.
This script cleans up the old table names after renames.

Run this once after deploying a rename change.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from sqlalchemy import text

from dataflow.toronto.models import get_engine


RENAMED_TABLES = [
    # (schema, old_name)
    ("mart_toronto", "mart_toronto__neighbourhood_profile"),
]


def main() -> int:
    engine = get_engine()
    with engine.begin() as conn:
        for schema, table in RENAMED_TABLES:
            conn.execute(text(f'DROP TABLE IF EXISTS {schema}."{table}"'))
            print(f"Dropped {schema}.{table} (if existed)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
