
# X.com Tweet Scraper

A Python tool to scrape tweets from X.com (formerly Twitter) user profiles and save them as text files.

## Features

- Scrape tweets from any public X.com profile
- Save tweets as text files to your Desktop
- Configure the number of tweets to collect
- View browser activity (optional headless mode)
- Robust error handling for X.com's dynamic structure

## Installation

### Requirements
- Python 3.6+
- Chrome browser
- ChromeDriver

### Setup

1. Clone this repository:
```bash
git clone https://github.com/Attractiveness/tweetscraperx.git
cd tweetscraperx
```

2. Install the required packages:
```bash
pip install -r requirements.txt
```

3. Install ChromeDriver:
   - **macOS**: `brew install --cask chromedriver`
   - **Linux**: Use your package manager or download from the [ChromeDriver website](https://sites.google.com/chromium.org/driver/)
   - **Windows**: Download from the [ChromeDriver website](https://sites.google.com/chromium.org/driver/) and add to your PATH

## Usage

Run the script:
```bash
python scraper.py
```

Follow the interactive prompts:
1. Enter the X.com username (with or without @ symbol)
2. Choose whether to limit the number of tweets to scrape
3. Specify a custom output filename (optional)
4. Choose whether to run in headless mode or view the browser

## Example Output

The script saves tweets in a text file with the following format:

```
Tweets from @username
Retrieved on: 2025-04-20 14:30:45
--------------------------------------------------------------------------------

Tweet #1:
Time: 2025-04-19T23:15:30.000Z
Text: This is an example tweet text.

--------------------------------------------------------------------------------

Tweet #2:
Time: 2025-04-18T14:22:10.000Z
Text: Another example tweet.

--------------------------------------------------------------------------------
```

## Limitations

- This scraper relies on X.com's web structure, which may change
- X.com may rate-limit or block automated scraping activity
- Only works with public profiles
- Currently only extracts text content (not images or videos)

## License

MIT License - See [LICENSE](LICENSE) file for details.

## Disclaimer

This tool is for educational purposes only. Use responsibly and in accordance with X.com's Terms of Service.
