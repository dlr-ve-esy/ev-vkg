from nobil.parser.extract import nobil_extract_data
from nobil.parser.annotate import write_annotated_nobil_csv
from bnetza.parser.rename import get_renamed_bnetza

# from bnetza.rename import get_renamed_bnetza
import polars as pl

output_folder = "operational"

sources = (
    pl.read_csv("sources/metadata.csv").select(pl.col("id"), pl.col("local")).rows()
)

nobil_data = [s for s in sources if (s[1] is not None) and ("nobil" in s[1].lower())]

source_nobil = nobil_data[0][1]  # "20-01-2025-NOBIL-dump.json"
name_nobil = nobil_data[0][0]


irve_data = [s for s in sources if (s[1] is not None) and ("irve" in s[1].lower())]

source_irve = irve_data[0][1]
name_irve = irve_data[0][0]


nobil_data = nobil_extract_data(source_nobil)
write_annotated_nobil_csv(nobil_data, output_folder, name_nobil, "nobil/metadata.yml")

get_renamed_bnetza(
    output_folder,
    "sources/BNETZA/bnetza_charging_stations_raw_08_2025.xlsx",
)
