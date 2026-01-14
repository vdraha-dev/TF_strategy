# TODO - Task List and Fixes

## 🟡 Important Improvements

### 4. Missing Error Handling in Trader

**Problem**: Insufficient error handling for:
- Failed order placement
- Network issues
- Insufficient balance
- Validation errors

**Solution**:
- Add try-catch blocks in `create_strategy_worker` method
- Add retry logic for transient errors
- Log all errors with sufficient context
- Add notification system (email/telegram) for critical errors

**Priority**: 🟡 Medium  
**File**: `tf_strategy/trader.py`

### 5. Missing Non-OCO Order Support

**Problem**: Line 262 has a comment about OCO emulation:
```python
# if connector is not support oco orders
# need close opposite order manually
# or emulate oco order in connector         <-- prefer this option
```

**Solution**:
- Add `supports_oco: bool` flag to `ConnectorBase`
- Implement OCO emulation through separate orders and tracking
- Add automatic closing of opposite order when one is triggered

**Priority**: 🟡 Medium  
**File**: `tf_strategy/common/base.py`, `tf_strategy/binance/wrapper.py`

### 6. Improve Logging System

**Problem**: Current logging configuration is basic and doesn't include:
- Log file rotation
- Different log levels for different modules
- Structured logging (JSON format)

**Solution**:
- Update `logging_config.yaml` to add file handlers
- Add log rotation (by size/time)
- Consider using `structlog` for structured logging

**Priority**: 🟡 Medium  
**File**: `logging_config.yaml`

## 🟢 Features and Enhancements

### 7. Add Backtesting Module

**Description**: Create module for backtesting strategies on historical data

**Tasks**:
- Use `vectorbt` for fast backtesting
- Add performance metrics (Sharpe ratio, max drawdown, win rate)
- Create results visualization
- Add parameter optimization

**Priority**: 🟢 Low  
**New module**: `tf_strategy/backtest/`

### 8. Add More Strategies

**Description**: Expand the set of available strategies

**Ideas**:
- Mean Reversion
- Breakout Strategy
- Grid Trading
- DCA (Dollar Cost Averaging)

**Priority**: 🟢 Low  
**Files**: `tf_strategy/strategy/`

### 9. Web Dashboard

**Description**: Create web interface for monitoring

**Features**:
- Display current positions
- Balance and P&L charts
- Strategy configuration
- Logs and trading history

**Technologies**: FastAPI + React/Vue  
**Priority**: 🟢 Low

### 10. Add Support for Other Exchanges

**Description**: Abstract logic to support different exchanges

**Exchanges**:
- Bybit
- OKX
- KuCoin

**Priority**: 🟢 Low  
**Files**: Create new modules like `tf_strategy/bybit/`

## 📝 Documentation

### 11. Improve Documentation

**Tasks**:
- [ ] Add more usage examples
- [ ] Create API documentation (Sphinx/MkDocs)
- [ ] Add architecture diagrams
- [ ] Write deployment guide
- [ ] Add troubleshooting section

**Priority**: 🟡 Medium

### 12. Add Strategy Examples

**Tasks**:
- [ ] Create `examples/` directory
- [ ] Add notebooks with examples
- [ ] Add examples for different timeframes
- [ ] Show integration with external data sources

**Priority**: 🟢 Low

## 🧪 Testing

### 13. Increase Test Coverage

**Current state**: Only basic tests exist

**Tasks**:
- [ ] Add unit tests for all indicators
- [ ] Add tests for Trader class
- [ ] Add mock tests for API calls
- [ ] Achieve 80%+ code coverage

**Priority**: 🟡 Medium  
**Files**: `tests/`

### 14. CI/CD Pipeline

**Tasks**:
- [ ] Setup GitHub Actions
- [ ] Automatic test runs on PR
- [ ] Automatic code formatting checks
- [ ] Automatic PyPI publishing (optional)

**Priority**: 🟡 Medium

## 🔧 Technical Debt

### 15. Refactor BinanceWrapper

**Problem**: `BinanceWrapper` class is quite large with many responsibilities

**Solution**:
- Split into separate classes for REST and WS operations
- Extract state update logic into separate class
- Improve connection lifecycle management

**Priority**: 🟢 Low  
**File**: `tf_strategy/binance/wrapper.py`

### 16. Type Hints

**Tasks**:
- [ ] Add complete type hints to all functions
- [ ] Setup mypy for type checking
- [ ] Fix all type hint errors

**Priority**: 🟢 Low

### 17. Performance Optimization

**Tasks**:
- [ ] Profile code to find bottlenecks
- [ ] Optimize indicator calculations
- [ ] Consider using Cython for critical sections
- [ ] Add caching for frequently used data

**Priority**: 🟢 Low

## 📦 Infrastructure

### 18. Docker Support

**Tasks**:
- [ ] Create Dockerfile
- [ ] Add docker-compose.yml
- [ ] Add Docker deployment instructions

**Priority**: 🟡 Medium

### 19. Monitoring and Alerts

**Tasks**:
- [ ] Integration with Prometheus/Grafana
- [ ] Add health check endpoints
- [ ] Setup alerts (Telegram/Email/SMS)
- [ ] Add performance metrics

**Priority**: 🟡 Medium