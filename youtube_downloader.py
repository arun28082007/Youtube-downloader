
import yt_dlp
import argparse
import json
import os
import sys
from rich.console import Console
from rich.table import Table
from rich.progress import Progress
import questionary

# --- Global variables ---
INTERACTIVE = sys.stdout.isatty()
CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".youtube_downloader_config.json")
console = Console()

# --- Config Functions ---
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

# --- Core yt-dlp Functions ---
def get_info(url):
    ydl_opts = {'quiet': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info_dict = ydl.extract_info(url, download=False)
            return info_dict
        except yt_dlp.utils.DownloadError as e:
            console.print(f"[red]Error: {e}[/red]")
            return None

def display_formats(info_dict):
    if not info_dict:
        return

    table = Table(title="Available Formats")
    table.add_column("ID", style="cyan")
    table.add_column("Ext", style="magenta")
    table.add_column("Type", style="green")
    table.add_column("Resolution", style="yellow")
    table.add_column("Size (MB)", style="blue")

    for f in info_dict.get('formats', []):
        size_mb = f.get('filesize')
        if size_mb:
            size_mb = round(size_mb / (1024 * 1024), 2)
        else:
            size_mb = "N/A"

        resolution = f.get('resolution', 'audio only')
        if resolution == 'audio only':
            resolution = f"{f.get('abr')}k"

        table.add_row(
            f.get('format_id'),
            f.get('ext'),
            f.get('vcodec') if f.get('vcodec') != 'none' else 'audio',
            resolution,
            str(size_mb)
        )
    console.print(table)

def download(urls, format_id=None, audio_only=False, output_path='.'):
    config = load_config()
    output_path = output_path or config.get('output_path', '.')

    with Progress(console=console) as progress:
        task = progress.add_task("[cyan]Downloading...", total=100)

        def progress_hook(d):
            if d['status'] == 'downloading':
                total_bytes = d.get('total_bytes')
                downloaded_bytes = d.get('downloaded_bytes')
                if total_bytes and downloaded_bytes:
                    percentage = (downloaded_bytes / total_bytes) * 100
                    progress.update(task, completed=percentage)
            elif d['status'] == 'finished':
                progress.update(task, completed=100)

        ydl_opts = {
            'progress_hooks': [progress_hook],
            'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
        }

        if audio_only:
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        elif format_id:
            ydl_opts['format'] = format_id
        else:
            ydl_opts['format'] = 'bestvideo+bestaudio/best'

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            for url in urls:
                try:
                    console.print(f"[yellow]Starting download for:[/] {url}")
                    ydl.download([url])
                    console.print("[green]Download finished.[/green]")
                except yt_dlp.utils.DownloadError as e:
                    console.print(f"[red]Error downloading {url}: {e}[/red]")

def search_and_select(query, args):
    ydl_opts = {'quiet': True, 'default_search': 'ytsearch', 'extract_flat': 'in_playlist'}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            result = ydl.extract_info(query, download=False)
            if not (result and 'entries' in result):
                console.print("[red]No search results found.[/red]")
                return

            table = Table(title=f"Search Results for \"{query}\"")
            table.add_column("#", style="cyan")
            table.add_column("Title", style="green")
            table.add_column("Duration", style="yellow")
            table.add_column("URL", style="blue")
            
            choices = []
            for i, entry in enumerate(result['entries']):
                duration_string = entry.get('duration_string')
                if not duration_string:
                    duration = entry.get('duration')
                    if duration:
                        minutes, seconds = divmod(int(duration), 60)
                        hours, minutes = divmod(minutes, 60)
                        duration_string = f'{hours}:{minutes:02d}:{seconds:02d}' if hours > 0 else f'{minutes:02d}:{seconds:02d}'
                    else:
                        duration_string = "N/A"
                
                video_url = f"https://www.youtube.com/watch?v={entry.get('id')}"
                title = entry.get('title', 'N/A')
                table.add_row(str(i+1), title, duration_string, video_url)
                choices.append((title, video_url))

            console.print(table)

            if INTERACTIVE:
                selected_video = questionary.select(
                    "Select a video to download:", 
                    choices=[f"{i+1}. {c[0]}" for i, c in enumerate(choices)] + ["Cancel"]
                ).ask()

                if selected_video and selected_video != "Cancel":
                    index = int(selected_video.split('.')[0]) - 1
                    url = choices[index][1]
                    handle_url(url, args, is_interactive=True)

        except yt_dlp.utils.DownloadError as e:
            console.print(f"[red]Error: {e}[/red]")

def handle_url(url, args, is_interactive=False):
    info = get_info(url)
    if not info:
        return

    # --- Interactive Mode ---
    if is_interactive:
        if 'entries' in info: # Playlist
            playlist_choice = questionary.select(
                f"This is a playlist with {len(info['entries'])} videos. What would you like to do?",
                choices=["Download all", "Select videos to download", "Cancel"]
            ).ask()

            if playlist_choice == "Download all":
                download([url], audio_only=args.audio_only, output_path=args.output_path)
            elif playlist_choice == "Select videos to download":
                selected_titles = questionary.checkbox(
                    "Select videos:", choices=[e['title'] for e in info['entries']]
                ).ask()
                if selected_titles:
                    urls_to_download = [e['webpage_url'] for e in info['entries'] if e['title'] in selected_titles]
                    download(urls_to_download, audio_only=args.audio_only, output_path=args.output_path)
        else: # Single Video
            display_formats(info)
            download_choice = questionary.select(
                "Select download option:",
                choices=["Best quality", "Audio only", "Specific format", "Cancel"]
            ).ask()

            if download_choice == "Best quality":
                download([url], output_path=args.output_path)
            elif download_choice == "Audio only":
                download([url], audio_only=True, output_path=args.output_path)
            elif download_choice == "Specific format":
                format_id = questionary.text("Enter the format ID:").ask()
                if format_id:
                    download([url], format_id=format_id, output_path=args.output_path)
        return

    # --- Non-Interactive (CLI) Mode ---
    if args.info:
        display_formats(info)
    if args.download:
        download([url], args.format_id, args.audio_only, args.output_path)

def main():
    parser = argparse.ArgumentParser(description="A user-friendly YouTube downloader.")
    parser.add_argument("urls", nargs='*', help="YouTube URL(s) (video, playlist, channel).")
    parser.add_argument("-i", "--info", action="store_true", help="List available formats.")
    parser.add_argument("-d", "--download", action="store_true", help="Download video/audio.")
    parser.add_argument("-f", "--format-id", help="The format ID to download (CLI mode). ")
    parser.add_argument("-a", "--audio-only", action="store_true", help="Download audio only (mp3).")
    parser.add_argument("-o", "--output-path", help="Path to save the downloaded file.")
    parser.add_argument("--batch-file", help="File with a list of URLs to download.")
    parser.add_argument("-s", "--search", help="Search YouTube.")
    parser.add_argument("--config", help="Set a default config value. e.g., --config output_path=/path/to/dir")

    args = parser.parse_args()

    if args.config:
        key, value = args.config.split('=')
        config = load_config()
        config[key] = value
        save_config(config)
        console.print(f"[green]Configuration updated: {key} = {value}[/green]")
        return

    if args.search:
        search_and_select(args.search, args)
        return

    urls = args.urls
    if args.batch_file:
        with open(args.batch_file, 'r') as f:
            urls.extend([line.strip() for line in f if line.strip()])

    if not urls:
        if INTERACTIVE:
            try:
                query = questionary.text("Enter a YouTube URL or a search query:").ask()
                if query:
                    if query.startswith("http"):
                        handle_url(query, args, is_interactive=True)
                    else:
                        search_and_select(query, args)
            except (EOFError, KeyboardInterrupt):
                console.print("\n[yellow]Exiting.[/yellow]")
        else:
            parser.print_help()
        return

    for url in urls:
        handle_url(url, args)

if __name__ == "__main__":
    main()
