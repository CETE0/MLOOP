"""MLOOP daemon entry point."""

from mloop.daemon import Daemon


def main() -> None:
    """Run the MLOOP daemon."""
    daemon = Daemon()
    try:
        daemon.run()
    except KeyboardInterrupt:
        daemon.stop()
    except Exception:
        daemon.stop()
        raise


if __name__ == "__main__":
    main()
