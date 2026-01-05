import { useState, useEffect } from 'react';
import { webSocketClient, ConnectionState } from '@/lib/websocket-client';
import { MarketDataUpdate } from '@/types/market';

export function useMarketData(symbol: string) {
  const [prices, setPrices] = useState<MarketDataUpdate[]>([]);
  const [connectionState, setConnectionState] = useState<ConnectionState>({
    isConnected: false,
    error: null,
  });

  useEffect(() => {
    webSocketClient.connect();

    const handleConnectionStateUpdate = (state: ConnectionState) => {
      setConnectionState(state);
    };
    webSocketClient.addConnectionStateListener(handleConnectionStateUpdate);

    const handlePriceUpdate = (data: MarketDataUpdate) => {
      if (data.symbol === symbol) {
        setPrices(prevPrices => [...prevPrices, data]);
      }
    };
    webSocketClient.subscribe(symbol, handlePriceUpdate);

    return () => {
      webSocketClient.unsubscribe(symbol, handlePriceUpdate);
      webSocketClient.removeConnectionStateListener(handleConnectionStateUpdate);
    };
  }, [symbol]);

  return {
    prices,
    isConnected: connectionState.isConnected,
    error: connectionState.error,
  };
}
