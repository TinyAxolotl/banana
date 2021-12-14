import yaml
from pathlib import Path


def new(path: Path):
    config = {
        "addons": [
            "https://www.esoui.com/downloads/info7-LibAddonMenu.html",
            "https://www.esoui.com/downloads/info1245-TamrielTradeCentre.html",
            "https://www.esoui.com/downloads/info1146-LibCustomMenu.html",
        ]
    }

    with path.open("w") as file_open:
        config = yaml.dump(config, file_open, default_flow_style=False)


def load(path: Path) -> dict:
    with path.open("r") as file_open:
        config = yaml.load(file_open, Loader=yaml.Loader)

    return config


def valid(config: dict) -> bool:
    assert config.get("addons")
    assert isinstance(config["addons"], list)
