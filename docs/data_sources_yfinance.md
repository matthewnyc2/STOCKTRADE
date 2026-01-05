# Yahoo Finance API (yfinance)

This document provides an overview of the Python `yfinance` library, which is a popular tool for accessing historical stock and cryptocurrency data from the Yahoo Finance API.

## 1. Python yfinance Library Capabilities

The `yfinance` library provides a simple and Pythonic way to access the vast amount of financial data available on Yahoo Finance. Its key capabilities include:

*   **Historical Market Data:** Download historical market data for stocks, ETFs, and cryptocurrencies as Pandas DataFrames.
*   **Ticker Information:** Access a wealth of information for a specific ticker, including:
    *   Company information (e.g., name, sector, industry)
    *   Financial statements (income statement, balance sheet, cash flow)
    *   Analyst recommendations
    *   Insider transactions
    *   And much more.
*   **Multiple Tickers:** Download data for multiple tickers at once.
*   **Intraday Data:** Download intraday data with intervals as low as one minute.
*   **Options Data:** Fetch options data, including calls and puts.
*   **News:** Retrieve recent news articles for a given ticker.

## 2. download() Method Parameters for Historical Data

The `yfinance.download()` function is the primary method for downloading historical market data. Here are the most important parameters:

*   `tickers`: A string or list of strings representing the ticker symbols to download (e.g., "MSFT" or ["MSFT", "AAPL", "GOOG"]).
*   `period`: The period of time to download data for. Valid periods are: `1d`, `5d`, `1mo`, `3mo`, `6mo`, `1y`, `2y`, `5y`, `10y`, `ytd`, `max`.
*   `start` and `end`: The start and end dates for the data download in "YYYY-MM-DD" format.
*   `interval`: The data interval. Valid intervals are: `1m`, `2m`, `5m`, `15m`, `30m`, `60m`, `90m`, `1h`, `1d`, `5d`, `1wk`, `1mo`, `3mo`.
*   `actions`: A boolean that, when set to `True`, downloads dividend and stock split data.
*   `auto_adjust`: A boolean that, when set to `True`, automatically adjusts the OHLC data for splits and dividends.

## 3. Available Data Types (OHLCV, Dividends, Splits)

The `yfinance` library can return the following data types:

*   **OHLCV:** Open, High, Low, Close, and Volume data for the specified interval. This is the default data returned by the `download()` method.
*   **Dividends:** The dividend amount per share for a given date. This data is available when the `actions` parameter is set to `True`.
*   **Stock Splits:** The split ratio for a given date. This data is also available when the `actions` parameter is set to `True`.

## 4. Rate Limiting and Best Practices

While the Yahoo Finance API does not have official, published rate limits, it is important to be aware of the following best practices to avoid being temporarily banned:

*   **Be Respectful:** Do not make an excessive number of requests in a short period. Space out your requests to avoid overwhelming the API.
*   **Use a Session Object:** The `yfinance` library allows you to pass a `requests.Session` object to the `download()` function. This will reuse the underlying TCP connection, which is more efficient and less likely to trigger rate limiting.
*   **Cache Your Data:** Cache the results of your API calls to avoid re-fetching the same data. This is especially important for historical data, which is unlikely to change.
*   **Implement Error Handling:** Implement robust error handling in your code to catch any API errors or IP bans. If you are banned, you will need to wait a period of time before you can make requests again.
