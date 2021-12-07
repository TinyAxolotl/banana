from argparse import ArgumentParser
import logging
import requests
from pathlib import Path

from . import config


def periodical_script():
    parser = ArgumentParser(description="Secret sharing script.")
    parser.add_argument("-v", "--verbose", action="count", help="verbose logging")
    parser.add_argument(
        "-c", "--config", default="banana.yaml", help="configuration file path"
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

    config_path = Path(args.config)
    config_path.touch(exist_ok=True)
    config_current = config.load(config_path)

    try:
        config.valid(config_current)
    except (AssertionError, AttributeError) as error:
        logging.debug(error)
        config.new(config_path)
        config_current = config.load(config_path)
