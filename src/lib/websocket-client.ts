import { MarketDataUpdate } from '@/types/market';

type MessageCallback = (data: MarketDataUpdate) => void;
type ConnectionStateCallback = (state: ConnectionState) => void;

export interface ConnectionState {
  isConnected: boolean;
  error: Error | null;
}

const RECONNECT_DELAY = 5000; // 5 seconds
const MAX_RECONNECT_ATTEMPTS = 10;

class WebSocketClient {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectAttempts = 0;
  private subscriptions: Map<string, Set<MessageCallback>> = new Map();
  private connectionState: ConnectionState = { isConnected: false, error: null };
  private connectionStateListeners: Set<ConnectionStateCallback> = new Set();

  constructor(url: string) {
    this.url = url;
  }

  public connect(): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      return;
    }

    this.ws = new WebSocket(this.url);

    this.ws.onopen = this.handleOpen;
    this.ws.onmessage = this.handleMessage;
    this.ws.onerror = this.handleError;
    this.ws.onclose = this.handleClose;
  }

  public subscribe(symbol: string, callback: MessageCallback): void {
    if (!this.subscriptions.has(symbol)) {
      this.subscriptions.set(symbol, new Set());
    }
    this.subscriptions.get(symbol)?.add(callback);

    if (this.ws?.readyState === WebSocket.OPEN) {
      this.sendSubscription(symbol);
    }
  }

  public unsubscribe(symbol: string, callback: MessageCallback): void {
    const symbolSubscriptions = this.subscriptions.get(symbol);
    if (symbolSubscriptions) {
      symbolSubscriptions.delete(callback);
      if (symbolSubscriptions.size === 0) {
        this.subscriptions.delete(symbol);
        if (this.ws?.readyState === WebSocket.OPEN) {
          this.sendUnsubscription(symbol);
        }
      }
    }
  }

  public addConnectionStateListener(callback: ConnectionStateCallback): void {
    this.connectionStateListeners.add(callback);
    callback(this.connectionState);
  }

  public removeConnectionStateListener(callback: ConnectionStateCallback): void {
    this.connectionStateListeners.delete(callback);
  }

  public close(): void {
    this.ws?.close();
  }

  private updateConnectionState(newState: Partial<ConnectionState>): void {
    this.connectionState = { ...this.connectionState, ...newState };
    this.connectionStateListeners.forEach(callback => callback(this.connectionState));
  }

  private handleOpen = (): void => {
    console.log('WebSocket connected');
    this.reconnectAttempts = 0;
    this.updateConnectionState({ isConnected: true, error: null });
    this.resubscribeToAll();
  };

  private handleMessage = (event: MessageEvent): void => {
    try {
      const data: MarketDataUpdate = JSON.parse(event.data);
      const symbolSubscriptions = this.subscriptions.get(data.symbol);
      if (symbolSubscriptions) {
        symbolSubscriptions.forEach(callback => callback(data));
      }
    } catch (error) {
      console.error('Error parsing WebSocket message:', error);
    }
  };

  private handleError = (event: Event): void => {
    console.error('WebSocket error:', event);
    this.updateConnectionState({ isConnected: false, error: new Error('WebSocket error occurred') });
  };

  private handleClose = (): void => {
    console.log('WebSocket disconnected');
    this.updateConnectionState({ isConnected: false, error: null });
    if (this.reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
      this.reconnectAttempts++;
      setTimeout(() => this.connect(), RECONNECT_DELAY);
    } else {
      console.error('Max WebSocket reconnect attempts reached');
    }
  };

  private sendSubscription(symbol: string): void {
    this.ws?.send(JSON.stringify({ action: 'subscribe', symbol }));
  }

  private sendUnsubscription(symbol: string): void {
    this.ws?.send(JSON.stringify({ action: 'unsubscribe', symbol }));
  }

  private resubscribeToAll(): void {
    this.subscriptions.forEach((_, symbol) => {
      this.sendSubscription(symbol);
    });
  }
}

const websocketUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws/market';
export const webSocketClient = new WebSocketClient(websocketUrl);
