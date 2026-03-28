from __future__ import annotations

import time
import psycopg2
from typing import Optional


def wait_for_postgres(timeout_seconds: int = 60) -> None:
    started_at = time.monotonic()
    last_error: Optional[BaseException] = None
