from __future__ import annotations

import subprocess
import sys
import time
from typing import Sequence

from .db import wait_for_postgres


def run_with_migrations(argv: Sequence[str]) -> int:
    wait_for_postgres()
    subprocess.run([sys.executable, "src/manage.py", "migrate", "--noinput"], check=True)
    result = subprocess.run(list(argv), check=False)
