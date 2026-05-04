# Livenode

Livenode is a minimal, hybrid trading bot architecture designed for Alpaca Paper Trading. It leverages the speed and robustness of **C++** for order execution and the flexibility of **Python** for signal generation and strategy logic.

> [!WARNING]
> **Important Disclaimer:** Livenode is purely a demonstration project and should **not** be used for live trading with real capital unless you are an expert and have modified it to meet your specific needs.


## Architecture

- **Python (Signal Engine)**: Streams real-time market data, calculates indicators (SMA Crossover), and sends trade signals.
- **C++ (Execution Engine)**: A high-performance TCP server that validates signals and executes trades via Alpaca's REST API.
- **IPC**: Communication happens over a local TCP socket (localhost:5555) using JSON packets.


## Setup

### 1. Prerequisites
- **Python 3.12+**
- **G++** (supporting C++17)
- **libcurl** (for C++ networking)
- **nlohmann-json** (included in the `include/` folder)

### 2. Installation
Clone the repository and set up the Python environment:
```bash
python3 -m venv venv
venv/bin/pip install -r requirements.txt
```

### 3. Authentication (api.txt)
Livenode requires an `api.txt` file in the **project root** directory to authenticate with Alpaca. 

Create a file named `api.txt` and add your Alpaca Paper Trading credentials in the following format:
```text
API: YOUR_ALPACA_API_KEY
SECRET: YOUR_ALPACA_SECRET_KEY
ENDPOINT: https://paper-api.alpaca.markets/v2
```

### 4. Compilation
Compile the C++ execution engine using the provided Makefile:
```bash
make
```

## Running the Bot

To start the full system, you need to run two processes simultaneously:

1. **Start the Execution Engine**:
   ```bash
   ./livenode_exec
   ```

2. **Start the Signal Engine** (in a new terminal):
   ```bash
   venv/bin/python src/bot.py
   ```

## Testing

You can run a timed integration test to verify the connection between the engines and the Alpaca API:

1. Ensure `./livenode_exec` is running.
2. Run the test script:
   ```bash
   venv/bin/python test.py
   ```
This will open an AAPL position, wait 20 seconds, and then close it automatically.

## Next Steps

- Modify the strategy to suit your needs better


