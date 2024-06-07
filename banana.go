package main

import (
	"github.com/alexflint/go-arg"

	"bufio"
	"errors"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"regexp"
	"runtime"
	"strings"
)

var args struct {
	Addon_list_path string `arg:"-i,--addon-list" help:"path to addon list file"`
	Out_dir         string `arg:"-o,--live-dir" help:"path to eso live directory"`
	Ttc             bool   `arg:"-t,--ttc" help:"only update tamriel trade centre db"`
}

func main() {
	arg.MustParse(&args)
	fmt.Println("args", args)

	eso_live_path := eso_live_path_get()

	if args.Addon_list_path == "" {
		args.Addon_list_path = filepath.Join(eso_live_path, "addons.list")
	}

	if args.Out_dir == "" {
		args.Out_dir = filepath.Join(eso_live_path)
	}

	_, error := os.Stat(args.Addon_list_path)
	if errors.Is(error, os.ErrNotExist) {
		error = addon_list_create(args.Addon_list_path)
		if error != nil {
			panic(error)
		}
	}

	addon_urls, error := addon_list_read(args.Addon_list_path)
	if error != nil {
		panic(error)
	}

	addon_paths, error := os.ReadDir(filepath.Join(args.Out_dir, "AddOns"))
	if error != nil {
		panic(error)
	}

	var eso_live_addon_names []string
	for _, path := range addon_paths {
		if path.IsDir() {
			eso_live_addon_names = append(eso_live_addon_names, path.Name())
		}
	}

	var eso_ui_list []EsoAddon

	for _, url := range addon_urls {
		eso_ui, error := eso_ui_stat_init(url)
		if error != nil {
			panic(error)
		}

		eso_ui_list = append(eso_ui_list, eso_ui)
	}

	for _, eso_live_name := range eso_live_addon_names {
		matching := ""

		for _, eso_ui := range eso_ui_list {
			if strings.Contains(eso_live_name, eso_ui.addon_name) {
				matching = eso_live_name
			}
		}

		if matching == "" {
			addon_path := filepath.Join(args.Out_dir, "AddOns", eso_live_name)
			fmt.Println("Removing inactive addon", addon_path)
			// TODO os.RemoveAll(addon_path)
		}
	}
}

const (
	CONFIG_TEMPLATE = `https://www.esoui.com/downloads/info7-LibAddonMenu.html
https://www.esoui.com/downloads/info1245-TamrielTradeCentre.html
https://www.esoui.com/downloads/info1146-LibCustomMenu.html
`
	ESO_LIVE_PATH_WINDOWS = `Documents\Elder Scrolls Online\live`
	ESO_LIVE_PATH_STEAMOS = ".steam/steam/steamapps/compatdata/306130/pfx/drive_c/users/steamuser/Documents/Elder Scrolls Online/live/"
	TCC_PRICE_TABLE_URI   = "https://us.tamrieltradecentre.com/download/PriceTable"
	TCC_PRICE_TABLE_NAME  = "TamrielTradeCentre"
)

var (
	ESOUI_NAME    = regexp.MustCompile(`(?:https://www.esoui.com/downloads/info[0-9]+\-)([A-Za-z]+)(?:\.html)`)
	ESOUI_VERSION = regexp.MustCompile(`(?:<div\s+id="version">Version:\s+)(.*)(?:</div>)`)
	LIVE_VERSION  = regexp.MustCompile(`(?:##\s+Version:\s+)(.*)`)
)

func eso_live_path_get() string {
	home_path, error := os.UserHomeDir()
	if error != nil {
		panic(error)
	}

	if runtime.GOOS == "windows" {
		return filepath.Join(home_path, ESO_LIVE_PATH_WINDOWS)
	} else {
		return filepath.Join(home_path, ESO_LIVE_PATH_STEAMOS)
	}
}

func addon_list_create(addon_list_path string) error {
	file_open, error := os.Create(addon_list_path)
	if error != nil {
		return error
	}
	defer file_open.Close()

	_, error = file_open.Write([]byte(CONFIG_TEMPLATE))
	if error != nil {
		return error
	}

	return nil
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

		switch {
		case line == "":
			continue
		case strings.HasPrefix(line, "#"):
			continue
		case strings.HasPrefix(line, "//"):
			continue
		case strings.HasPrefix(line, "-"):
			continue
		}

		lines = append(lines, line)
	}

	return lines, nil
}

type EsoAddon struct {
	addon_name  string
	version     string
	dowload_uri string
}

func eso_ui_stat_init(addon_url string) (EsoAddon, error) {
	response, error := http.Get(addon_url)
	if error != nil {
		return EsoAddon{}, error
	}
	defer response.Body.Close()

	if response.StatusCode == http.StatusNotFound {
		return EsoAddon{}, errors.New(http.StatusText(response.StatusCode))
	}

	body, error := io.ReadAll(response.Body)
	if error != nil {
		return EsoAddon{}, error
	}

	addon_name := ESOUI_NAME.FindStringSubmatch(addon_url)[1]
	version := ESOUI_VERSION.FindStringSubmatch(string(body))[1]
	dowload_uri := strings.Replace(addon_url, "info", "download", -1)

	return EsoAddon{addon_name, version, dowload_uri}, nil
}
