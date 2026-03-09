import pytest
from app.services import alpha_vantage_client
from app.schemas.security import SecurityQuote
from unittest.mock import patch, MagicMock

def test_get_quote_caching(app, monkeypatch):
    """Test that Alpha Vantage quotes are cached and not refetched within the timeout."""
    with app.app_context():
        ticker = "AAPL"
        
        # Mock responses for OVERVIEW and GLOBAL_QUOTE
        overview_resp = MagicMock()
        overview_resp.status_code = 200
        overview_resp.json.return_value = {"Name": "Apple Inc."}
        
        quote_resp = MagicMock()
        quote_resp.status_code = 200
        quote_resp.json.return_value = {
            "Global Quote": {
                "01. symbol": ticker,
                "05. price": "150.00",
                "07. latest trading day": "2026-03-08"
            }
        }
        
        def side_effect(url, params=None):
            if params.get("function") == "OVERVIEW":
                return overview_resp
            if params.get("function") == "GLOBAL_QUOTE":
                return quote_resp
            return MagicMock(status_code=404)

        with patch("requests.get", side_effect=side_effect) as mock_get:
            # First call
            quote1 = alpha_vantage_client.get_quote(ticker)
            assert quote1 is not None
            assert quote1.ticker == ticker
            assert quote1.issuer == "Apple Inc."
            assert mock_get.call_count == 2 # OVERVIEW + GLOBAL_QUOTE
            
            # Second call - both should be cached
            quote2 = alpha_vantage_client.get_quote(ticker)
            assert quote2 is not None
            assert mock_get.call_count == 2

def test_get_company_name_caching(app, monkeypatch):
    """Test that company names are cached."""
    with app.app_context():
        ticker = "MSFT"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"Name": "Microsoft Corporation"}
        
        with patch("requests.get", return_value=mock_response) as mock_get:
            # First call
            name1 = alpha_vantage_client.get_company_name(ticker)
            assert name1 == "Microsoft Corporation"
            assert mock_get.call_count == 1
            
            # Second call
            name2 = alpha_vantage_client.get_company_name(ticker)
            assert name2 == "Microsoft Corporation"
            assert mock_get.call_count == 1

def test_get_quote_api_failure(app, monkeypatch):
    """Test behavior when API returns an error or empty data."""
    with app.app_context():
        ticker = "INVALID"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"Error Message": "Invalid API call"}
        
        with patch("requests.get", return_value=mock_response):
            quote = alpha_vantage_client.get_quote(ticker)
            assert quote is None
