from pathlib import Path
import logging
import re
import requests

esoui_prefix = re.compile("https://www.esoui.com/downloads/info[0-9]+\-")
esoui_version_html = re.compile('<div\s+id="version">Version:\s+[^<]+')
esoui_version_split = re.compile('<div\s+id="version">Version:\s+')
live_title = re.compile("##\s+Title:\s+.*")
live_title_split = re.compile("##\s+Title:\s+")
live_version = re.compile("##\s+Version:\s+.*")
live_version_split = re.compile("##\s+Version:\s+")


def esoui(url: str):
    addon_name = esoui_prefix.split(url)[1]
    addon_name = addon_name.split(".html")[0]

    response = requests.get(url)
    version_line = esoui_version_html.search(response.text)
    version = esoui_version_split.split(version_line.group(0))[1]

    esoui_dowload_uri = url.replace("info", "download")
    response = requests.head(esoui_dowload_uri)
    response.raise_for_status()

    return addon_name, version, esoui_dowload_uri


def live_addon(path: Path):
    for meta in path.glob("*.txt"):
        with meta.open("r") as file_open:
            meta_data = file_open.read()

        title = live_title.search(meta_data)
        title = live_title_split.split(title.group(0))[1]
        version = live_version.search(meta_data)
        version = live_version_split.split(version.group(0))[1]

    return title, version
