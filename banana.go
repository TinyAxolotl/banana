package main

import (
	"github.com/alexflint/go-arg"

	"bufio"
	"fmt"
	"os"
	"regexp"
	"strings"
)

var args struct {
	Addon_List_Path string `arg:"positional" default:"addons.list"`
	Out             string `arg:"-o,--out-dir" default:"downloads" help:"path to download directory"`
	Delay           int    `arg:"-d,--delay" default:"30" help:"seconds between poll with jitter"`
}

func main() {
	arg.MustParse(&args)
	fmt.Println("args", args)
}

func addon_list_read(addon_list_path string) ([]string, error) {
	file_open, error := os.OpenFile(addon_list_path, os.O_RDONLY, 0644)
	defer file_open.Close()
	if error != nil {
		return nil, error
	}

	file_scanner := bufio.NewScanner(file_open)
	lines := []string{}

	for file_scanner.Scan() {
		line := file_scanner.Text()

		if strings.HasPrefix(line, "#") {
			continue
		}

		lines = append(lines, line)
	}

	return lines, nil
}

const (
	CONFIG_TEMPLATE = `https://www.esoui.com/downloads/info7-LibAddonMenu.html
https://www.esoui.com/downloads/info1245-TamrielTradeCentre.html
https://www.esoui.com/downloads/info1146-LibCustomMenu.html
`
	ESO_LIVE_PATH_WINDOWS = `Documents\Elder Scrolls Online\live`
	ESO_LIVE_PATH_STEAMOS = ".steam/steam/steamapps/compatdata/306130/pfx/drive_c/users/steamuser/Documents/Elder Scrolls Online/live/"
)

var (
	ESOUI_PREFIX        = regexp.MustCompile(`https://www.esoui.com/downloads/info[0-9]+\-`)
	ESOUI_VERSION_HTML  = regexp.MustCompile(`<div\s+id="version">Version:\s+[^<]+`)
	ESOUI_VERSION_SPLIT = regexp.MustCompile(`<div\s+id="version">Version:\s+`)
	ESOUI_DOWNLOAD      = regexp.MustCompile(`https://cdn.esoui.com/downloads/file[^"]*`)
	LIVE_VERSION        = regexp.MustCompile(`##\s+Version:\s+.*`)
	LIVE_VERSION_SPLIT  = regexp.MustCompile(`##\s+Version:\s+`)
)
