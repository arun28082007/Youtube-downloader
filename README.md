# YouTube Downloader

A simple, yet powerful command-line tool to download videos and audio from YouTube.

## Features

*   Download videos, playlists, and channels.
*   Choose from a list of available formats and qualities.
*   See the required internet data before downloading.
*   Download audio-only and convert to MP3.
*   Progress bar for downloads.
*   Batch downloading.
*   Search for videos on YouTube.
*   Configuration file for default settings.

## Installation

1.  **Install Python:** Make sure you have Python 3.6+ installed.
2.  **Install Dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

3.  **Install FFmpeg:** This is required for downloading and converting video and audio.

    *   **On Termux:** `pkg install ffmpeg`
    *   **On Debian/Ubuntu:** `sudo apt-get install ffmpeg`
    *   **On MacOS:** `brew install ffmpeg`
    *   **On Windows:** Download from the official website and add to your PATH.

## Usage

```bash
python youtube_downloader.py [options] <URL>
```

**Examples:**

*   **List available formats:**

    ```bash
    python youtube_downloader.py --info <URL>
    ```

*   **Download a video (best quality):**

    ```bash
    python youtube_downloader.py --download <URL>
    ```

*   **Download a specific format:**

    ```bash
    python youtube_downloader.py --download --format-id <ID> <URL>
    ```

*   **Download audio only (as MP3):**

    ```bash
    python youtube_downloader.py --download --audio-only <URL>
    ```

*   **Download to a specific directory:**

    ```bash
    python youtube_downloader.py --download -o /path/to/directory <URL>
    ```

*   **Batch download from a file:**

    ```bash
    python youtube_downloader.py --download --batch-file /path/to/urls.txt
    ```

*   **Search for a video:**

    ```bash
    python youtube_downloader.py --search "Your search query"
    ```

## Disclaimer

This tool is for personal use only. Please respect YouTube's Terms of Service and copyright laws. The developers of this tool are not responsible for any misuse.
