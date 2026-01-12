# MyHeritage Family Tree Scraper & GEDCOM Exporter

A powerful, robust Python toolset designed to scrape family tree data from the MyHeritage web view (Canvas/SVG) and convert it into a standard GEDCOM 5.5.1 file with photo support.

## 🚀 Features

*   **Smart Recursive Crawling**: Automatically navigates through family tree branches to capture all individuals, even in large trees (6,000+ people).
*   **Intelligent Pivoting**: Identifies "expansion points" and distant relatives to maximize coverage.
*   **Photo Downloading**: Downloads high-quality profile photos and links them in the GEDCOM file.
*   **Anti-Ban Protection**: Includes random delays and human-like browsing patterns to avoid rate-limiting.
*   **State Recovery**: Saves progress automatically. If the script stops, it resumes exactly where it left off.
*   **GEDCOM 5.5.1 Compliance**: Generates files compatible with all major genealogy software (Ancestry, MyHeritage, Family Tree Builder, Gramps).

## 📋 Prerequisites

*   Python 3.8 or higher
*   [Playwright](https://playwright.dev/) for browser automation

## 🛠️ Installation

1.  Clone this repository:
    ```bash
    git clone https://github.com/yourusername/scrapeHeritage.git
    cd scrapeHeritage
    ```

2.  Install required Python packages:
    ```bash
    pip install playwright aiohttp
    ```

3.  Install Playwright browsers:
    ```bash
    playwright install chromium
    ```

## 📖 Usage

### Step 1: Scraping the Tree
Run the scraper script. You will need to provide the URL of the family tree view.

```bash
python heritage_scraper.py
```

*   **Input**: The script currently has a hardcoded URL example in `__main__`, but you can modify it to accept user input or hardcode your target URL.
*   **Output**: A JSON data file (e.g., `output/tree_ID_data.json`) and a folder of images (e.g., `output/tree_ID_photos`).

### Step 2: Exporting to GEDCOM
Convert the scraped JSON data into a GEDCOM file.

```bash
python smart_gedcom.py output/tree_YOUR_ID_data.json
```

*   **Output**: A `.ged` file (e.g., `tree_YOUR_ID.ged`) ready for import into any genealogy software.

## ⚠️ Important Notes

*   **Rate Limiting**: MyHeritage has strict rate limits. The scraper is configured to run slowly (8-15 seconds per page load) to respect these limits. If you get blocked, wait 24 hours before trying again.
*   **Private Data**: This tool runs locally on your machine using your browser session. It creates a local copy of the data you have access to.
*   **Terms of Service**: Use this tool responsibly and in accordance with MyHeritage's Terms of Service. This is for personal backup and data portability purposes only.

## 📂 Project Structure

*   `heritage_scraper.py`: Main scraper logic (crawler, photo downloader).
*   `smart_gedcom.py`: Converter that transforms JSON data + photos to GEDCOM format.
*   `recursive_crawler.py`: (Legacy) Earlier version of the crawler.

## 📄 License

This project is open-source. Feel free to modify and adapt it to your needs.
