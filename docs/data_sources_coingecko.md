# CoinGecko API for Historical Cryptocurrency Price Data

## Overview

CoinGecko provides a free and comprehensive API for accessing historical cryptocurrency data, making it a valuable resource for backtesting trading strategies. The API offers a range of endpoints to retrieve detailed market information, including prices, market capitalization, and trading volumes.

**Base URL for the free API**: `https://api.coingecko.com/api/v3`

## Key Endpoints

### 1. `/coins/{id}/market_chart`

This endpoint provides historical market data for a specific coin, including price, market capitalization, and 24-hour volume.

-   **Endpoint**: `GET /coins/{id}/market_chart`
-   **Parameters**:
    -   `id` (required): The coin's unique identifier (e.g., `bitcoin`).
    -   `vs_currency` (required): The currency to compare against (e.g., `usd`).
    -   `days` (required): The number of days of historical data to retrieve.
-   **Returns**: JSON object with three arrays:
    -   `prices`: An array of `[timestamp, price]` pairs.
    -   `market_caps`: An array of `[timestamp, market_cap]` pairs.
    -   `total_volumes`: An array of `[timestamp, volume]` pairs.

-   **Data Granularity**: The interval between data points is determined automatically based on the requested date range:
    -   **1 day**: 5-minute intervals
    -   **2-90 days**: Hourly intervals
    -   **Over 90 days**: Daily intervals (00:00 UTC)

### 2. `/coins/{id}/market_chart/range`

This endpoint allows for fetching historical data within a specific date range using UNIX timestamps.

-   **Endpoint**: `GET /coins/{id}/market_chart/range`
-   **Parameters**:
    -   `id` (required): The coin's unique identifier (e.g., `bitcoin`).
    -   `vs_currency` (required): The currency to compare against (e.g., `usd`).
    -   `from` (required): The start date as a UNIX timestamp.
    -   `to` (required): The end date as a UNIX timestamp.
-   **Returns**: JSON object with three arrays, similar to `/market_chart`.

### 3. `/coins/{id}/ohlc`

This endpoint returns OHLC (Open, High, Low, Close) data for a specific coin, which is essential for candlestick chart analysis.

-   **Endpoint**: `GET /coins/{id}/ohlc`
-   **Parameters**:
    -   `id` (required): The coin's unique identifier (e.g., `bitcoin`).
    -   `vs_currency` (required): The currency for OHLC values (e.g., `usd`).
    -   `days` (required): The number of days of OHLC data to retrieve. Accepts one of the following values: `1`, `7`, `14`, `30`, `90`, `180`, `365`, `max`.
-   **Returns**: An array of arrays, where each inner array contains:
    -   `[timestamp, open, high, low, close]`

-   **Data Granularity**: The interval between data points is determined automatically based on the requested date range:
    -   **1-2 days**: 30-minute intervals
    -   **3-30 days**: 4-hour intervals
    -   **Over 31 days**: 4-day intervals

## Getting OHLCV Data

A key challenge in creating a complete OHLCV (Open, High, Low, Close, Volume) dataset is that the `/coins/{id}/ohlc` and `/coins/{id}/market_chart` endpoints return data at different time intervals (granularities). A simple timestamp alignment is not possible.

To create an accurate OHLCV dataset, you must:
1.  Fetch OHLC data from the `/coins/{id}/ohlc` endpoint.
2.  Fetch volume data from the `/coins/{id}/market_chart` endpoint for the same period.
3.  Resample the volume data to match the OHLC data's time intervals. For example, if the OHLC data is in 4-hour intervals, you must aggregate the hourly volume data into corresponding 4-hour blocks.

## Rate Limits and API Keys

-   **API Key**: The free CoinGecko API (public/demo) does not require an API key.
-   **Rate Limit**: The free tier is limited to approximately **30 calls per minute**. There is no official monthly cap.

This documentation provides a foundational guide for integrating CoinGecko's historical data into a financial analysis and backtesting platform.
