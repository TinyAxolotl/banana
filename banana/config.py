import yaml
from pathlib import Path


def new(path: Path):
    config = {
        "addons": [None],
        "eso": {"path": None},
    }

    with path.open("w") as file_open:
        config = yaml.dump(config, file_open, default_flow_style=False)


def load(path: Path) -> dict:
    with path.open("r") as file_open:
        config = yaml.load(file_open)

    return config


def valid(config: dict) -> bool:
    assert config.get("addons")
    assert config.get("eso")

    if not "path" in config.get("eso"):
        raise AssertionError()
