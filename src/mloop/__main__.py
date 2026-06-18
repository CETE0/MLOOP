"""MLOOP daemon entry point."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

from mloop.config import load_config
from mloop.daemon import Daemon


async def _amain() -> None:
    """Run the MLOOP daemon asynchronously."""
    config_dir = os.environ.get("MLOOP_CONFIG_DIR")
    config_path = Path(config_dir, "config.toml") if config_dir else None
    config = load_config(config_path)
    daemon = Daemon(config=config)

    try:
        await daemon.run()
    except KeyboardInterrupt:
        await daemon.stop()
    except Exception:
        await daemon.stop()
        raise


def main() -> None:
    """Console-script entry point."""
    asyncio.run(_amain())


if __name__ == "__main__":
    main()
