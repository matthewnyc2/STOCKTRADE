# Binance API for Historical Cryptocurrency Data

This document outlines the process of fetching historical cryptocurrency data from the Binance API, focusing on the `/api/v3/klines` endpoint for OHLCV data.

## `/api/v3/klines` Endpoint

This endpoint provides kline/candlestick data for a specified symbol.

### Parameters

| Name      | Type   | Mandatory | Description                                                                                             |
| --------- | ------ | --------- | ------------------------------------------------------------------------------------------------------- |
| `symbol`    | STRING | YES       | The trading pair, e.g., `BTCUSDT`.                                                                      |
| `interval`  | ENUM   | YES       | The kline interval.                                                                                     |
| `startTime` | LONG   | NO        | The start time in milliseconds.                                                                         |
| `endTime`   | LONG   | NO        | The end time in milliseconds.                                                                           |
| `timeZone`  | STRING | NO        | The timezone. Default is `0` (UTC).                                                                     |
| `limit`     | INT    | NO        | The number of results to return. Default is `500`, maximum is `1000`.                                     |

### Code Example

```python
import requests

BASE_URL = "https://api.binance.com"
symbol = "BTCUSDT"
interval = "1h"
start_time = "1640995200000"  # January 1, 2022
end_time = "1641081599999"    # January 1, 2022, 23:59:59

url = f"{BASE_URL}/api/v3/klines?symbol={symbol}&interval={interval}&startTime={start_time}&endTime={end_time}"

response = requests.get(url)
data = response.json()
print(data)
```

## Supported Intervals

The `interval` parameter supports the following values:

- **Seconds**: `1s`
- **Minutes**: `1m`, `3m`, `5m`, `15m`, `30m`
- **Hours**: `1h`, `2h`, `4h`, `6h`, `8h`, `12h`
- **Days**: `1d`, `3d`
- **Weeks**: `1w`
- **Months**: `1M`

## Time Ranges

- If `startTime` and `endTime` are not provided, the most recent klines are returned.
- `startTime` and `endTime` are always interpreted in UTC, regardless of the `timeZone` parameter.

## Rate Limits

- The `/api/v3/klines` endpoint has a weight of **2**.
- The total weight of all requests is limited per minute. You can find more details in the [Binance API documentation](https://developers.binance.com/docs/binance-spot-api-docs/rest-api/limits).

## Download Limits

- The maximum number of klines returned per request is **1000**.
- If the time range between `startTime` and `endTime` is larger than what can be covered by 1000 klines for the given interval, you will need to make multiple requests to retrieve all the data.
