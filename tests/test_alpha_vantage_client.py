from app.cache import cache
from app.services import alpha_vantage_client as av


def test_get_company_name_and_cache(app, monkeypatch):
    calls = {'n': 0}

    def fake_http(_params):
        calls['n'] += 1
        return {'Name': 'Apple Inc.'}

    with app.app_context():
        cache.clear()
        monkeypatch.setattr(av, '_http_get_json', fake_http)
        assert av.get_company_name('AAPL') == 'Apple Inc.'
        assert av.get_company_name('AAPL') == 'Apple Inc.'
        assert calls['n'] == 1


def test_get_price_data_and_none(app, monkeypatch):
    with app.app_context():
        cache.clear()
        monkeypatch.setattr(
            av,
            '_http_get_json',
            lambda _params: {
                'Time Series (Daily)': {
                    '2026-01-01': {
                        '1. open': '1',
                        '2. high': '2',
                        '3. low': '0.5',
                        '4. close': '1.5',
                        '5. volume': '10',
                    }
                }
            },
        )
        out = av.get_price_data('AAPL')
        assert out['close'] == 1.5

        cache.clear()
        monkeypatch.setattr(av, '_http_get_json', lambda _params: {})
        assert av.get_price_data('BAD') is None
