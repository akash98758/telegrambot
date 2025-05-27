# AI-Powered Telegram Job Channel Bot

This project is an AI-powered Telegram bot that automatically sources job postings from RSS feeds, processes them using the Gemini AI model, and posts them to a specified Telegram channel. It is designed to avoid duplicate postings and run at regular intervals.

## Features

*   Fetches job data from multiple RSS feeds.
*   Uses Google's Gemini AI to process and summarize job details, and generate relevant hashtags.
*   Posts formatted job listings to a Telegram channel.
*   Prevents duplicate job postings using a local SQLite database.
*   Scheduled job fetching and posting using APScheduler.
*   Configurable via environment variables.

## Setup Instructions

1.  **Clone the Repository:**
    ```bash
    git clone <your-repository-url>
    cd <repository-directory>
    ```

2.  **Create a Python Virtual Environment:**
    It's highly recommended to use a virtual environment to manage project dependencies.
    ```bash
    python -m venv venv
    ```
    Activate the environment:
    *   On Windows:
        ```bash
        .\venv\Scripts\activate
        ```
    *   On macOS and Linux:
        ```bash
        source venv/bin/activate
        ```

3.  **Install Dependencies:**
    Install all required Python packages using the `requirements.txt` file:
    ```bash
    pip install -r requirements.txt
    ```

### Environment Variables

This project uses a `.env` file to manage environment variables for configuration.

1.  **Create your `.env` file:**
    Make a copy of the example file `.env.example` and name it `.env`:
    ```bash
    cp .env.example .env
    ```

2.  **Edit your `.env` file:**
    Open the `.env` file with a text editor and fill in your actual credentials and configuration values:
    *   `BOT_TOKEN`: Your Telegram Bot Token obtained from BotFather.
    *   `CHANNEL_ID`: The ID of your Telegram channel (e.g., `-1001234567890` for private channels/supergroups, or `@yourchannelusername` for public channels).
    *   `GEMINI_API_KEY`: Your API key for the Gemini AI.
    *   `RSS_FEED_URLS`: A comma-separated list of RSS feed URLs you want to source jobs from (e.g., `https://example.com/feed1.xml,https://another.example.com/feed2.xml`).
    *   `JOB_POSTING_INTERVAL_HOURS`: The interval (in hours) at which the bot should check for and post new jobs (e.g., `1` for every hour).

3.  **Important Security Note:**
    The `.env` file contains sensitive credentials. **DO NOT commit it to version control (Git).** If you are using Git, make sure `.env` is listed in your `.gitignore` file. A general Python `.gitignore` template usually includes this. If not, add a line containing just `.env` to your `.gitignore`.

### RSS Feed URL Configuration

The primary way to configure the RSS feed URLs is through the `RSS_FEED_URLS` variable in your `.env` file. This should be a comma-separated list of valid RSS feed URLs.

Example in `.env`:
```
RSS_FEED_URLS=https://example.com/feed1.xml,https://jobs.another-site.com/rss
```

If the `RSS_FEED_URLS` environment variable is not set or is empty, the bot will fall back to a hardcoded list in `telegram_bot_framework.py`. However, it is strongly recommended to use the `.env` file method.

You **must** ensure that valid, non-placeholder URLs are provided either through the `.env` file or, as a last resort, by editing the fallback list in `telegram_bot_framework.py` for the bot to fetch jobs.

## Running the Bot

Once the setup is complete, you can run the bot using the main script:

```bash
python telegram_bot_framework.py
```

The bot will then start, initialize its components, perform an initial job processing run, and then continue to run, fetching and posting jobs at the scheduled interval. Log messages will be printed to the console and saved to `job_bot.log`.

## Project Structure

The project consists of the following key Python files:

*   **`telegram_bot_framework.py`**:
    The main script that orchestrates the bot's operations. It initializes the Telegram bot, Gemini AI, database, and scheduler. It manages the job processing cycle (fetching, processing, posting) and handles the scheduling of these tasks.

*   **`rss_sourcing.py`**:
    Contains functions for fetching and parsing job data from RSS feeds using the `feedparser` library. It extracts raw job information like title, link, summary, and publication date.

*   **`gemini_processor.py`**:
    Interfaces with the Google Gemini AI model. It takes raw job data, sends it to the Gemini API with a specific prompt, and processes the response to extract structured information (e.g., job title, company name, location, concise summary, hashtags).

*   **`database.py`**:
    Manages a local SQLite database (`job_channel.db`) to store job URLs that have already been posted. This is used to prevent duplicate job postings to the Telegram channel.

*   **`requirements.txt`**:
    Lists all Python dependencies required for the project.

*   **`README.md`**:
    This file, providing information about the project.
