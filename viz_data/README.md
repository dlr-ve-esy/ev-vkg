# Context for these files

These files are hardcoded in this repository because I do not expect to change them, these are needed for some of the viz work.


## fair_scores.json

Country-level FAIR scores generated from the final `sources/metadata.csv`
with the scoring heuristics implemented in the `main.py` notebook
(Findability, Accessibility, Interoperability, Reusability). Per country
the record with the earliest publication date is selected; for Germany
this is the BNetZA register (de.2), the dataset used in the paper's
quantitative comparison. No code reads this file at runtime; regenerate
it by re-running the FAIR scoring cells of `main.py` against the final
metadata.
