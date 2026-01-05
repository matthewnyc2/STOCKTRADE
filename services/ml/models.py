"""
LSTM Model Implementation (Pure NumPy - No PyTorch Dependency).

Provides lightweight LSTM implementation for time series prediction.
"""

import numpy as np
import numpy.typing as npt
from typing import Any, Optional


class LSTMLayer:
    """
    Single LSTM layer implementation using NumPy.

    Uses simplified LSTM cell with gates:
    - Forget gate: What to discard from cell state
    - Input gate: What to write to cell state
    - Output gate: What to output from cell state
    """

    def __init__(
        self,
        input_size: int,
        hidden_size: int,
    ):
        """
        Initialize LSTM layer.

        Args:
            input_size: Number of input features
            hidden_size: Number of hidden units
        """
        self.input_size = input_size
        self.hidden_size = hidden_size

        # Combined weights for efficiency
        # W: [input_size, 4 * hidden_size]
        # U: [hidden_size, 4 * hidden_size]
        # b: [4 * hidden_size]

        # Xavier initialization
        limit = np.sqrt(6 / (input_size + hidden_size))

        self.W = np.random.uniform(-limit, limit, (input_size, 4 * hidden_size))
        self.U = np.random.uniform(-limit, limit, (hidden_size, 4 * hidden_size))
        self.b = np.zeros((4 * hidden_size,))

        # Gradients
        self.dW = np.zeros_like(self.W)
        self.dU = np.zeros_like(self.U)
        self.db = np.zeros_like(self.b)

        # Cache for backprop
        self.cache: dict[str, npt.NDArray[np.float64]] = {}

    def forward(
        self,
        x: npt.NDArray[np.float64],
        h_prev: Optional[npt.NDArray[np.float64]] = None,
        c_prev: Optional[npt.NDArray[np.float64]] = None,
    ) -> tuple[npt.NDArray[np.float64], npt.NDArray[np.float64]]:
        """
        Forward pass through LSTM layer.

        Args:
            x: Input sequence [seq_len, input_size]
            h_prev: Initial hidden state [hidden_size]
            c_prev: Initial cell state [hidden_size]

        Returns:
            h: Hidden states [seq_len, hidden_size]
            c: Cell states [seq_len, hidden_size]
        """
        seq_len = x.shape[0]

        # Initialize states
        if h_prev is None:
            h_prev = np.zeros((self.hidden_size,))
        if c_prev is None:
            c_prev = np.zeros((self.hidden_size,))

        h = np.zeros((seq_len, self.hidden_size))
        c = np.zeros((seq_len, self.hidden_size))

        # Store for backprop
        self.cache["x"] = x
        self.cache["h"] = h
        self.cache["c"] = c

        for t in range(seq_len):
            # Combined gates calculation
            gates_t = np.dot(x[t], self.W) + np.dot(h_prev, self.U) + self.b

            # Split into gates
            i_t = self._sigmoid(gates_t[: self.hidden_size])  # Input gate
            f_t = self._sigmoid(gates_t[self.hidden_size : 2 * self.hidden_size])  # Forget gate
            o_t = self._sigmoid(gates_t[2 * self.hidden_size : 3 * self.hidden_size])  # Output gate
            g_t = np.tanh(gates_t[3 * self.hidden_size :])  # Cell candidate

            # Update cell state and hidden state
            c[t] = f_t * c_prev + i_t * g_t
            h[t] = o_t * np.tanh(c[t])

            # Update previous states
            h_prev = h[t]
            c_prev = c[t]

        return h, c

    def _sigmoid(self, x: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
        """Sigmoid activation function."""
        return 1 / (1 + np.exp(-np.clip(x, -500, 500)))

    def _tanh(self, x: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
        """Tanh activation function."""
        return np.tanh(x)

    def get_params(self) -> list[npt.NDArray[np.float64]]:
        """Get model parameters."""
        return [self.W, self.U, self.b]

    def set_params(self, params: list[npt.NDArray[np.float64]]) -> None:
        """Set model parameters."""
        self.W, self.U, self.b = params


class LSTMModel:
    """
    Complete LSTM model for time series prediction.

    Architecture:
    - Input layer
    - LSTM layers (stackable)
    - Dense output layer
    """

    def __init__(
        self,
        input_size: int,
        hidden_sizes: list[int],
        output_size: int = 1,
        dropout: float = 0.0,
    ):
        """
        Initialize LSTM model.

        Args:
            input_size: Number of input features
            hidden_sizes: List of hidden layer sizes
            output_size: Number of output units
            dropout: Dropout rate
        """
        self.input_size = input_size
        self.hidden_sizes = hidden_sizes
        self.output_size = output_size
        self.dropout = dropout

        # Build LSTM layers
        self.lstm_layers: list[LSTMLayer] = []

        # First LSTM layer
        self.lstm_layers.append(LSTMLayer(input_size, hidden_sizes[0]))

        # Additional LSTM layers
        for i in range(1, len(hidden_sizes)):
            self.lstm_layers.append(LSTMLayer(hidden_sizes[i - 1], hidden_sizes[i]))

        # Output layer (dense)
        # Use Xavier initialization
        limit = np.sqrt(6 / (hidden_sizes[-1] + output_size))
        self.W_out = np.random.uniform(-limit, limit, (hidden_sizes[-1], output_size))
        self.b_out = np.zeros((output_size,))

        # Training state
        self.is_training = True
        self.best_params: dict[str, Any] = {}

    def forward(
        self,
        x: npt.NDArray[np.float64],
    ) -> npt.NDArray[np.float64]:
        """
        Forward pass.

        Args:
            x: Input batch [batch_size, seq_len, input_size]

        Returns:
            predictions: Model outputs [batch_size, output_size]
        """
        batch_size = x.shape[0]

        predictions = np.zeros((batch_size, self.output_size))

        for i in range(batch_size):
            h_seq = x[i]

            # Pass through LSTM layers
            for lstm in self.lstm_layers:
                h_seq, _ = lstm.forward(h_seq)

            # Use last hidden state for prediction
            last_hidden = h_seq[-1]

            # Apply dropout during training
            if self.is_training and self.dropout > 0:
                mask = (np.random.random(last_hidden.shape) > self.dropout).astype(np.float64)
                last_hidden = last_hidden * mask / (1 - self.dropout)

            # Output layer
            predictions[i] = np.dot(last_hidden, self.W_out) + self.b_out

        return predictions

    def predict(
        self,
        x: npt.NDArray[np.float64],
    ) -> npt.NDArray[np.float64]:
        """
        Make prediction (sets eval mode).

        Args:
            x: Input batch

        Returns:
            Predictions
        """
        self.is_training = False
        output = self.forward(x)
        self.is_training = True
        return output

    def save_best(self) -> None:
        """Save current parameters as best."""
        params = [lstm.get_params() for lstm in self.lstm_layers]
        self.best_params = {
            "lstm_layers": params,
            "W_out": self.W_out.copy(),
            "b_out": self.b_out.copy(),
        }

    def load_best(self) -> None:
        """Load best parameters."""
        if self.best_params:
            for lstm, params in zip(self.lstm_layers, self.best_params["lstm_layers"]):
                lstm.set_params(params)
            self.W_out = self.best_params["W_out"].copy()
            self.b_out = self.best_params["b_out"].copy()

    def get_num_params(self) -> int:
        """Get total number of parameters."""
        count = 0
        for lstm in self.lstm_layers:
            for p in lstm.get_params():
                count += p.size
        count += self.W_out.size + self.b_out.size
        return count
