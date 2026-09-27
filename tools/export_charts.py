"""Re-render a completed run at 600 DPI, with vector PDF/SVG exports; no retraining."""
import argparse
from pathlib import Path

import pandas as pd

from marketforecast.evaluation import history_plot, plots
from marketforecast.io import read_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    output = args.output or args.run
    selected = read_json(args.run / "model_metadata.json")["selected"]["name"]
    histories = {
        "selected_lstm": read_json(args.run / "candidates" / selected / "history.json"),
        "ohlcv_lstm": read_json(args.run / "candidates/ohlcv/history.json"),
    }
    plots(output, pd.read_csv(args.run / "test_predictions.csv"), histories)
    history_plot(output, pd.read_csv(args.run / "features.csv"))
    print(f"Exported five charts as 600-DPI PNG, PDF, and SVG: {output}")


if __name__ == "__main__":
    main()
