# Figure inputs

The tracked JSON files describe source categories, palettes, country positions,
and the original country-score snapshot. The original `fair_scores.json` is
retained for history; the exporter does not read it.

The dated EAFO CSV files and `code_mappings.csv` are reference observations used
by the notebook and capacity panels. They are intentionally tracked.

`query_results/` contains generated inputs from the final cell of `main.py`.
It includes the actual graph query results, comparison frames, and FAIR scores
calculated from `sources/metadata.csv`. These files are ignored by Git. Rerun the
notebook to completion after changes; never fill this directory with manuscript
values. The exporter reports a missing-input error if required files are absent.

FAIR bar rows contain a compact `code`, the original `source_id`, and computed
F/A/I/R/TOTAL values. Codes are assigned per country for display within a run;
they do not merge snapshot records or imply persistent dataset identity.
