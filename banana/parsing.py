from pathlib import Path
import logging
import re
import requests

esoui_prefix = re.compile("https://www.esoui.com/downloads/info[0-9]+\-")
esoui_version_html = re.compile('<div\s+id="version">Version:\s+[^<]+')
esoui_version_split = re.compile('<div\s+id="version">Version:\s+')
esoui_download = re.compile('https://cdn.esoui.com/downloads/file[^"]*')
live_title = re.compile("##\s+Title:\s+.*")
live_title_split = re.compile("##\s+Title:\s+")
live_version = re.compile("##\s+Version:\s+.*")
live_version_split = re.compile("##\s+Version:\s+")


def esoui(url: str):
    addon_name = esoui_prefix.split(url)[1]
    addon_name = addon_name.split(".html")[0]

    response = requests.get(url)
    response.raise_for_status()

    version_line = esoui_version_html.search(response.text).group(0)
    version = esoui_version_split.split(version_line)[1]

    esoui_page_url = url.replace("info", "download").replace(".html", "")

    response = requests.get(esoui_page_url)
    response.raise_for_status()

    esoui_dowload_uri = esoui_download.search(response.text).group(0)
    response = requests.head(esoui_dowload_uri)
    response.raise_for_status()

    return addon_name, version, esoui_dowload_uri


def live(path: Path):
    for meta in path.glob("*.txt"):

        try:
            with meta.open("r") as file_open:
                meta_data = file_open.read()
        except UnicodeDecodeError:
            with meta.open("r", encoding="latin-1") as file_open:
                meta_data = file_open.read()

        addon_name = live_title.search(meta_data).group(0)
        addon_name = live_title_split.split(addon_name)[1]
        version = live_version.search(meta_data).group(0)
        version = live_version_split.split(version)[1]

        return addon_name, version, path

    return None, None, None
