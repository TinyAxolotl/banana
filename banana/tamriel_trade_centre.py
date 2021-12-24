from distutils.dir_util import copy_tree
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile
import logging
import requests

price_table_uri = "https://us.tamrieltradecentre.com/download/PriceTable"
price_table_name = "TamrielTradeCentre"


def update(live_path: Path):
    response = requests.get(price_table_uri)
    response.raise_for_status()

    temp_dir = TemporaryDirectory()
    temp_path = Path(temp_dir.name)

    zip_file = ZipFile(BytesIO(response.content))
    zip_file.extractall(temp_path)

    live_tamriel_trade_centre = live_path.joinpath("TamrielTradeCentre")
    copy_tree(str(temp_path.absolute()), str(live_tamriel_trade_centre.absolute()))

    logging.info(
        f"tamriel trade centre price table updated: {live_tamriel_trade_centre}"
    )
