# TradeGuard Risk Engine Demo

TradeGuard is a demonstration of a pre-trade risk engine that fuses a high-performance Python orchestration layer with a declarative **Prolog** compliance rulebase.

It evaluates synthetic `TradeTickets`, validates them against complex `MarketStates` using fuzzy logic models, and cleanly isolates business rules (e.g., restricted macro sessions, hard asset leverage limits, tier-based exposure caps) into logical rules rather than nested `if/then` statements.

## Project Architecture

1. **Python Domain Models**: `tradeguard/core/models.py` strict typed representations of trades.
2. **Prolog Knowledge Base**: `tradeguard/knowledge_base/rules.pl` contains declarative rules.
3. **Prolog Bridge**: `tradeguard/engine/bridge.py` dynamically interfaces with the SWI-Prolog engine using `PySwip`.
4. **Fuzzifier**: `tradeguard/engine/fuzzifier.py` bridges continuous float limits (e.g. spread) into logical fuzzy buckets (e.g `wide`, `tight`) for Prolog evaluation.

## Prerequisites

Because this project uses `PySwip`, **you must install SWI-Prolog** on your operating system and ensure its binaries are on your PATH.

- [SWI-Prolog Download Page](https://www.swi-prolog.org/download/stable)

## Installation

1. Create a Python virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # Or `venv\Scripts\activate` on Windows
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Demo

Run the main application to start continuously simulating and evaluating trades. Output will print to standard output (with colors) and be fully serialized into `./audit_log.txt`.

```bash
# Run infinitely with a 1-second interval
python main.py

# Run exactly 10 iterations with a 0.5 sec sleep
python main.py --iterations 10 --interval 0.5
```

## Running Tests

An extensive test suite using `pytest` verifies the Prolog engine integrations and business rule logic. 

```bash
python -m pytest tests/
```

## Development & Code Quality

Linters and static-typing checks are provided via `ruff` and `mypy`:

```bash
ruff check .
ruff format .
mypy .
```
