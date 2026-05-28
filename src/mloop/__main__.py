"""MLOOP daemon entry point."""

import asyncio
import os
from pathlib import Path

from mloop.config import Config, load_config
from mloop.daemon import Daemon


async def main() -> None:
    """Run the MLOOP daemon."""
    config_dir = os.environ.get("MLOOP_CONFIG_DIR")
    config_path = Path(config_dir, "config.toml") if config_dir else None
    config = load_config(config_path) if config_path else load_config()
    daemon = Daemon(config=config)
    try:
        await daemon.run()
    except KeyboardInterrupt:
        await daemon.stop()
    except Exception:
        await daemon.stop()
        raise


if __name__ == "__main__":
    asyncio.run(main())
