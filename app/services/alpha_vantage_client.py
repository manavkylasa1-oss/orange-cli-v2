import requests
from flask import current_app

from app.cache import cache
from app.schemas.security import SecurityQuote

BASE_URL = 'https://www.alphavantage.co/query'


def _get_api_key() -> str:
    """Retrieve the Alpha Vantage API key from the application configuration."""
    return current_app.config.get('ALPHAVANTAGE_API_KEY', '')


def get_company_name(ticker: str) -> str | None:
    """
    Queries the Alpha Vantage API for the company overview to get the issuer name.
    """
    cache_key = f'company_name:{ticker}'
    cached_val = cache.get(cache_key)
    if cached_val is not None:
        return cached_val

    # API call
    params = {
        'function': 'OVERVIEW',
        'symbol': ticker,
        'apikey': _get_api_key(),
    }
    response = requests.get(BASE_URL, params=params)
    if response.status_code == 200:
        data = response.json()
        print(f"DEBUG: get_company_name data: {data}")
        if 'Name' in data:
            name = data['Name']
            cache.set(cache_key, name)
            return name
        return None
    return None


def get_price_data(ticker: str) -> dict | None:
    """
    Retrieves the most recent available price data.
    """
    cache_key = f'price_data:{ticker}'
    cached_val = cache.get(cache_key)
    if cached_val is not None:
        return cached_val

    params = {
        'function': 'GLOBAL_QUOTE',
        'symbol': ticker,
        'apikey': _get_api_key(),
    }
    response = requests.get(BASE_URL, params=params)
    if response.status_code == 200:
        data = response.json()
        print(f"DEBUG: get_price_data data: {data}")
        if 'Global Quote' in data and data['Global Quote']:
            quote = data['Global Quote']
            cache.set(cache_key, quote)
            return quote
        return None
    return None


def get_quote(ticker: str) -> SecurityQuote | None:
    """
    Returns a SecurityQuote dataclass instance, or None if the ticker cannot be resolved.
    """
    company_name = get_company_name(ticker)
    if not company_name:
        return None
        
    price_data = get_price_data(ticker)
    if not price_data:
        return None
        
    # '05. price' format -> dict key
    price_str = price_data.get('05. price')
    date_str = price_data.get('07. latest trading day')
    
    if not price_str or not date_str:
        return None
        
    try:
        price = float(price_str)
    except ValueError:
        return None

    return SecurityQuote(
        ticker=ticker,
        date=date_str,
        price=price,
        issuer=company_name
    )
