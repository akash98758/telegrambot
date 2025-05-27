# telegram_bot_framework.py

import os
import logging
import asyncio
import re # For MarkdownV2 escaping

# Telegram Bot imports
from telegram import Bot
# from telegram.ext import ApplicationBuilder, ContextTypes # Not strictly needed for this version

# Scheduler imports
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Custom module imports
from rss_sourcing import get_jobs_from_all_feeds
from gemini_processor import configure_gemini, process_job_with_gemini
from database import initialize_db, add_job_posted, is_job_posted

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# --- Configuration ---
# Load from environment variables
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID") # e.g., "@yourchannelname" or "-1001234567890"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# RSS Feed URLs - Loaded from environment variable, with a fallback to a hardcoded list.
# The environment variable should be a comma-separated string of URLs.
RSS_FEED_URLS_ENV = os.getenv("RSS_FEED_URLS")
if RSS_FEED_URLS_ENV:
    RSS_FEED_URLS = [url.strip() for url in RSS_FEED_URLS_ENV.split(',') if url.strip()]
else:
    # Fallback to hardcoded list if the environment variable is not set or is empty
    RSS_FEED_URLS = [
        # "https://example.com/feed1.xml", # Example
        # "https://jobs.another-site.com/rss", # Example
        "URL_1_PLACEHOLDER", # Default placeholder
        "URL_2_PLACEHOLDER"  # Default placeholder
    ]

# Job posting interval (in hours)
JOB_POSTING_INTERVAL_HOURS = int(os.getenv("JOB_POSTING_INTERVAL_HOURS", 1))

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(module)s - %(message)s",
    handlers=[
        logging.FileHandler("job_bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Global bot instance (initialized in main)
bot_instance: Bot = None

def escape_markdown_v2(text: str) -> str:
    """Escapes text for Telegram MarkdownV2.
    
    See: https://core.telegram.org/bots/api#markdownv2-style
    """
    if not isinstance(text, str): # Ensure text is a string
        return ""
    # Order matters. `\` must be escaped first.
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    # Escape \ first, then other characters
    text = text.replace('\\', '\\\\')
    for char in escape_chars:
        text = text.replace(char, f'\\{char}')
    return text

async def process_and_post_jobs():
    """
    Fetches jobs from RSS feeds, processes them with Gemini, checks for duplicates,
    and posts new jobs to the Telegram channel.
    """
    logger.info("Starting job processing cycle...")
    global bot_instance

    if not bot_instance:
        logger.error("Bot instance not initialized. Skipping job processing cycle.")
        return

    if not RSS_FEED_URLS or all(url.startswith("URL_") and url.endswith("_PLACEHOLDER") for url in RSS_FEED_URLS):
        logger.warning("No actual RSS feed URLs configured. Skipping fetching jobs.")
        logger.info("Job processing cycle finished (no feeds).")
        return

    raw_jobs = get_jobs_from_all_feeds(RSS_FEED_URLS) # rss_sourcing was modified to accept this
    logger.info(f"Fetched {len(raw_jobs)} raw job entries.")

    new_jobs_posted_count = 0
    for raw_job in raw_jobs:
        job_url = raw_job.get('link')
        if not job_url or job_url == 'N/A':
            logger.warning(f"Skipping job with missing or invalid URL: {raw_job.get('title', 'Unknown Title')}")
            continue

        if await asyncio.to_thread(is_job_posted, job_url): # Run synchronous DB call in a thread
            logger.info(f"Skipping duplicate job (already posted): {job_url}")
            continue

        logger.info(f"Processing new job: {raw_job.get('title', 'Unknown Title')} ({job_url})")
        processed_data = await asyncio.to_thread(process_job_with_gemini, raw_job) # Run sync Gemini call in a thread

        if processed_data:
            job_title = escape_markdown_v2(processed_data.get('job_title', 'N/A'))
            company_name = escape_markdown_v2(processed_data.get('company_name', 'N/A'))
            location = escape_markdown_v2(processed_data.get('location', 'N/A'))
            summary = escape_markdown_v2(processed_data.get('summary', 'N/A'))
            url = processed_data.get('url', job_url) # Use original link if Gemini fails to return one
            
            # Ensure URL is not escaped for Markdown (it's a link)
            # but if other parts of the URL need escaping, that's more complex.
            # For simple URLs, this is fine.
            
            hashtags_list = processed_data.get('hashtags', [])
            # Escape each hashtag individually
            hashtags = " ".join([f"#{escape_markdown_v2(tag.replace('#', ''))}" for tag in hashtags_list if tag])


            message = (
                f"✨ *{job_title}* ✨\n\n"
                f"🏢 *Company:* {company_name}\n"
                f"📍 *Location:* {location}\n\n"
                f"📝 *Summary:*\n{summary}\n\n"
                f"🔗 *Apply here:* [Job Link]({url})\n\n"
                f"{hashtags}"
            )
            
            try:
                await bot_instance.send_message(
                    chat_id=CHANNEL_ID,
                    text=message,
                    parse_mode='MarkdownV2',
                    disable_web_page_preview=False # Or True, depending on preference
                )
                logger.info(f"Successfully posted job: {job_title} ({url})")
                if await asyncio.to_thread(add_job_posted, url): # Run synchronous DB call in a thread
                    logger.info(f"Successfully added job to database: {url}")
                    new_jobs_posted_count += 1
                else:
                    logger.error(f"Failed to add job to database after posting: {url}")
            except Exception as e:
                logger.error(f"Error sending Telegram message for {url}: {e}. Message content:\n{message}")
                # Potentially add more specific error handling for Telegram API errors
        else:
            logger.warning(f"Failed to process job with Gemini: {raw_job.get('title', 'Unknown Title')} ({job_url})")
    
    logger.info(f"Job processing cycle finished. Posted {new_jobs_posted_count} new jobs.")


async def main():
    """
    Main function to initialize the bot, database, Gemini, and start the scheduler.
    """
    global bot_instance
    logger.info("Starting bot application...")

    # --- Dependency Checks & Initialization ---
    critical_configs_missing = False
    if not BOT_TOKEN:
        logger.critical("CRITICAL: TELEGRAM_BOT_TOKEN environment variable not set.")
        critical_configs_missing = True
    if not CHANNEL_ID:
        logger.critical("CRITICAL: TELEGRAM_CHANNEL_ID environment variable not set.")
        critical_configs_missing = True
    if not GEMINI_API_KEY:
        logger.critical("CRITICAL: GEMINI_API_KEY environment variable not set.")
        critical_configs_missing = True

    # Validate RSS_FEED_URLS - ensure at least one non-placeholder URL exists
    # This check is also present in the __main__ block but good to have in main() too for programmatic calls.
    valid_rss_urls = [url for url in RSS_FEED_URLS if url and not (url.startswith("URL_") and url.endswith("_PLACEHOLDER"))]
    if not valid_rss_urls:
        logger.critical("CRITICAL: RSS_FEED_URLS list is empty or contains only placeholder URLs. No jobs can be fetched.")
        critical_configs_missing = True
        
    if critical_configs_missing:
        logger.critical("One or more critical configurations are missing or invalid. Exiting application.")
        return # Exit if critical configurations are missing
    
    logger.info("All critical environment variables and configurations seem to be present.")

    # Initialize Database
    # Running synchronous function in a thread for async context
    await asyncio.to_thread(initialize_db)
    logger.info("Database initialized.")

    # Configure Gemini
    # Running synchronous function in a thread for async context
    gemini_ok = await asyncio.to_thread(configure_gemini)
    if not gemini_ok:
        logger.critical("Failed to configure Gemini API. Check API key and connectivity. Exiting.")
        # Depending on desired behavior, you might allow the bot to run without Gemini
        # but for this project, it's a core component.
        return
    logger.info("Gemini API configured.")

    # Initialize Telegram Bot
    bot_instance = Bot(token=BOT_TOKEN)
    bot_info = await bot_instance.get_me()
    logger.info(f"Telegram Bot initialized: {bot_info.username} (ID: {bot_info.id})")
    
    # --- Scheduler Setup ---
    scheduler = AsyncIOScheduler(timezone="UTC") # Or your local timezone
    scheduler.add_job(
        process_and_post_jobs,
        'interval',
        hours=JOB_POSTING_INTERVAL_HOURS,
        # For testing, you might want a shorter interval:
        # minutes=1,
        id="job_posting_task",
        replace_existing=True
    )
    scheduler.start()
    logger.info(f"Scheduler started. Job processing will run every {JOB_POSTING_INTERVAL_HOURS} hour(s).")

    # Keep the script running
    try:
        # Optionally, run the job once immediately on startup
        logger.info("Performing initial job processing run...")
        await process_and_post_jobs()
        
        while True:
            await asyncio.sleep(3600) # Keep the main coroutine alive
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped. Bot shutting down.")
    finally:
        if scheduler.running:
            scheduler.shutdown()
        logger.info("Bot application finished.")


if __name__ == '__main__':
    # This script is intended to be run directly.
    # The old send_test_message and direct main() call from previous versions are removed.
    
    # Perform initial checks before starting asyncio loop
    # These checks are also done inside main(), but good for an early exit if __name__ == '__main__'.
    initial_check_critical_configs_missing = False
    if not BOT_TOKEN:
        logger.critical("CRITICAL (startup check): TELEGRAM_BOT_TOKEN environment variable not set.")
        initial_check_critical_configs_missing = True
    if not CHANNEL_ID:
        logger.critical("CRITICAL (startup check): TELEGRAM_CHANNEL_ID environment variable not set.")
        initial_check_critical_configs_missing = True
    if not GEMINI_API_KEY:
        logger.critical("CRITICAL (startup check): GEMINI_API_KEY environment variable not set.")
        initial_check_critical_configs_missing = True

    valid_rss_urls_startup = [url for url in RSS_FEED_URLS if url and not (url.startswith("URL_") and url.endswith("_PLACEHOLDER"))]
    if not valid_rss_urls_startup:
        logger.critical("CRITICAL (startup check): RSS_FEED_URLS list is empty or contains only placeholder URLs. No jobs can be fetched.")
        initial_check_critical_configs_missing = True

    if initial_check_critical_configs_missing:
        logger.critical("Exiting due to missing critical configurations detected at startup.")
    else:
        logger.info("Startup checks passed. Running the bot application.")
        asyncio.run(main())

# Placeholder for original send_test_message, if needed for other purposes (not used by scheduler)
# def send_test_message(bot_instance_local, channel_id_local, message_text):
#     try:
#         # This function is synchronous, if called from async code, wrap with asyncio.to_thread
#         bot_instance_local.send_message(chat_id=channel_id_local, text=message_text)
#         logger.info(f"Test message sent to {channel_id_local}: {message_text}")
#     except Exception as e:
#         logger.error(f"Error sending test message: {e}")
