from __future__ import annotations

import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

    try:
        from dotenv import load_dotenv
    except Exception:
        pass
    else:
        load_dotenv()

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
