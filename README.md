# TF Strategy

Implementation of the Trend Following trading strategy for Binance.

## Description

TF Strategy is a Python framework for automated trading on the Binance cryptocurrency exchange using the Trend Following strategy. The project includes a complete set of tools for working with Binance REST API and WebSocket connections, implementation of technical indicators, and a position management system.

## Key Features

- ✅ Full Binance API integration (REST + WebSocket)
- ✅ Trend Following strategy implementation
- ✅ Technical indicators: EMA, RSI, ADX
- ✅ Order management (Market, Limit, OCO)
- ✅ Real-time balance tracking
- ✅ Asynchronous architecture

## Tech Stack

- **Python**: 3.14+
- **Main libraries**:
  - `httpx` - asynchronous HTTP requests
  - `websockets` - WebSocket connections
  - `pydantic` - data validation
  - `numba` - computation acceleration
  - `pandas` / `numpy` - data processing
  - `vectorbt` - backtesting

## Installation

```bash
# Clone repository
git clone https://github.com/your-username/tf-strategy.git
cd tf-strategy

# Install dependencies (recommended to use uv)
uv sync

# Or with pip
pip install -e .
```

## Configuration

1. Create a `.env` file in the root directory:

```env
# Binance API
BINANCE_API_KEY=your_api_key
BINANCE_PRIVATE_KEY_PATH=/path/to/private_key.pem

# URLs
BINANCE_PUBLIC_REST_URL=https://api.binance.com
BINANCE_PRIVATE_REST_URL=https://api.binance.com
BINANCE_PUBLIC_WS_URL=wss://stream.binance.com:9443/ws
BINANCE_PRIVATE_WS_URL=wss://ws-api.binance.com:443/ws-api/v3
```

2. Generate RSA keys for Binance API (if using RSA signature):

```bash
# Generate private key
openssl genrsa -out private_key.pem 2048

# Generate public key
openssl rsa -in private_key.pem -pubout -out public_key.pem
```

## Usage

### Basic Example

```python
import asyncio
from tf_strategy.binance.wrapper import BinanceWrapper
from tf_strategy.common.schemas import ConnectorConfig, Symbol
from tf_strategy.common.enums import TimeInterval
from tf_strategy.common.tools import load_private_key_from_pep

async def main():
    # Configuration
    config = ConnectorConfig(
        public_rest_url="https://api.binance.com",
        private_rest_url="https://api.binance.com",
        public_ws_url="wss://stream.binance.com:9443/ws",
        private_ws_url="wss://ws-api.binance.com:443/ws-api/v3",
        api_key="your_api_key",
        private_key=load_private_key_from_pep("path/to/private_key.pem")
    )
    
    # Initialization
    connector = BinanceWrapper(config)
    await connector.start()
    
    # Get historical data
    symbol = Symbol(first="BTC", second="USDC")
    candles = await connector.get_historical_candles(
        symbol=symbol,
        interval=TimeInterval._1h,
        limit=100
    )
    
    # Get balance
    wallet = await connector.wallet()
    print(f"Balance: {wallet.balance}")
    
    await connector.stop()

asyncio.run(main())
```

### Using Strategy

```python
import pandas as pd
from tf_strategy.strategy.trend_following import TrendFollowing

# Prepare data
df = pd.DataFrame({
    'open': [...],
    'high': [...],
    'low': [...],
    'close': [...],
    'volume': [...]
})

# Initialize strategy
strategy = TrendFollowing(params={
    'fast_period': 20,
    'slow_period': 50,
    'rsi_period': 14,
    'adx_period': 20,
    'adx_strength': 25,
    'rsi_overbought': 70,
    'rsi_oversold': 30
})

# Get signals
strategy.update_batch(df)
signals = strategy.signals

# Check last signal
last_signal = strategy.get_last_signal()
# 1 = open position, -1 = close position, 0 = do nothing
```

## Project Structure

```
tf_strategy/
├── binance/              # Binance integration
│   ├── rest/            # REST API clients
│   ├── ws/              # WebSocket clients
│   ├── schemas.py       # Binance data schemas
│   ├── tools.py         # Helper functions
│   └── wrapper.py       # High-level interface
├── common/              # Common components
│   ├── connection/      # WebSocket listener
│   ├── async_event.py   # Event system
│   ├── base.py          # Base abstractions
│   ├── enums.py         # Enumerations
│   ├── schemas.py       # Common schemas
│   └── tools.py         # Utilities
├── strategy/            # Trading strategies
│   ├── signals/         # Technical indicators
│   │   ├── adx.py      # Average Directional Index
│   │   ├── ema.py      # Exponential Moving Average
│   │   ├── rsi.py      # Relative Strength Index
│   │   └── sma.py      # Simple Moving Average
│   ├── base.py         # Base strategy class
│   ├── tools.py        # Helper functions
│   └── trend_following.py  # Trend Following strategy
└── trader.py           # Trade execution system
```

## Testing

```bash
# All tests
pytest

# Only unit tests (without integration)
pytest -m "not integration"

# Integration tests (require Binance API access)
pytest -m integration

# With coverage
pytest --cov=tf_strategy
```

## Development

### Code Formatting

```bash
# Auto-format
make format

# Check
make lint
```

### Pre-commit Hooks

The project uses `black` and `ruff` to maintain code quality.

## Examples

See more detailed usage examples in the `tests/` directory:
- `tests/binance/public_rest_test.py` - working with public API
- `tests/binance/tools_test.py` - using utilities
- `tests/common/schemas_test.py` - working with schemas

## License

MIT License - see [LICENSE](LICENSE) file

## Disclaimer

⚠️ **IMPORTANT**: This project is for educational purposes only. Cryptocurrency trading carries high risks. The authors are not responsible for any financial losses resulting from the use of this software.

Always:
- Test on testnet before using real funds
- Use small amounts for initial tests
- Understand the risks of automated trading
- Don't invest more than you can afford to lose