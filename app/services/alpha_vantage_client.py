import json
from dataclasses import dataclass
from urllib.parse import urlencode
from urllib.request import urlopen

from flask import current_app

from app.cache import cache


@dataclass
class SecurityQuote:
    ticker: str
    date: str
    price: float
    issuer: str


def _get_api_key() -> str:
    key = current_app.config.get('ALPHA_VANTAGE_API_KEY')
    if not key:
        raise ValueError('Alpha Vantage API key is not configured')
    return key


def _http_get_json(params: dict) -> dict:
    url = f"https://www.alphavantage.co/query?{urlencode(params)}"
    with urlopen(url, timeout=10) as resp:
        return json.loads(resp.read().decode('utf-8'))


def get_company_name(ticker: str) -> str | None:
    cache_key = f'company_name:{ticker.upper()}'
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    params = {'function': 'OVERVIEW', 'symbol': ticker.upper(), 'apikey': _get_api_key()}
    data = _http_get_json(params)
    issuer = data.get('Name')
    cache.set(cache_key, issuer, timeout=3600)
    return issuer


def get_price_data(ticker: str) -> dict | None:
    cache_key = f'price_data:{ticker.upper()}'
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    params = {'function': 'TIME_SERIES_DAILY', 'symbol': ticker.upper(), 'apikey': _get_api_key()}
    data = _http_get_json(params)
    series = data.get('Time Series (Daily)')
    if not series:
        cache.set(cache_key, None, timeout=300)
        return None

    latest_date = sorted(series.keys(), reverse=True)[0]
    day = series[latest_date]
    out = {
        'date': latest_date,
        'open': float(day['1. open']),
        'high': float(day['2. high']),
        'low': float(day['3. low']),
        'close': float(day['4. close']),
        'volume': int(day['5. volume']),
    }
    cache.set(cache_key, out, timeout=300)
    return out


def get_quote(ticker: str) -> SecurityQuote | None:
    issuer = get_company_name(ticker)
    price_data = get_price_data(ticker)
    if not issuer or not price_data:
        return None
    return SecurityQuote(
        ticker=ticker.upper(),
        date=price_data['date'],
        price=price_data['close'],
        issuer=issuer,
    )
