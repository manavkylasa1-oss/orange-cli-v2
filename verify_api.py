import os
import sys
import time
from flask import Flask

# Add the project root to sys.path
project_root = '/Users/mk/.gemini/antigravity/scratch/orange-cli-v2'
sys.path.insert(0, project_root)

from app.config import DevelopmentConfig
from app.cache import cache
from app import create_app
from app.services import alpha_vantage_client

def test_live_alpha_vantage():
    app = create_app(DevelopmentConfig)
    with app.app_context():
        ticker = "AAPL"
        print(f"--- Testing Live Alpha Vantage for {ticker} ---")
        
        # Test 1: Fetch Quote
        print("Fetching quote...")
        quote = alpha_vantage_client.get_quote(ticker)
        if quote:
            print(f"SUCCESS: {quote.ticker} ({quote.issuer}) price: {quote.price}")
        else:
            print("FAILURE: Could not fetch quote.")
            # Note: Overviews are often the first thing to fail if rate limited.
            
        print("\nWaiting 2 seconds to avoid rate limits...")
        time.sleep(2)

        # Test 2: Verify Cache
        print("\nVerifying cache...")
        cached_quote = cache.get(f'quote:{ticker}')
        if cached_quote:
            print(f"SUCCESS: Found quote for {ticker} in cache.")
        else:
            print("FAILURE: Quote not found in cache.")

        # Test 3: Fetch Company Name
        print("\nFetching company name...")
        name = alpha_vantage_client.get_company_name(ticker)
        if name:
            print(f"SUCCESS: {ticker} name is: {name}")
        else:
            print("FAILURE: Could not fetch company name.")

if __name__ == "__main__":
    test_live_alpha_vantage()
