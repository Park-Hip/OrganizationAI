"""Minimal environment smoke check for the L0 foundation.

Proves typed settings load for the current environment without connecting
to the database. The health endpoint is the database reachability probe.
"""

from __future__ import annotations

import sys

from app.core.settings import get_settings


def main() -> int:
    try:
        settings = get_settings()
    except Exception as exc:  # report any configuration failure with a clear exit code
        print(f"Environment smoke check failed: {exc}", file=sys.stderr)
        return 1

    print(
        f"Environment smoke OK: app={settings.app_name!r} "
        f"environment={settings.environment!r} log_level={settings.log_level!r} "
        f"database_url={'configured' if settings.database_url.get_secret_value() else 'missing'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
