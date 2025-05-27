# gemini_processor.py
# This script processes raw job data using the Gemini API.
# Note: This script requires the 'google-generativeai' library.
# Install it using: pip install google-generativeai

import google.generativeai as genai
import json # For parsing JSON responses
import logging

# Placeholder for your Gemini API Key
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"

# Initialize logger for this module
logger = logging.getLogger(__name__)

# Flag to ensure Gemini is configured only once
gemini_configured = False

def configure_gemini():
    """
    Configures the google.generativeai library with the API key.
    Should be called once.
    """
    global gemini_configured
    if GEMINI_API_KEY == "YOUR_GEMINI_API_KEY":
        logger.error("GEMINI_API_KEY is not set. Please replace 'YOUR_GEMINI_API_KEY' with your actual key.")
        return False
    if not gemini_configured:
        try:
            genai.configure(api_key=GEMINI_API_KEY)
            gemini_configured = True
            logger.info("Gemini API configured successfully.")
            return True
        except Exception as e:
            logger.error(f"Error configuring Gemini API: {e}")
            return False
    return True # Already configured

def process_job_with_gemini(raw_job_data):
    """
    Processes raw job data using the Gemini API to extract and structure information.

    Args:
        raw_job_data (dict): A dictionary containing raw job data with keys like
                             'title', 'link', 'summary', 'published_date', 'source_feed'.

    Returns:
        dict: A dictionary containing processed job information (job_title, company_name,
              location, summary, url, hashtags) or None if processing fails.
    """
    if not gemini_configured:
        logger.error("Gemini API not configured. Call configure_gemini() first for optimal operation.")
        # Attempt to configure if not done, as a safeguard, though explicit call is preferred.
        if not configure_gemini():
             logger.error("Automatic Gemini configuration failed during processing attempt.")
             return None

    model = genai.GenerativeModel('gemini-pro')

    # Constructing the input string from raw_job_data
    input_text = (
        f"Title: {raw_job_data.get('title', 'N/A')}\n"
        f"Summary: {raw_job_data.get('summary', 'N/A')}\n"
        f"Link: {raw_job_data.get('link', 'N/A')}\n"
        f"Published Date: {raw_job_data.get('published_date', 'N/A')}"
    )

    prompt = f"""
    You are a helpful assistant that processes job postings.
    Based on the following job data:

    {input_text}

    Extract the following information and return it as a JSON object:
    1.  "job_title": The official job title.
    2.  "company_name": The name of the company hiring. If not explicitly mentioned, try to infer or state "Unknown".
    3.  "location": Determine if the job is remote. If not remote, list city and state if available. If ambiguous, state "Not specified".
    4.  "summary": A concise and engaging summary (around 2-3 sentences) focusing on key responsibilities and unique benefits if available in the input.
    5.  "url": The original job URL from the input.
    6.  "hashtags": Generate 3-4 relevant hashtags (e.g., #job #career #hiring #[JobTitle] #[Industry]). This should be a list of strings.

    Example of expected JSON output format:
    {{
        "job_title": "Software Engineer",
        "company_name": "Tech Solutions Inc.",
        "location": "Remote",
        "summary": "Join our innovative team to develop cutting-edge software. Key responsibilities include coding, testing, and deployment in an agile environment. Enjoy competitive salary and remote work flexibility.",
        "url": "http://example.com/job/123",
        "hashtags": ["#SoftwareEngineer", "#TechJobs", "#RemoteWork", "#Hiring"]
    }}

    Ensure the output is a valid JSON object.
    """

    try:
        logger.info(f"Sending request to Gemini API for job: {raw_job_data.get('title', 'N/A')}")
        response = model.generate_content(prompt)
        
        # Attempt to parse the response as JSON
        # Gemini's response might have markdown ```json ... ```, so we need to clean it.
        response_text = response.text
        if response_text.strip().startswith("```json"):
            response_text = response_text.strip()[7:-3].strip() # Remove ```json and ```
        elif response_text.strip().startswith("```"): # Fallback for just ```
             response_text = response_text.strip()[3:-3].strip()


        processed_data = json.loads(response_text)
        
        # Ensure all expected keys are present, providing defaults if not
        expected_keys = ["job_title", "company_name", "location", "summary", "url", "hashtags"]
        for key in expected_keys:
            if key not in processed_data:
                processed_data[key] = "N/A" if key != "hashtags" else []
        
        # Specifically ensure 'url' is from the original raw_job_data if not accurately returned
        if 'link' in raw_job_data and processed_data.get('url') != raw_job_data['link']:
             logger.warning(f"Gemini returned URL '{processed_data.get('url')}' differs from original '{raw_job_data['link']}'. Using original link for job '{raw_job_data.get('title', 'N/A')}'.")
             processed_data['url'] = raw_job_data['link']


        logger.info(f"Successfully processed job data with Gemini for: {raw_job_data.get('title', 'N/A')}")
        return processed_data
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from Gemini response for job '{raw_job_data.get('title', 'N/A')}': {e}")
        if 'response' in locals() and hasattr(response, 'text'):
            logger.error(f"Raw Gemini response text was: {response.text}")
        else:
            logger.error("No response object or text available to log.")
        return None
    except Exception as e:
        logger.error(f"Error calling Gemini API for job '{raw_job_data.get('title', 'N/A')}': {e}")
        return None

if __name__ == '__main__':
    # Basic logging setup for direct script execution
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    logger.info("Gemini Processor script - for testing.")

    # This is a placeholder for how you might use the functions.
    # Ensure GEMINI_API_KEY is set above before running.
    
    # 1. Configure Gemini (ideally once at the start of your application)
    # configure_gemini() # Called within process_job_with_gemini if not already, but explicit is good.

    # 2. Sample raw job data (similar to output from rss_sourcing.py)
    sample_raw_job = {
        'title': 'Senior Python Developer (Remote)',
        'link': 'https://example.com/job/python-developer-123',
        'summary': 'We are seeking an experienced Python Developer to join our distributed team. Responsibilities include developing and maintaining web applications, working with various APIs, and contributing to our microservices architecture. Experience with Django/Flask and cloud platforms is a plus. Offering flexible work hours.',
        'published_date': '2023-10-26T10:00:00Z',
        'source_feed': 'http://example.com/rss'
    }
    
    logger.info(f"Sample Raw Job Data:\n{json.dumps(sample_raw_job, indent=2)}")

    # 3. Process the job data
    # Note: configure_gemini() will be called by process_job_with_gemini if not already.
    # However, you need to replace "YOUR_GEMINI_API_KEY" with a real key for actual API calls.
    if GEMINI_API_KEY != "YOUR_GEMINI_API_KEY":
        if configure_gemini(): # Ensure configuration is successful
            processed_job_info = process_job_with_gemini(sample_raw_job)
            if processed_job_info:
                logger.info(f"Processed Job Information (from Gemini):\n{json.dumps(processed_job_info, indent=2)}")
            else:
                logger.warning("Failed to process job information with Gemini.")
        else:
            logger.error("Skipping processing due to Gemini configuration failure.")
    else:
        logger.warning("SKIPPING GEMINI CALL: GEMINI_API_KEY is not set in the script.")
        logger.warning("To test, replace 'YOUR_GEMINI_API_KEY' with your actual key in the script or environment.")

    # Example of a job with less information
    sample_raw_job_minimal = {
        'title': 'Frontend Dev',
        'link': 'https://example.com/job/frontend-dev-456',
        'summary': 'Looking for a frontend dev. React needed.',
        'published_date': '2023-10-25',
        'source_feed': 'http://another.example.com/rss'
    }
    logger.info(f"Sample Minimal Raw Job Data:\n{json.dumps(sample_raw_job_minimal, indent=2)}")
    if GEMINI_API_KEY != "YOUR_GEMINI_API_KEY":
        if gemini_configured: # Check if already configured from previous call
             processed_job_info_minimal = process_job_with_gemini(sample_raw_job_minimal)
             if processed_job_info_minimal:
                 logger.info(f"Processed Minimal Job Information (from Gemini):\n{json.dumps(processed_job_info_minimal, indent=2)}")
             else:
                 logger.warning("Failed to process minimal job information with Gemini.")
        # else: # Not configured, and previous attempt might have failed or key not set.
        #    logger.warning("Skipping minimal job processing, Gemini not configured.")
    else: # Key not set, so this test won't run with actual API
        logger.info("Skipping minimal job processing with Gemini as API key is not set.")


    logger.info("Gemini Processor script test finished.")
