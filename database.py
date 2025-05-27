# database.py
# This script manages a SQLite database to prevent duplicate job postings.

import sqlite3
import logging

# Database file name
DB_NAME = 'job_channel.db'

# Initialize logger for this module
logger = logging.getLogger(__name__)

def initialize_db():
    """
    Initializes the SQLite database and creates the 'posted_jobs' table if it doesn't exist.
    The 'posted_jobs' table uses 'job_url' as its PRIMARY KEY to ensure uniqueness.
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS posted_jobs (
                job_url TEXT PRIMARY KEY
            )
        ''')
        conn.commit()
        logger.info(f"Database '{DB_NAME}' initialized successfully.")
        logger.info("Table 'posted_jobs' created or already exists with column: job_url (TEXT PRIMARY KEY).")
    except sqlite3.Error as e:
        logger.error(f"Error initializing database '{DB_NAME}': {e}")
    finally:
        if conn:
            conn.close()

def add_job_posted(job_url):
    """
    Adds a job URL to the 'posted_jobs' table.

    Args:
        job_url (str): The unique URL of the job to add.

    Returns:
        bool: True if the job URL was successfully added, False otherwise.
    """
    if not job_url:
        logger.warning("Attempted to add an empty or None job URL.")
        return False
        
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO posted_jobs (job_url) VALUES (?)", (job_url,))
        conn.commit()
        logger.info(f"Successfully added job URL to database: {job_url}")
        return True
    except sqlite3.IntegrityError:
        # This error occurs if the job_url (PRIMARY KEY) already exists.
        logger.info(f"Job URL already exists in database (or other integrity error): {job_url}")
        return False # Not an error, but a failed precondition for adding.
    except sqlite3.Error as e:
        logger.error(f"Database error adding job URL '{job_url}': {e}")
        return False
    finally:
        if conn:
            conn.close()

def is_job_posted(job_url):
    """
    Checks if a job URL already exists in the 'posted_jobs' table.

    Args:
        job_url (str): The job URL to check.

    Returns:
        bool: True if the job URL exists, False otherwise.
    """
    if not job_url:
        logger.warning("Attempted to check an empty or None job URL.")
        return False # Or raise ValueError, depending on desired strictness

    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM posted_jobs WHERE job_url = ?", (job_url,))
        exists = cursor.fetchone() is not None
        # Optional: log if found or not for debugging, but can be verbose
        # logger.debug(f"Checked for job URL '{job_url}', found: {exists}")
        return exists
    except sqlite3.Error as e:
        logger.error(f"Database error checking job URL '{job_url}': {e}")
        return False # Return False in case of error to prevent potential re-posting
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    # Basic logging setup for direct script execution
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    logger.info("Starting database script demonstration...")

    # 1. Initialize the database and table
    initialize_db()

    logger.info("--- Testing Database Operations ---")

    # Sample job URLs
    sample_url_1 = "http://example.com/job/123"
    sample_url_2 = "http://example.com/job/456"
    sample_url_3 = "http://example.com/job/789" # For later testing

    # 2. Demonstrate adding new job URLs
    logger.info(f"Attempting to add '{sample_url_1}'...")
    add_job_posted(sample_url_1)

    logger.info(f"Attempting to add '{sample_url_2}'...")
    add_job_posted(sample_url_2)

    # 3. Demonstrate checking if URLs exist
    logger.info(f"Is '{sample_url_1}' posted? {is_job_posted(sample_url_1)}")
    logger.info(f"Is '{sample_url_2}' posted? {is_job_posted(sample_url_2)}")
    logger.info(f"Is '{sample_url_3}' (not yet added) posted? {is_job_posted(sample_url_3)}")

    # 4. Demonstrate trying to add a duplicate URL
    logger.info(f"Attempting to add duplicate URL '{sample_url_1}' again...")
    add_job_posted(sample_url_1) # This should result in an "already exists" log

    # Verify it wasn't added again (or rather, that the check still works as expected)
    logger.info(f"Is '{sample_url_1}' still posted? {is_job_posted(sample_url_1)}")

    # 5. Demonstrate checking before adding (preferred way to handle duplicates)
    logger.info(f"Checking '{sample_url_3}' before attempting to add...")
    if not is_job_posted(sample_url_3):
        logger.info(f"'{sample_url_3}' is not posted. Adding it now.")
        add_job_posted(sample_url_3)
        logger.info(f"Is '{sample_url_3}' posted now? {is_job_posted(sample_url_3)}")
    else:
        logger.info(f"'{sample_url_3}' was already posted. No action taken.")
        
    # Test with an empty URL
    logger.info("--- Testing Edge Cases ---")
    logger.info("Attempting to add an empty URL:")
    add_job_posted("")
    logger.info("Attempting to check an empty URL:")
    is_job_posted("")


    logger.info("Database script demonstration finished.")
