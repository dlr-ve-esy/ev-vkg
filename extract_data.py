from nobil.src.extract import nobil_extract_data
from nobil.src.annotate import write_annotated_nobil_csv
from bnetza.src.rename import get_renamed_bnetza
import polars as pl

sources = (
    pl.read_csv("sources/metadata.csv").select(pl.col("id"), pl.col("local")).rows()
)

mappings = [s for s in sources if (s[1] is not None) and ("nobil" in s[1].lower())]

source = mappings[0][1]  # "20-01-2025-NOBIL-dump.json"
name = mappings[0][0]

nobil_data = nobil_extract_data("sources/NOBIL/20-01-2025-NOBIL-dump.json")
write_annotated_nobil_csv(nobil_data, "operational", name, "nobil/metadata.yml")

get_renamed_bnetza(
    "operational",
    "sources/BNETZA/bnetza_charging_stations_raw_08_2025.xlsx",
)
