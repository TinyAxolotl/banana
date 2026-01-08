from argparse import ArgumentParser
from io import BytesIO
from packaging import version
from pathlib import Path
from platform import system
from shutil import rmtree, copytree
from tempfile import TemporaryDirectory
from typing import Tuple
from zipfile import ZipFile
import logging
import re
import requests

config_template = """https://www.esoui.com/downloads/info7-LibAddonMenu.html
https://www.esoui.com/downloads/info1245-TamrielTradeCentre.html
https://www.esoui.com/downloads/info1146-LibCustomMenu.html
"""


def config_new(path: Path):
    path.touch(exist_ok=True)

    with path.open("w") as file_open:
        file_open.write(config_template)

def live_to_esoui(*, path: Path, esoui_uris: list):
    live_name, live_version, live_path = parsing_live(path)

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


esoui_prefix = re.compile("https://www.esoui.com/downloads/info[0-9]+\-")
esoui_version_html = re.compile('<div\s+id="version">Version:\s+[^<]+')
esoui_version_split = re.compile('<div\s+id="version">Version:\s+')
esoui_download = re.compile('https://cdn.esoui.com/downloads/file[^"]*')
live_version = re.compile("##\s+Version:\s+.*")
live_version_split = re.compile("##\s+Version:\s+")


def esoui_parse(url: str) -> Tuple[str, version.Version, str]:
    addon_name = esoui_prefix.split(url)[1]
    addon_name = addon_name.split(".html")[0]

    response = requests.get(url)
    response.raise_for_status()

    version_line = esoui_version_html.search(response.text).group(0)
    _version = esoui_version_split.split(version_line)[1]
    try:
        _version = version.parse(_version)
    except version.InvalidVersion:
        _version = version.parse("1")

    esoui_page_url = url.replace("info", "download").replace(".html", "")

    response = requests.get(esoui_page_url)
    response.raise_for_status()

    esoui_dowload_uri = esoui_download.search(response.text).group(0)
    response = requests.head(esoui_dowload_uri)
    response.raise_for_status()

    return addon_name, _version, esoui_dowload_uri


def parsing_live(path: Path):
    if not path.is_dir():
        logging.error(f"unexpected file object {path}, ignoring")
        return

    meta_file = path.joinpath(f"{path.stem}.txt")

    if not meta_file.exists():
        for meta_file in path.glob("*.txt"):
            if not meta_file.stem in path.stem:
                continue

    try:
        with meta_file.open("r") as file_open:
            meta_data = file_open.read()
    except UnicodeDecodeError:
        with meta_file.open("r", encoding="latin-1") as file_open:
            meta_data = file_open.read()

    addon_name = meta_file.stem
    result = live_version.search(meta_data)

    if result:
        _version = result.group(0)
        _version = live_version_split.split(_version)[1]
        try:
            _version = version.parse(_version)
        except version.InvalidVersion:
            _version = version.parse("0")
    else:
        _version = version.parse("0")

    return addon_name, _version, path

def eso_live_path_get():
    if system() == "Windows":
        eso_live_path = Path.home().joinpath(
            "Documents\Elder Scrolls Online\live"
        )
        if eso_live_path.exists:
            return eso_live_path

    else:
        eso_live_path = Path.home().joinpath(
            ".steam/steam/steamapps/compatdata/306130/pfx/drive_c/users/steamuser/Documents/Elder Scrolls Online/live/"
        )

        if eso_live_path.exists():
            return eso_live_path
        
        eso_live_path = Path.home().joinpath(
            ".var/app/com.valvesoftware.Steam/.local/share/Steam/steamapps/compatdata/306130/pfx/drive_c/users/steamuser/Documents/Elder Scrolls Online/live"
        )

        if eso_live_path.exists():
            return eso_live_path
    
    raise Exception("Unable to find `steamuser/Documents/Elder Scrolls Online/live`, specify the full path and contact maintainer to see if they'll add it.")

def unlisted_remove():
    parser = ArgumentParser(
        description="Visit https://www.esoui.com/ to search for addons and their dependencies URLs. Edit addons.yaml in the ESO live path and add the URL for each addon for installation. "
    )
    parser.add_argument("-v", "--verbose", action="count", help="verbose logging")
    parser.add_argument("-l", "--log", action="store_true")
    parser.add_argument("-p", "--eso_live_path")
    args = parser.parse_args()

    if args.eso_live_path:
        args.eso_live_path = Path(args.eso_live_path)
    else:
        args.eso_live_path = eso_live_path_get()

    if args.verbose:
        level = logging.DEBUG
        format = "%(asctime)s %(filename)s:%(lineno)d %(message)s"
    else:
        level = logging.INFO
        format = "%(asctime)s %(message)s"

    if args.log:
        logging.basicConfig(
            level=level,
            format=format,
            filename=args.eso_live_path.joinpath("banana.log"),
        )
    else:
        logging.basicConfig(
            level=level,
            format=format,
        )

    logging.info(args)


    config_path = Path(args.eso_live_path).joinpath("addons.list")

    if not config_path.exists():
        config_new(config_path)
        logging.info(f'addons list created at "{config_path}"')

    with config_path.open("r") as file_open:
        config_current = [line.rstrip('\n') for line in file_open]

    config_current = filter(None, config_current)
    live_path = args.eso_live_path.joinpath("AddOns")
    live_path.mkdir(parents=True, exist_ok=True)
    esoui_uris = list()

    for url in config_current:
        esoui = esoui_parse(url)
        if esoui:
            esoui_uris.append(esoui)

    for child in live_path.iterdir():
        live_to_esoui(path=child, esoui_uris=esoui_uris)

    esoui_to_live(esoui_uris=esoui_uris, live_path=live_path)
    ttc_update(live_path=live_path)

def periodical_script():
    parser = ArgumentParser(
        description="Visit https://www.esoui.com/ to search for addons and their dependencies URLs. Edit addons.yaml in the ESO live path and add the URL for each addon for installation. "
    )
    parser.add_argument("-v", "--verbose", action="count", help="verbose logging")
    parser.add_argument("-l", "--log", action="store_true")
    parser.add_argument("-p", "--eso_live_path")
    args = parser.parse_args()

    if args.eso_live_path:
        args.eso_live_path = Path(args.eso_live_path)
    else:
        args.eso_live_path = eso_live_path_get()

    if args.verbose:
        level = logging.DEBUG
        format = "%(asctime)s %(filename)s:%(lineno)d %(message)s"
    else:
        level = logging.INFO
        format = "%(asctime)s %(message)s"

    if args.log:
        logging.basicConfig(
            level=level,
            format=format,
            filename=args.eso_live_path.joinpath("banana.log"),
        )
    else:
        logging.basicConfig(
            level=level,
            format=format,
        )

    logging.info(args)


    config_path = Path(args.eso_live_path).joinpath("addons.list")

    if not config_path.exists():
        config_new(config_path)
        logging.info(f'addons list created at "{config_path}"')

    with config_path.open("r") as file_open:
        config_current = [line.rstrip('\n') for line in file_open]

    config_current = filter(None, config_current)
    live_path = args.eso_live_path.joinpath("AddOns")
    live_path.mkdir(parents=True, exist_ok=True)
    esoui_uris = list()

    for url in config_current:
        esoui = esoui_parse(url)
        if esoui:
            esoui_uris.append(esoui)

    esoui_to_live(esoui_uris=esoui_uris, live_path=live_path)
    ttc_update(live_path=live_path)


def ttc():
    parser = ArgumentParser(description="Tamriel Trade Centre price table updater.")
    parser.add_argument("-v", "--verbose", action="count", help="verbose logging")
    parser.add_argument("-l", "--log", action="store_true")
    parser.add_argument("-p", "--eso_live_path")
    args = parser.parse_args()

    if args.eso_live_path:
        args.eso_live_path = Path(args.eso_live_path)
    else:
        args.eso_live_path = eso_live_path_get()

    if args.verbose:
        level = logging.DEBUG
        format = "%(asctime)s %(filename)s:%(lineno)d %(message)s"
    else:
        level = logging.INFO
        format = "%(asctime)s %(message)s"

    if args.log:
        logging.basicConfig(
            level=level,
            format=format,
            filename=args.eso_live_path.joinpath("banana.log"),
        )
    else:
        logging.basicConfig(
            level=level,
            format=format,
        )

    logging.info(args)

    live_path = Path(args.eso_live_path).joinpath("AddOns")

    if not live_path.is_dir():
        logging.error(f"eso_live_path_invalid_dir {live_path}")
        return

    ttc_update(live_path=live_path)


price_table_uri = "https://us.tamrieltradecentre.com/download/PriceTable"
price_table_name = "TamrielTradeCentre"


def ttc_update(live_path: Path):
    response = requests.get(price_table_uri)
    response.raise_for_status()

    temp_dir = TemporaryDirectory()
    temp_path = Path(temp_dir.name)

    zip_file = ZipFile(BytesIO(response.content))
    zip_file.extractall(temp_path)

    live_tamriel_trade_centre = live_path.joinpath("TamrielTradeCentre")
    copytree(temp_path.absolute(), live_tamriel_trade_centre.absolute(), dirs_exist_ok=True)

    logging.info(
        f"tamriel trade centre price table updated: {live_tamriel_trade_centre}"
    )


if __name__ == "__main__":
    periodical_script()
