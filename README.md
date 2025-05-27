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

4.  **Set Environment Variables:**
    The bot requires the following environment variables to be set. You can set these in your operating system or by creating a `.env` file and using a library like `python-dotenv` (though `python-dotenv` is not explicitly included in `requirements.txt` for this project, you can add it if you prefer this method).

    *   `TELEGRAM_BOT_TOKEN`: Your Telegram Bot Token obtained from BotFather.
    *   `TELEGRAM_CHANNEL_ID`: The ID of your Telegram channel (e.g., `@yourchannelname` or a numerical ID like `-1001234567890`).
    *   `GEMINI_API_KEY`: Your API key for the Google Gemini AI.
    *   `JOB_POSTING_INTERVAL_HOURS` (Optional): The interval in hours for fetching and posting jobs. Defaults to `1` if not set.

    Example:
    ```bash
    export TELEGRAM_BOT_TOKEN="your_bot_token_here"
    export TELEGRAM_CHANNEL_ID="@your_channel_username"
    export GEMINI_API_KEY="your_gemini_api_key_here"
    # export JOB_POSTING_INTERVAL_HOURS="2" # Optional
    ```

5.  **Configure RSS Feed URLs:**
    The list of RSS feed URLs is currently managed in the `telegram_bot_framework.py` script, within the `RSS_FEED_URLS` list.
    ```python
    # In telegram_bot_framework.py
    RSS_FEED_URLS = [
        "URL_1_PLACEHOLDER",
        "URL_2_PLACEHOLDER"
        # Replace these placeholders with actual RSS feed URLs.
        # e.g., "https://feeds.yourjobsite.com/jobs"
    ]
    ```
    You **must** replace the placeholder URLs with actual, valid RSS feed URLs for the bot to fetch jobs.
    For more flexible configuration, consider moving `RSS_FEED_URLS` to an environment variable (e.g., a comma-separated string) or a dedicated configuration file.

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
