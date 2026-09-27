"""Generate the committed, output-free Colab notebook from readable cell sources."""
import json
from pathlib import Path


def cell(kind, source):
    result = {"cell_type": kind, "metadata": {}, "source": source.strip() + "\n"}
    if kind == "code":
        result.update(execution_count=None, outputs=[])
    return result


cells = [
cell("markdown", """
# MarketForecast — فولاد / TSETMC
Forecast the next observed traded session's **adjusted official closing price**.
This is retrospective research: backward adjustments use later corporate actions.
Official close (`pClosing`) and last trade (`pDrCotVal`) are different fields.
Run cells in order. A GPU is optional; CPU works. Data is frozen for five years, with a 70/15/15
chronological split. No market performance is claimed until real data and evaluation succeed.
"""),
cell("code", """
from pathlib import Path
import subprocess, sys
REPO_URL = "https://github.com/sina-04/MarketForecast.git"
REPO_REF = "codex/tsetmc-colab"
REPO_DIR = Path("/content/MarketForecast")
if not (REPO_DIR / ".git").exists():
    subprocess.run(["git", "clone", "--branch", REPO_REF, "--single-branch", REPO_URL, str(REPO_DIR)], check=True)
COMMIT = subprocess.check_output(["git", "-C", str(REPO_DIR), "rev-parse", "HEAD"], text=True).strip()
print("Repository commit:", COMMIT)
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r", str(REPO_DIR / "requirements-colab.txt")], check=True)
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "--no-deps", "-e", str(REPO_DIR)], check=True)
"""),
cell("markdown", """
## Storage
By default mount Drive and write under `MyDrive/MarketForecast`. Complete Google's normal authorization
if requested. For a temporary run set `PERSIST_TO_DRIVE=False`, then download the archive before disconnecting.
"""),
cell("code", """
PERSIST_TO_DRIVE = True
if PERSIST_TO_DRIVE:
    from google.colab import drive
    drive.mount("/content/drive")
    ROOT = Path("/content/drive/MyDrive/MarketForecast")
else:
    ROOT = Path("/content/marketforecast_outputs")
ROOT.mkdir(parents=True, exist_ok=True)
from marketforecast.io import read_json, write_json
CONFIG = read_json(REPO_DIR / "configs/default.json")
write_json(ROOT / "source_commit.json", {"commit": COMMIT, "repo": REPO_URL})
print("Output root:", ROOT)
"""),
cell("markdown", "## Implementation checks\nSynthetic test fixtures validate behavior, not market performance."),
cell("code", """
subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=REPO_DIR, check=True)
"""),
cell("markdown", """
## Collect or validate the frozen snapshot
The first capture excludes today's Tehran date. Later runs validate and reuse the snapshot.
If this cell fails, run `marketforecast collect --root artifacts/local` locally and copy the complete
`artifacts/local/data/snapshot` directory to `ROOT/data/snapshot` in Drive. Rerun to verify checksums.
If both routes fail, stop. Do not substitute synthetic data.
"""),
cell("code", """
from marketforecast.data import collect
SNAPSHOT, MANIFEST = collect(ROOT, CONFIG)
print(MANIFEST)
import pandas as pd
from IPython.display import display
raw = pd.read_csv(SNAPSHOT / "raw.csv")
display(raw.head(), raw.tail())
"""),
cell("markdown", """
## Audit, adjust, engineer features, and prepare sequences
Unresolved invalid traded records stop preparation after their quarantine audit is saved.
Do not edit frozen CSVs in place; corrections need a separate documented snapshot.
All window lengths and model comparisons share the same target dates.
"""),
cell("code", """
from marketforecast.workflow import prepare_run
OUTPUT, FRAME, FEATURES, PLAN, MANIFEST, AUDITS = prepare_run(ROOT, CONFIG)
print("Run:", OUTPUT, "Audits:", AUDITS, "Features:", FEATURES)
display(FRAME[["date", "jalali_date", "adj_official_close", "volume"]].tail())
from marketforecast.sequences import prepare
splits, _, _ = prepare(FRAME, FEATURES, CONFIG["default_sequence_length"], PLAN)
for name, split in splits.items():
    print(name, split["X"].shape, split["dates"][0], split["dates"][-1])
FRAME.plot(x="date", y="adj_official_close", figsize=(12, 4), title="Adjusted official close (rial)")
"""),
cell("markdown", """
## Train, select on validation, then evaluate the sealed test period
Six candidates: lengths 10/30/60 × widths 32/64. Dropout 0.2, Adam/MSE, batch 32,
at most 100 epochs, early-stopping patience 10. Best checkpoints persist on Drive.
Completed candidates are reused; interrupted candidates restart from their seed.
Ridge is validation-selected; OHLCV ablation holds the selected architecture constant.
Do not tune parameters after inspecting test results.
"""),
cell("code", """
from marketforecast.workflow import run
OUTPUT = run(ROOT, CONFIG, acquire=False)
display(pd.DataFrame(read_json(OUTPUT / "test_metrics.json")).T)
"""),
cell("markdown", "## Verify saved models and reproduce predictions\nBoth `.keras` and required `.h5` are checked."),
cell("code", """
from marketforecast.workflow import verify_run
print(verify_run(OUTPUT))
from IPython.display import Image, Markdown, display
for filename in ["loss_selected_lstm.png", "loss_ohlcv_lstm.png", "test_forecasts.png", "residuals.png"]:
    display(Image(filename=str(OUTPUT / filename)))
display(Markdown((OUTPUT / "report.md").read_text(encoding="utf-8")))
"""),
cell("markdown", """
## Export
The archive includes snapshot, CSVs, sequences, scalers, checkpoints, models, configuration/environment,
predictions, metrics, figures, and the English report. Drive retains original files.
"""),
cell("code", """
from marketforecast.workflow import export_bundle
BUNDLE = export_bundle(ROOT, OUTPUT)
print("Saved archive:", BUNDLE)
# Optional browser download (especially without Drive):
# from google.colab import files
# files.download(str(BUNDLE))
"""),
]
notebook = {"cells": cells, "metadata": {
    "colab": {"name": "marketforecast_colab.ipynb", "provenance": []},
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python"}}, "nbformat": 4, "nbformat_minor": 5}
for index, entry in enumerate(notebook["cells"]):
    entry["id"] = f"marketforecast-{index:02d}"
path = Path(__file__).resolve().parents[1] / "notebooks" / "marketforecast_colab.ipynb"
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(notebook, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print(path)

