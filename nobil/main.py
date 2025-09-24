from parser.extract import nobil_extract_data
from parser.annotate import write_annotated_nobil_csv

output_folder = "parsed"

data = nobil_extract_data("sources/NOBIL/20-01-2025-NOBIL-dump.json")
write_annotated_nobil_csv(data, output_folder, "NOBIL", "nobil/metadata.yml")
