# Implementation and execution status

Acquisition, preparation, Colab training, model selection, evaluation, artifact verification, and reporting
are implemented. Live execution evidence is recorded here after verification.
Synthetic fixtures check behavior only; real-data deliverables require a successful `completion.json`.

## Data access checks — 2026-09-27

- Direct HTTPS TSETMC CDN search: connection timed out locally and in Colab.
- Installed and inspected `pytse-client` 0.19.1 and upstream source.
- Bundled فولاد identity: company فولاد مبارکه اصفهان, index `46348559193224090`, ISIN `IRO1FOLD0001`.
- Its legacy export at `old.tsetmc.com/tsev2/data/Export-txt.aspx` timed out over both HTTP and HTTPS,
  locally and in Colab. No real historical CSV or successful research snapshot was produced.
- `tools/download_pytse.py` preserves original successful HTTP responses, metadata, and CSVs, with bounded
  retries. Use `requirements-pytse.txt` in an isolated acquisition environment because its older
  `jdatetime` dependency conflicts with the pinned training environment.
- In unadjusted pytse-client output, `adjClose` means official closing price and `close` means last trade.
  A download must be validated/imported before research training can begin.
- The current Colab runtime uses Python 3.13. Training requirements now select TensorFlow 2.20 there,
  while retaining TensorFlow 2.19.1 for Python 3.11/3.12.

Next empirical prerequisite: a real, source-documented five-year فولاد history from a reachable network
or an unchanged user-supplied TSETMC export. No synthetic performance is presented as a market result.

