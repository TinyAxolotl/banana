from argparse import ArgumentParser
import logging
import requests
from pathlib import Path

from . import config


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

    if args.eso_live_path[:2] == "~/":
        args.eso_live_path = Path.home().joinpath(args.eso_live_path[2:])

    config_path = Path(args.eso_live_path).joinpath("addons.yaml")
    config_path.touch(exist_ok=True)
    config_current = config.load(config_path)

    try:
        config.valid(config_current)
    except AssertionError:
        config.new(config_path)
        config_current = config.load(config_path)
        logging.info(f'addons list created at "{config_path}"')
