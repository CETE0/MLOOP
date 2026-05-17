"""MLOOP daemon entry point."""

import asyncio

from mloop.daemon import Daemon


async def main() -> None:
    """Run the MLOOP daemon."""
    daemon = Daemon()
    try:
        await daemon.run()
    except KeyboardInterrupt:
        await daemon.stop()
    except Exception:
        await daemon.stop()
        raise


if __name__ == "__main__":
    asyncio.run(main())
