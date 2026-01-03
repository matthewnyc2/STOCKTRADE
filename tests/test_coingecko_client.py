import pytest
from unittest.mock import MagicMock
from services.data_sources.coingecko import CoinGeckoAPI

@pytest.fixture
def mock_client():
    """Provides a mocked httpx client."""
    return MagicMock()

def test_ping(mock_client):
    """Tests if the CoinGecko API is reachable."""
    mock_response = MagicMock()
    mock_response.json.return_value = {'gecko_says': '(V3) To the Moon!'}
    mock_client.get.return_value = mock_response

    client = CoinGeckoAPI(client=mock_client)
    response = client.ping()

    assert response['gecko_says'] == '(V3) To the Moon!'
    mock_client.get.assert_called_once_with('https://api.coingecko.com/api/v3/ping')

def test_get_price(mock_client):
    """Tests fetching the price of a cryptocurrency."""
    mock_response = MagicMock()
    mock_response.json.return_value = {'bitcoin': {'usd': 60000}}
    mock_client.get.return_value = mock_response

    client = CoinGeckoAPI(client=mock_client)
    response = client.get_price('bitcoin', 'usd')

    assert 'bitcoin' in response
    assert 'usd' in response['bitcoin']
    assert response['bitcoin']['usd'] == 60000
    mock_client.get.assert_called_once_with(
        'https://api.coingecko.com/api/v3/simple/price',
        params={'ids': 'bitcoin', 'vs_currencies': 'usd'}
    )
