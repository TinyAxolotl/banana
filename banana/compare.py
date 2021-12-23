from io import BytesIO
from pathlib import Path
from shutil import rmtree, copytree
from tempfile import TemporaryDirectory
from zipfile import ZipFile
import logging
import requests

from . import parsing


def live_to_esoui(*, path: Path, esoui_uris: list):
    live_name, live_version, live_path = parsing.live(path)

    if not live_path:
        return

    esoui_name, esoui_version, esoui_uri = None, None, None

    for _name, _version, _uri in esoui_uris:
        if _name in live_name:
            esoui_name, esoui_version, esoui_uri = _name, _version, _uri
            break

        if live_name in _name:
            esoui_name, esoui_version, esoui_uri = _name, _version, _uri
            break

    if not esoui_name:
        rmtree(live_path)
        logging.info(f"{live_name} addon removed from: {live_path}")
        return

    if esoui_version == live_version:
        logging.info(f"{live_name} is already up to date.")
        return

    response = requests.get(esoui_uri)
    response.raise_for_status()

    temp_dir = TemporaryDirectory()
    temp_path = Path(temp_dir.name)

    zip_file = ZipFile(BytesIO(response.content))
    zip_file.extractall(temp_path)

    rmtree(live_path)

    for each in temp_path.iterdir():
        copytree(each, live_path)

    logging.info(
        f"{live_name} updated from {live_version} to {esoui_version} at {live_path}"
    )


def esoui_to_live(*, esoui_uris: list, live_path: Path):
    for addon_name, addon_version, esoui_dowload_uri in esoui_uris:
        match = None

        for each in live_path.iterdir():
            if addon_name in each.name:
                match = each
                break

            if each.name in addon_name:
                match = each
                break

        if match:
            logging.debug(f"{addon_name} already installed.")
            continue

        response = requests.get(esoui_dowload_uri)
        response.raise_for_status()

        temp_dir = TemporaryDirectory()
        temp_path = Path(temp_dir.name)

        zip_file = ZipFile(BytesIO(response.content))
        zip_file.extractall(temp_path)

        for each in temp_path.iterdir():
            live_dest = live_path.joinpath(each.name)

            if live_dest.exists():
                continue

            copytree(each, live_dest)

        logging.info(f"{addon_name} installed {addon_version} at {live_dest}")
