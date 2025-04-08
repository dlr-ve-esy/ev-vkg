import requests
from pathlib import Path
import logging

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)

if not (p := Path("./robot.jar")).exists():
    logging.info("Downloading robot.jar")
    response = requests.get("https://github.com/ontodev/robot/releases/download/v1.9.7/robot.jar")
    if response.status_code == 200:
        with open(p, "wb") as f:
            f.write(response.content)
else:
    logging.info("robot.jar is already downloaded")
