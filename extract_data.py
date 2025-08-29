from nobil.extract import nobil_extract_csv
from bnetza.src.rename import get_renamed_bnetza
import polars as pl

sources = (
    pl.read_csv("sources/metadata.csv").select(pl.col("id"), pl.col("local")).rows()
)

mappings = [s for s in sources if (s[1] is not None) and ("nobil" in s[1].lower())]

source = mappings[0][1]  # "20-01-2025-NOBIL-dump.json"
name = mappings[0][0]

nobil_extract_csv(source, name, "operational")

get_renamed_bnetza(
    "operational",
    "sources/BNETZA/bnetza_charging_stations_raw_08_2025.xlsx",
)
