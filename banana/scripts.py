import requests
import re
import logging
from pathlib import Path
from argparse import ArgumentParser

from . import config


def esoui_parse(addon_urls: list):
    esoui_prefix = re.compile("https://www.esoui.com/downloads/info[0-9]+\-")
    esoui_names = list()

    for url in addon_urls:
        addon = esoui_prefix.split(url)[1]
        addon = addon.split(".html")[0]
        esoui_names.append(addon)

    logging.info(esoui_names)

    esoui_version_html = re.compile('<div\s+id="version">Version:\s+[^<]+')
    esoui_version_split = re.compile('<div\s+id="version">Version:\s+')
    esoui_versions = list()

    for url in addon_urls:
        response = requests.get(url)
        version_line = esoui_version_html.search(response.text)
        version = esoui_version_split.split(version_line.group(0))[1]
        esoui_versions.append(version)

    esoui_dowload_uris = list()

    for url in addon_urls:
        esoui_dowload_uri = url.replace("info", "download")
        response = requests.head(esoui_dowload_uri)
        response.raise_for_status()
        esoui_dowload_uris.append(esoui_dowload_uri)

    return esoui_names, esoui_versions, esoui_dowload_uris


def periodical_script():
    parser = ArgumentParser(
        description="Visit https://www.esoui.com/ to search for addons and their dependencies URLs. Edit addons.yaml in the ESO live path and add the URL for each addon for installation. "
    )
    parser.add_argument("-v", "--verbose", action="count", help="verbose logging")
    parser.add_argument(
        "-p",
        "--eso_live_path",
        default=Path.home().joinpath(
            ".steam/steam/steamapps/compatdata/306130/pfx/drive_c/users/steamuser/Documents/Elder Scrolls Online/live/"
        ),
        help='default: "~/.steam/steam/steamapps/compatdata/306130/pfx/drive_c/users/steamuser/Documents/Elder Scrolls Online/live/"',
    )
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s %(filename)s:%(lineno)d %(message)s",
        )
    else:
        logging.basicConfig(
            level=logging.INFO,
            format="%(message)s",
        )

    logging.info(args)

    if isinstance(args.eso_live_path, str):
        if args.eso_live_path[:2] == "~/":
            args.eso_live_path = Path.home().joinpath(args.eso_live_path[2:])

    config_path = Path(args.eso_live_path).joinpath("addons.yaml")
    config_path.touch(exist_ok=True)
    config_current = config.load(config_path)

    try:
        config.valid(config_current)
    except (AssertionError, AttributeError):
        config.new(config_path)
        config_current = config.load(config_path)
        logging.info(f'addons list created at "{config_path}"')

    addon_urls = config_current.get("addons")
    esoui = esoui_parse(addon_urls)
    logging.info(esoui)
