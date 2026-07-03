# Trading Bot — Binance Futures Testnet (USDT-M)

A small, structured Python CLI application that places **Market**, **Limit**,
and (bonus) **Stop-Limit** orders on the Binance USDT-M Futures **Testnet**.

## Project Structure

```
trading_bot/
  bot/
    __init__.py
    client.py         # Binance API client wrapper (testnet-pinned)
    orders.py          # Order placement logic (returns structured results)
    validators.py      # CLI input validation
    logging_config.py  # Shared file + console logger
  cli.py                # CLI entry point (argparse)
  logs/
    trading_bot.log     # Created at runtime — request/response/error log
  requirements.txt
  .env.example
  README.md
```

The code is layered so each file has one job:

- **`validators.py`** — pure functions, no network calls, easy to unit test.
- **`client.py`** — the *only* file that talks to Binance. Wraps
  `python-binance`, pinned to the Futures Testnet base URL
  (`https://testnet.binancefuture.com`), and converts all Binance
  exceptions into a single `BinanceClientError`.
- **`orders.py`** — turns a validated order request into the right
  Binance params (MARKET / LIMIT / STOP) and returns a structured
  `OrderResult` — it never raises, so the CLI can always print a clean
  success/failure message.
- **`cli.py`** — argument parsing, wiring the layers together, printing
  output. No Binance-specific logic lives here.

## 1. Setup

### 1.1 Create a Testnet account & API keys

1. Go to **https://testnet.binancefuture.com** and log in (GitHub account).
2. Open the **API Key** panel and generate a key/secret pair.
3. The testnet account is pre-funded with fake USDT for paper trading.

### 1.2 Install dependencies

```bash
cd trading_bot
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 1.3 Configure credentials

```bash
cp .env.example .env
# then edit .env and paste your testnet API key/secret
```

Credentials are read from environment variables
(`BINANCE_TESTNET_API_KEY`, `BINANCE_TESTNET_API_SECRET`) via
`python-dotenv`, so nothing sensitive is hard-coded or committed
(`.env` is git-ignored).

## 2. Running the bot

### Market order

```bash
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01
```

### Limit order

```bash
python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.01 --price 45000
```

### Bonus: Stop-Limit order

```bash
python cli.py --symbol BTCUSDT --side SELL --type STOP_LIMIT \
  --quantity 0.01 --price 44000 --stop-price 44500
```

### Verbose mode (debug-level console output)

```bash
python cli.py --symbol ETHUSDT --side BUY --type MARKET --quantity 0.05 -v
```

### Sample output

```
--- Order Request ---
  Symbol     : BTCUSDT
  Side       : BUY
  Type       : MARKET
  Quantity   : 0.01
  Price      : -
  Stop Price : -

--- Order Response ---
  Order ID     : 12345678
  Status       : FILLED
  Executed Qty : 0.01
  Avg Price    : 60123.40

[SUCCESS] Order placed successfully.
```

On failure (bad input, rejected order, or network issue) the bot prints
`[FAILED] ...` with a human-readable reason and logs the full detail
(including stack trace, where applicable) to `logs/trading_bot.log`.

## 3. Logging

Every run appends to `logs/trading_bot.log`:

- the outgoing request (endpoint + parameters)
- the raw Binance response
- any validation, API, or network errors (with context)

The console only shows INFO-level summaries by default (`-v` for more).
Log files rotate at 2 MB (5 backups kept) so they don't grow unbounded.

## 4. Error handling covered

- **Invalid input**: unknown symbol format, invalid side/type, non-numeric
  or non-positive quantity/price, missing price for LIMIT/STOP_LIMIT,
  missing stop-price for STOP_LIMIT — all caught in `validators.py`
  before any network call is made.
- **API errors**: Binance rejects the order (e.g. insufficient testnet
  balance, invalid symbol, min-notional not met) — caught as
  `BinanceAPIException`, wrapped, logged, and reported cleanly.
- **Network failures**: timeouts / connection errors — caught and
  reported without a raw traceback shown to the user.

## 5. Assumptions

- Only **USDT-M Futures** are targeted (not Coin-M or Spot).
- LIMIT orders use `timeInForce=GTC` (Good-Til-Cancelled); this isn't
  exposed as a CLI flag to keep the required arguments minimal, but
  it's straightforward to add.
- The bonus **Stop-Limit** order is implemented via Binance's `STOP`
  futures order type (triggers a limit order at `price` once the market
  touches `stopPrice`).
- Quantity/price precision (tick size / step size) is assumed to be
  handled by the values the user supplies; `client.get_symbol_info()`
  is provided as a hook for stricter pre-flight validation against
  exchange filters if desired.
- Positions are opened in **one-way mode** (Binance testnet default);
  hedge-mode `positionSide` is not set.

## 6. Deliverable logs

`logs/trading_bot.log` in this repo includes one MARKET and one LIMIT
order run as required by the task deliverables. Re-running the commands
in Section 2 with your own API keys will append fresh entries.
