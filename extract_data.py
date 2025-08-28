from nobil.extract_nobil import nobil_extract_csv
import polars as pl

sources = (
    pl.read_csv("sources/metadata.csv").select(pl.col("id"), pl.col("local")).rows()
)

mappings = [s for s in sources if (s[1] is not None) and ("nobil" in s[1].lower())]

source = mappings[0][1]  # "20-01-2025-NOBIL-dump.json"
name = mappings[0][0]

nobil_extract_csv(source, name, "operational")

