# rss_sourcing.py
# This script fetches and parses job data from RSS feeds.
# Note: This script requires the 'feedparser' library.
# Install it using: pip install feedparser

import feedparser
import logging

# Initialize logger for this module
logger = logging.getLogger(__name__)

# Placeholder list for RSS feed URLs
# RSS_FEED_URLS = [
# "URL_1_PLACEHOLDER",
# "URL_2_PLACEHOLDER"
    # Add more RSS feed URLs here
# ]

def fetch_and_parse_rss(feed_url):
    """
    Fetches and parses an RSS feed, extracting job data.

    Args:
        feed_url (str): The URL of the RSS feed.

    Returns:
        list: A list of dictionaries, where each dictionary contains
              job data (title, link, published_date, summary) for an entry.
              Returns an empty list if the feed URL is a placeholder,
              if parsing fails, or if there are no entries.
    """
    if feed_url.startswith("URL_") and feed_url.endswith("_PLACEHOLDER"):
        logger.info(f"Skipping placeholder URL: {feed_url}")
        return []

    logger.info(f"Fetching and parsing RSS feed: {feed_url}")
    try:
        feed = feedparser.parse(feed_url)
    except Exception as e:
        logger.error(f"Exception during feedparser.parse for URL {feed_url}: {e}")
        return []


    # Check for parsing errors
    if feed.bozo:
        # feed.bozo_exception can be a string or an exception object
        bozo_reason = feed.bozo_exception
        if isinstance(feed.bozo_exception, Exception):
            bozo_reason = str(feed.bozo_exception)
        logger.warning(f"Error parsing feed {feed_url}: {bozo_reason}")
        return []

    if not feed.entries:
        logger.info(f"No entries found in feed: {feed_url}")
        return []

    jobs_list = []
    for entry in feed.entries:
        # Attempt to extract common fields for job postings
        title = entry.get('title', 'N/A')
        link = entry.get('link', 'N/A')
        # Handle different possible date fields
        published_date = entry.get('published', entry.get('updated', 'N/A'))
        # Handle different possible summary/description fields
        summary = entry.get('summary', entry.get('description', 'N/A'))

        job_data = {
            'title': title,
            'link': link,
            'published_date': published_date,
            'summary': summary,
            'source_feed': feed_url
        }
        jobs_list.append(job_data)

    logger.info(f"Successfully parsed {len(jobs_list)} entries from {feed_url}")
    return jobs_list

def get_jobs_from_all_feeds(rss_feed_urls):
    """
    Iterates through the provided list of RSS feed URLs, fetches job data from each,
    and aggregates the results.

    Args:
        rss_feed_urls (list): A list of RSS feed URLs to process.

    Returns:
        list: A list of all job data dictionaries fetched from the feeds.
              Returns an empty list if no valid URLs are provided or no jobs are found.
    """
    all_jobs_data = []
    if not rss_feed_urls or all(url.startswith("URL_") and url.endswith("_PLACEHOLDER") for url in rss_feed_urls):
        logger.warning("No actual RSS feed URLs provided to get_jobs_from_all_feeds. Please provide a list of valid RSS feed URLs.")
        # Log example format only if it's truly an example, not actual data.
        # logger.info("Example of job data format (if there were jobs): {'title': 'Sample Job Title', ...}")
        return [] # Return empty list if no valid URLs

    for url in rss_feed_urls:
        if not url or (isinstance(url, str) and url.strip() == ""):
            logger.warning("Empty or invalid URL string provided in the list. Skipping.")
            continue
        jobs_from_feed = fetch_and_parse_rss(url)
        all_jobs_data.extend(jobs_from_feed)

    if all_jobs_data:
        logger.info(f"Total jobs fetched from all feeds: {len(all_jobs_data)}")
        # Printing all jobs can be very verbose for a log, consider summarizing or removing for production.
        # For debugging, one might log a few:
        # for i, job in enumerate(all_jobs_data[:3]): # Log first 3 jobs for example
        # logger.debug(f"Sample fetched job {i+1}: {job}")
    else:
        logger.info("No job data fetched from any of the provided RSS feeds.")
    return all_jobs_data # Return the list, even if empty

if __name__ == '__main__':
    # Basic logging setup for direct script execution
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')

    # Define some example URLs for direct script execution if needed for testing.
    EXAMPLE_RSS_FEEDS = [
        # "http://feeds.feedburner.com/PythonJobs?format=xml", # Example live feed
        "URL_1_PLACEHOLDER", 
        "URL_2_PLACEHOLDER",
        "" # Example of an invalid URL entry
    ]
    logger.info("Starting RSS feed fetching process (direct script execution)...")
    
    # Filter out placeholder URLs for direct testing unless they are the only ones
    active_test_feeds = [url for url in EXAMPLE_RSS_FEEDS if not (url.startswith("URL_") and url.endswith("_PLACEHOLDER")) and url]

    if not active_test_feeds and any(EXAMPLE_RSS_FEEDS): # If only placeholders or empty strings, mention it.
        logger.warning("No actual example RSS feeds configured for direct execution, or only placeholders/empty strings found.")
        logger.warning("Please update EXAMPLE_RSS_FEEDS in rss_sourcing.py with real URLs for direct testing.")
        # Optionally, run with placeholders to test that logic:
        # fetched_jobs = get_jobs_from_all_feeds(EXAMPLE_RSS_FEEDS)
        # logger.info(f"Process finished using placeholders. Total jobs fetched: {len(fetched_jobs)}")
    elif not active_test_feeds: # All URLs were empty or placeholders
        logger.info("No valid RSS feeds to process for direct testing.")
    else:
        logger.info(f"Using active test feeds for direct execution: {active_test_feeds}")
        fetched_jobs = get_jobs_from_all_feeds(active_test_feeds)
        logger.info(f"Direct execution process finished. Total jobs fetched: {len(fetched_jobs)}")
        if fetched_jobs: # Log some details of fetched jobs if any
            for i, job in enumerate(fetched_jobs[:2]): # Log first 2 jobs
                 logger.info(f"Sample fetched job {i+1} - Title: {job.get('title', 'N/A')}, Link: {job.get('link', 'N/A')}")


    logger.info("RSS feed fetching script (direct execution) finished.")
