import requests
import zipfile
from pathlib import Path
import wget
import re

(TEMP := Path("temp")).mkdir(exist_ok=True)
(PARSED := Path("parsed")).mkdir(exist_ok=True)
(RAW := Path("sources")).mkdir(exist_ok=True)

URL = "https://zenodo.org/api/records/17174842"


zip_filename = "data-ci-publication-transparency"
if not (folder := Path(TEMP).joinpath(f"{zip_filename}.zip")).exists():
    r = requests.get(URL, timeout=15.0)
    js = r.json()
    files = [f for f in js["files"] if f["key"] == f"{zip_filename}.zip"]
    link = files[0]["links"]["self"]
    filename = wget.download(
        f"{link}",
        out=f"{folder}",
    )
else:
    print(f"{folder} already exists, skipping download!")

z = zipfile.ZipFile(folder)

for file in z.namelist():
    if file.startswith("parsed/"):
        if Path(file).is_dir():
            pass
        else:
            file_name = PARSED.joinpath(file.replace("parsed/", ""))
            file_name.parent.mkdir(exist_ok=True, parents=True)
            if re.match(r"^.*\.[^\\]+$", file_name.as_posix()) is not None:
                if not file_name.exists():
                    with open(f"{file_name}", "wb") as f:
                        f.write(z.read(file))
                else:
                    print(f"{file_name} already exists, skipping extraction!")

    if file.startswith("sources/"):
        if (sp := Path(file)).is_dir():
            pass
        else:
            file_name = RAW.joinpath(file.replace("sources/", ""))
            file_name.parent.mkdir(exist_ok=True, parents=True)
            if re.match(r"^.*\.[^\\]+$", file_name.as_posix()) is not None:
                if not file_name.exists():
                    with open(f"{file_name}", "wb") as f:
                        f.write(z.read(file))
                else:
                    print(f"{file_name} already exists, skipping extraction!")
