import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def google_search(query, num_results=5):
    """
    Perform a Google Custom Search and return the top `num_results` links.
    
    :param query: Search query string
    :param num_results: Number of results to return (default: 5)
    :return: List of result links
    """
    API_KEY = os.getenv("API_KEY_GOOGLE_CUSTOM_SEARCH")
    SEARCH_ENGINE_ID = os.getenv("SEARCH_ENGINE_ID")

    if not API_KEY or not SEARCH_ENGINE_ID:
        raise ValueError("Missing API key or Search Engine ID in environment variables.")

    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        'q': query,
        'key': API_KEY,
        'cx': SEARCH_ENGINE_ID
    }

    response = requests.get(url, params=params)
    results = response.json()

    if 'items' in results:
        return [results['items'][i]['link'] for i in range(min(num_results, len(results['items'])))]
    else:
        return []
