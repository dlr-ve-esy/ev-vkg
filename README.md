# Public EV charging infrastructure virtual knowledge graph

This repository is the code suppoting the publication "Actionable Electric Vehicle Charging Infrastructure Data: Enabling digital preservation of European policy performance analyses"

## Usage

To work with this repository you need to acquire the data from 
 [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.17174842.svg)](https://doi.org/10.5281/zenodo.17174842). The script `get_data.py` can be used to download it automatically and saved in the right folder. 

Once the data is in the main folder you need to install the dependencies. I recommend using [uv](https://github.com/astral-sh/uv). But any python package management should work. Using uv you can run:

```bash
uv install
```

Otherwise using your favorite python environment management tool you can activate your env and install:

```bash
pip install -e .
```
To get the archived version of the data you can run the `get_data.py` script.

```bash
python get_data.py
```

The knowledge graph can be built and explored using the marimo notebook `main.py`, calling:

```bash
uv run marimo edit main.py
```

Or using the pip installation of marimo, calling:

```bash
marimo edit main.py
```