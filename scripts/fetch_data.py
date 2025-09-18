from __future__ import annotations
import argparse
from pathlib import Path


def parse_args():
    p = argparse.ArgumentParser(description="Fetch historical OHLCV CSVs via yfinance")
    p.add_argument("--symbols", required=True, help="Comma-separated tickers, e.g., TQQQ,SPXL")
    p.add_argument("--from", dest="from_", required=True, help="Start date YYYY-MM-DD")
    p.add_argument("--to", required=True, help="End date YYYY-MM-DD (exclusive or inclusive per provider)")
    p.add_argument("--interval", default="1d", help="Bar interval: 1d, 1h, 5m, etc.")
    p.add_argument("--out", default="data", help="Output directory for CSVs")
    return p.parse_args()


def main():
    args = parse_args()
    syms = [s.strip() for s in args.symbols.split(",") if s.strip()]
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        import yfinance as yf
    except ImportError as e:
        raise SystemExit("yfinance not installed. Run: pip install -r requirements-data.txt") from e

    for sym in syms:
        print(f"[fetch] {sym} {args.from_}..{args.to} interval={args.interval}")
        t = yf.Ticker(sym)
        df = t.history(start=args.from_, end=args.to, interval=args.interval, auto_adjust=False)
        if df.empty:
            print(f"[warn] no data for {sym}")
            continue
        df.index.name = "Date"
        df = df.reset_index()
        # Ensure canonical columns
        cols = [
            c if c in ("Date",) else c.title().replace(" ", "")
            for c in df.columns
        ]
        df.columns = cols
        path = out_dir / f"{sym}.csv"
        df.to_csv(path, index=False)
        print(f"[ok] wrote {path}")


if __name__ == "__main__":
    main()

