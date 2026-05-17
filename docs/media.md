# Media

MLOOP scans configured directories for media files and creates a playlist for continuous playback.

## Supported Formats

### Video

- `.mp4`
- `.mov`
- `.mkv`
- `.webm`
- `.m4v`

### Audio

- `.mp3`
- `.wav`
- `.flac`

### Images

- `.jpg`
- `.jpeg`
- `.png`

## Adding Media

1. Copy media files to your configured media directory (default: `/home/mloop/media`)
2. MLOOP will automatically detect new files on startup
3. Use "Rescan media" from the HDMI gesture menu to refresh without restarting

## Media Directory Configuration

Configure media directories in `/etc/mloop/config.toml`:

```toml
[playback]
media_dirs = ["/home/mloop/media", "/media/mloop"]
```

Multiple directories are supported. All directories are scanned and combined into a single playlist.

## Playlist Behavior

- Files are sorted alphabetically by default
- Set `shuffle = true` to randomize playback order
- Set `loop = true` to repeat the playlist indefinitely
- Images are displayed for `image_duration_seconds` (default: 10 seconds)

## No Media State

If no media files are found, MLOOP displays an error screen on the OSD indicating that no media was detected. Add media files and rescan to begin playback.
