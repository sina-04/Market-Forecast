"""Build an output-free hourly notebook and a checksum-protected local-source input ZIP."""
import json
from pathlib import Path
import subprocess
import zipfile

from marketforecast.io import checksum, write_json
from marketforecast.data import validate_snapshot

ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "artifacts/foolad_hourly_20261005"
DEST = EXPERIMENT / "colab"
DEST.mkdir(parents=True, exist_ok=True)
validate_snapshot(EXPERIMENT / "data/snapshot")
FILES = [*ROOT.glob("src/marketforecast/*.py"), *ROOT.glob("tests/*.py"),
         *ROOT.glob("notebooks/marketforecast*colab.ipynb"),
         ROOT / "pyproject.toml", ROOT / "requirements-colab.txt", *ROOT.glob("configs/*.json"),
         *ROOT.glob("artifacts/foolad_hourly_20261005/data/snapshot/*")]
commit = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
provenance = DEST / "source_commit.json"
write_json(provenance, {"commit": commit, "working_tree_changes_included": True,
                        "source_basis": "Exact local source files in checksum-protected input bundle; commit alone is insufficient"})



def cell(kind, source, index):
    result = {"cell_type": kind, "metadata": {}, "id": f"hourly-{index}", "source": source.strip()+"\n"}
    if kind == "code":
        result.update(execution_count=None, outputs=[])
    return result


bootstrap = '''
from pathlib import Path
import hashlib, json, shutil, subprocess, sys, zipfile
from google.colab import files
gpu = subprocess.check_output(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"], text=True)
print("GPU:", gpu, flush=True)
assert "A100" in gpu, "Select Runtime > Change runtime type > A100 GPU before running"
INPUT = Path("/content/foolad_hourly_training_input.zip")
if not INPUT.exists():
    files.upload()
assert INPUT.exists(), "Upload foolad_hourly_training_input.zip built by tools/build_hourly_colab.py"
WORK = Path("/content/MarketForecastHourly")
WORK.mkdir(exist_ok=True)
with zipfile.ZipFile(INPUT) as archive:
    for item in archive.infolist():
        target = (WORK/item.filename).resolve()
        assert target.is_relative_to(WORK.resolve()), "Unsafe archive member"
        assert not item.filename.startswith("/") and ".." not in Path(item.filename).parts
    archive.extractall(WORK)
for name, expected in json.loads((WORK/"input_checksums.json").read_text()).items():
    assert hashlib.sha256((WORK/name).read_bytes()).hexdigest() == expected, name
print("Exact local source + frozen hourly snapshot verified", flush=True)
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r", str(WORK/"requirements-colab.txt")], check=True)
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "--no-deps", "-e", str(WORK)], check=True)
sys.path.insert(0, str(WORK/"src"))
test_result = subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=WORK, capture_output=True, text=True)
print(test_result.stdout, test_result.stderr, flush=True)
assert test_result.returncode == 0, "Pre-training tests failed; inspect captured output"
from marketforecast.io import read_json, write_json
from marketforecast.workflow import prepare_run, run, verify_run, export_bundle
from marketforecast.evaluation import history_plot
import pandas as pd
from IPython.display import display, Markdown, Image
ROOT = WORK/"artifacts/foolad_hourly_20261005"
CONFIG = read_json(WORK/"configs/hourly.json")
shutil.copy2(WORK/"source_commit.json", ROOT/"source_commit.json")
OUTPUT, FRAME, FEATURES, PLAN, MANIFEST, AUDITS = prepare_run(ROOT, CONFIG)
print("Audits:", AUDITS, flush=True)
print("Training/validation/test targets:", PLAN.train_end, PLAN.validation_end-PLAN.train_end, len(PLAN.target_positions)-PLAN.validation_end, flush=True)
history_plot(OUTPUT, FRAME)
OUTPUT = run(ROOT, CONFIG, acquire=False)
verification = verify_run(OUTPUT)
write_json(OUTPUT/"fresh_kernel_verification.json", verification)
print("Reload verification:", verification, flush=True)
display(pd.DataFrame(read_json(OUTPUT/"test_metrics.json")).T)
display(Markdown((OUTPUT/"report.md").read_text()))
BUNDLE = export_bundle(ROOT, OUTPUT)
print("RESULT_BUNDLE", BUNDLE, "SHA256", hashlib.sha256(BUNDLE.read_bytes()).hexdigest(), flush=True)
files.download(str(BUNDLE))
'''
cells = [cell("markdown", """
# MarketForecast — hourly Foolad / A100
Predict the next observed traded hourly bar's adjusted last price. Full timestamps, daily corporate-action
basis, indicators restarted at known missing dates, training-only scalers, 70/15/15 chronological common targets.
Six validation-selected LSTMs (12/24/60 bars × 32/64 units), persistence, Ridge and OHLCV comparisons.
Log-return learning with price reconstruction. More bars do not guarantee lower errors.
Use Runtime → Change runtime type → **A100 GPU**. Build the exact local source/snapshot input ZIP using
`python tools/build_hourly_colab.py`, then run the cell and choose `foolad_hourly_training_input.zip`.
Outputs remain in this runtime and are downloaded as a verified results ZIP; download before disconnecting.
""", 0), cell("code", bootstrap, 1), cell("code", '''
for name in ["adjusted_close_history.png", "loss_selected_lstm.png", "test_forecasts.png", "residuals.png"]:
    display(Image(filename=str(OUTPUT/name), width=1000))
''', 2)]
notebook = {"cells": cells, "metadata": {"colab": {"name": "marketforecast_hourly_colab.ipynb", "provenance": []},
           "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
           "language_info": {"name": "python"}, "accelerator": "GPU"}, "nbformat": 4, "nbformat_minor": 5}
(ROOT/"notebooks/marketforecast_hourly_colab.ipynb").write_text(json.dumps(notebook, indent=1, ensure_ascii=False)+"\n", encoding="utf-8")
(DEST/"bootstrap.py").write_text(bootstrap.strip()+"\n", encoding="utf-8")
bundle_hashes = {str(p.relative_to(ROOT)).replace("\\", "/"): checksum(p) for p in FILES}
bundle_hashes["source_commit.json"] = checksum(provenance)
archive_path = DEST / "foolad_hourly_training_input.zip"
with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as archive:
    for path in FILES:
        archive.write(path, str(path.relative_to(ROOT)).replace("\\", "/"))
    archive.write(provenance, "source_commit.json")
    archive.writestr("input_checksums.json", json.dumps(bundle_hashes, indent=2))
print(archive_path, archive_path.stat().st_size)
