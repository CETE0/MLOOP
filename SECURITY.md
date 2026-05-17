# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in MLOOP, please report it privately through GitHub Security Advisories or by contacting the maintainers directly.

**Please do not report security vulnerabilities through public GitHub issues.**

## Security Considerations

### mpv IPC

MLOOP uses mpv's JSON IPC interface for playback control. This interface is **not a secure network protocol**. MLOOP uses a local Unix socket only (`/run/mloop/mpv.sock`), which limits exposure to local processes.

### Web UI

The web UI is **disabled by default**. When enabled in the future, it will bind to `127.0.0.1` by default and require explicit configuration to expose to the network.

### Configuration Files

Configuration files are stored in standard system directories:
- `/etc/mloop/config.toml` - requires root to modify
- `/var/lib/mloop/state.toml` - writable by the `mloop` user

### Recommendations

- Run MLOOP as a dedicated `mloop` user with minimal privileges
- Do not expose the mpv IPC socket to the network
- Keep the system updated with security patches
- Use Raspberry Pi OS security best practices
