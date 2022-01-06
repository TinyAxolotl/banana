from argparse import ArgumentParser
from pathlib import Path
from platform import system
import logging

from . import compare
from . import config
from . import parsing
from . import tamriel_trade_centre


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
        if system() == "Windows":
            args.eso_live_path = Path.home().joinpath(
                "Documents\Elder Scrolls Online\live"
            )
        else:
            args.eso_live_path = Path.home().joinpath(
                ".steam/steam/steamapps/compatdata/306130/pfx/drive_c/users/steamuser/Documents/Elder Scrolls Online/live/"
            )

    if args.verbose:
        level = logging.DEBUG
        format = "%(asctime)s %(filename)s:%(lineno)d %(message)s"
    else:
        level = logging.INFO
        format = "%(message)s"

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

    config_path = Path(args.eso_live_path).joinpath("addons.yaml")
    config_path.touch(exist_ok=True)
    config_current = config.load(config_path)

    try:
        config.valid(config_current)
    except (AssertionError, AttributeError):
        config.new(config_path)
        config_current = config.load(config_path)
        logging.info(f'addons list created at "{config_path}"')

    live_path = args.eso_live_path.joinpath("AddOns")

    if not live_path.is_dir():
        logging.error(f"eso_live_path_invalid_dir {live_path}")
        return

    addon_urls = config_current.get("addons")
    esoui_uris = list()

    for url in addon_urls:
        esoui = parsing.esoui(url)
        esoui_uris.append(esoui)

    for child in live_path.iterdir():
        compare.live_to_esoui(path=child, esoui_uris=esoui_uris)

    compare.esoui_to_live(esoui_uris=esoui_uris, live_path=live_path)
    tamriel_trade_centre.update(live_path=live_path)


def ttc():
    parser = ArgumentParser(description="Tamriel Trade Centre price table updater.")
    parser.add_argument("-v", "--verbose", action="count", help="verbose logging")
    parser.add_argument("-l", "--log", action="store_true")
    parser.add_argument("-p", "--eso_live_path")
    args = parser.parse_args()

    if args.eso_live_path:
        args.eso_live_path = Path(args.eso_live_path)
    else:
        if system() == "Windows":
            args.eso_live_path = Path.home().joinpath(
                "Documents\Elder Scrolls Online\live"
            )
        else:
            args.eso_live_path = Path.home().joinpath(
                ".steam/steam/steamapps/compatdata/306130/pfx/drive_c/users/steamuser/Documents/Elder Scrolls Online/live/"
            )

    if args.verbose:
        level = logging.DEBUG
        format = "%(asctime)s %(filename)s:%(lineno)d %(message)s"
    else:
        level = logging.INFO
        format = "%(message)s"

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

    tamriel_trade_centre.update(live_path=live_path)
