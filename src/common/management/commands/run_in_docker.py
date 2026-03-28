from __future__ import annotations

import subprocess
import sys
from argparse import ArgumentParser
from django.core.management.base import BaseCommand, CommandError
from typing import Any


class Command(BaseCommand):

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument("command", nargs="+", type=str)

    def handle(self, *args: Any, **options: Any) -> None:
        raw_command: list[str] = options["command"]
        if not raw_command:
            raise CommandError("Не задана команда для запуска.")
        
        result = subprocess.run(raw_command, capture_output=False)
        sys.exit(result.returncode)
