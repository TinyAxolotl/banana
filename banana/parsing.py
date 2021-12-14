import requests
import re
import logging

esoui_prefix = re.compile("https://www.esoui.com/downloads/info[0-9]+\-")
esoui_version_html = re.compile('<div\s+id="version">Version:\s+[^<]+')
esoui_version_split = re.compile('<div\s+id="version">Version:\s+')


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
