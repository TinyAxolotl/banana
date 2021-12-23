from packaging import version
from pathlib import Path
import logging
import re
import requests

esoui_prefix = re.compile("https://www.esoui.com/downloads/info[0-9]+\-")
esoui_version_html = re.compile('<div\s+id="version">Version:\s+[^<]+')
esoui_version_split = re.compile('<div\s+id="version">Version:\s+')
esoui_download = re.compile('https://cdn.esoui.com/downloads/file[^"]*')
live_version = re.compile("##\s+Version:\s+.*")
live_version_split = re.compile("##\s+Version:\s+")


def esoui(url: str):
    addon_name = esoui_prefix.split(url)[1]
    addon_name = addon_name.split(".html")[0]

    response = requests.get(url)
    response.raise_for_status()

    version_line = esoui_version_html.search(response.text).group(0)
    _version = esoui_version_split.split(version_line)[1]
    _version = version.parse(_version)

    esoui_page_url = url.replace("info", "download").replace(".html", "")

    response = requests.get(esoui_page_url)
    response.raise_for_status()

    esoui_dowload_uri = esoui_download.search(response.text).group(0)
    response = requests.head(esoui_dowload_uri)
    response.raise_for_status()

    return addon_name, _version, esoui_dowload_uri


def live(path: Path):
    meta_file = path.joinpath(f"{path.stem}.txt")

    if not meta_file.is_file():
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
        _version = version.parse(_version)
    else:
        _version = version.parse("0")

    return addon_name, _version, path
