# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ComicHub is a Python-based comic downloader for manhuagui.com (漫画柜) using Selenium WebDriver for dynamic content scraping. It supports resumable downloads via PostgreSQL tracking and multi-threaded image downloading.

## Development Commands

### Setup
```bash
# Install dependencies (uses local .venv)
pip install -r requirements.txt

# Ensure chromedriver is installed and accessible
# On macOS with Homebrew:
brew install chromedriver

# Run the CLI
python cli.py --help
```

### Common Operations
```bash
# Search and download comics
python cli.py search --keyword "海贼王" --limit 1

# Download specific comic by URL
python cli.py url --url "https://m.manhuagui.com/comic/1128/"

# Download with chapter range
python cli.py url --url "https://m.manhuagui.com/comic/1128/" --start-chapter 1170 --end-chapter 1172

# List downloaded comics in database
python cli.py list

# View comic details
python cli.py info --name "海贼王"

# Test functionality
python cli.py test
```

### Scripts
- `scripts/download_comic.py` - Standalone comic download script
- `scripts/download_all_comics.py` - Batch download multiple comics
- `scripts/analyze_chapter.py` - Debug chapter structure

## Architecture

### Three-Layer Design

1. **Fetch Layer** ([`comichub/core/fetcher.py`](comichub/core/fetcher.py))
   - `ManhuaGuiFetcherSelenium`: Selenium-based scraper for dynamic content
   - Handles: comic search, comic info, chapter lists, image URLs with pagination
   - Uses BeautifulSoup for HTML parsing after Selenium loads pages
   - Requires local `chromedriver` installation (auto-detects common paths)

2. **Download Layer** ([`comichub/downloader/batch.py`](comichub/downloader/batch.py))
   - `BatchDownloader`: Orchestrates multi-threaded downloads
   - Uses `ThreadPoolExecutor` for concurrent image downloads
   - Retry logic, progress tracking via `tqdm`, database state updates

3. **Data Layer** ([`comichub/core/database.py`](comichub/core/database.py))
   - `Database`: PostgreSQL wrapper with psycopg2
   - Tables: `comics`, `chapters`, `images`, `fetch_history`
   - Tracks download state for resumability

### Configuration

All configuration via [`config.yaml`](config.yaml) loaded by [`comichub/core/config.py`](comichub/core/config.py):

```yaml
save_path: ~/data/comics
database:
  host: localhost
  port: 5432
  database: comichub
  user: postgres
  password: postgres
fetch:
  concurrent_downloads: 5
  delay: 1
  retry: 3
  timeout: 30
```

### Key Data Flow

1. `cli.py` → Creates `ComicHubCLI` instance
2. For URL downloads: `fetch_comic_by_url()` → `BatchDownloader.download_comic()`
3. `BatchDownloader` calls `ManhuaGuiFetcherSelenium` methods:
   - `get_comic_info()` - metadata
   - `get_chapters()` - chapter list
   - `get_images()` - image URLs (handles pagination)
4. Images downloaded in parallel, database updated per-chapter
5. `info.txt` generated with statistics

## Important Notes

### ChromeDriver Setup
The fetcher auto-detects `chromedriver` at:
- `/usr/local/bin/chromedriver`
- `/usr/bin/chromedriver`
- `/opt/homebrew/bin/chromedriver`
- Or via `which chromedriver`

If not found, defaults to `/usr/local/bin/chromedriver`. Ensure the executable is on your PATH.

### Chapter Number Extraction
Chapter numbers are extracted from titles matching pattern `第(\d+)[话章节]`. If unavailable, falls back to URL ID. This can cause issues if chapter titles don't follow the expected pattern.

### Image Pagination
The `get_images()` method handles multi-page chapter views by clicking "下一页" links, with a maximum of 30 pages to prevent infinite loops.

### Database State
The database enables resumable downloads - `chapters.downloaded` and `images.downloaded` flags track progress. Use `get_undownloaded_chapters()` to resume interrupted downloads.

## Testing

Test the fetcher without full download:
```bash
python cli.py test --url "https://m.manhuagui.com/comic/1128/" --keyword "海贼王"
```

This runs three tests: comic search, comic info retrieval, and chapter list fetching.
