package main

import (
	"github.com/alexflint/go-arg"

	"archive/zip"
	"bufio"
	"bytes"
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
	eso_live_path := eso_live_path_get()
	if args.Addon_list_path == "" {
		args.Addon_list_path = filepath.Join(eso_live_path, "addons.list")
	}
	if args.Out_dir == "" {
		args.Out_dir = filepath.Join(eso_live_path, "AddOns")
	}
	fmt.Println("args", args)

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

	error = ttc_update(filepath.Join(args.Out_dir, "TamrielTradeCentre"))
	if error != nil {
		panic(error)
	}

	fmt.Println("Updated,", TCC_PRICE_TABLE_URI)

	if args.Ttc {
		return
	}

	addon_paths, error := os.ReadDir(args.Out_dir)
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

	var eso_live_list []EsoAddon
	for _, eso_live_name := range eso_live_addon_names {
		eso_live, error := eso_live_stat_init(eso_live_name)
		if error != nil {
			continue
		}

		matching := ""

		for _, eso_ui := range eso_ui_list {
			if strings.Contains(eso_live_name, eso_ui.name) {
				matching = eso_live_name
			}
		}

		if matching == "" {
			fmt.Println("Removed,", eso_live.path)
			os.RemoveAll(eso_live.path)
			continue
		}

		eso_live_list = append(eso_live_list, eso_live)
	}

	for _, eso_live := range eso_live_list {
		fmt.Printf("Live, %s, %s\n", eso_live.name, eso_live.version)
	}
	for _, eso_ui := range eso_ui_list {
		fmt.Printf("Updated, %s, %s\n", eso_ui.name, eso_ui.version)
		error = eso_ui_get_unzip(eso_ui.path, args.Out_dir)
		if error != nil {
			panic(error)
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
)

var (
	ESOUI_NAME     = regexp.MustCompile(`(?:https://www.esoui.com/downloads/info[0-9]+\-)([A-Za-z]+)(?:\.html)`)
	ESOUI_VERSION  = regexp.MustCompile(`(?:<div\s+id="version">Version:\s+)(.*)(?:</div>)`)
	ESOUI_DOWNLOAD = regexp.MustCompile(`https://cdn.esoui.com/downloads/file[^"]*`)
	LIVE_VERSION   = regexp.MustCompile(`(?:##\s+Version:\s+)(.*)(?:\n)`)
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
	name    string
	version string
	path    string
}

func eso_ui_stat_init(addon_url string) (EsoAddon, error) {
	addon_resp, error := http.Get(addon_url)
	if error != nil {
		return EsoAddon{}, error
	}
	defer addon_resp.Body.Close()

	if addon_resp.StatusCode == http.StatusNotFound {
		return EsoAddon{}, errors.New(http.StatusText(addon_resp.StatusCode))
	}

	addon_body, error := io.ReadAll(addon_resp.Body)
	if error != nil {
		return EsoAddon{}, error
	}

	download_page_url := strings.Replace(addon_url, "info", "download", -1)
	download_resp, error := http.Get(download_page_url)
	if error != nil {
		return EsoAddon{}, error
	}
	defer download_resp.Body.Close()

	if download_resp.StatusCode == http.StatusNotFound {
		return EsoAddon{}, errors.New(http.StatusText(download_resp.StatusCode))
	}

	download_body, error := io.ReadAll(download_resp.Body)
	if error != nil {
		return EsoAddon{}, error
	}

	var name string
	names := ESOUI_NAME.FindStringSubmatch(addon_url)
	if len(names) > 1 {
		name = names[1]
	} else {
		name = ""
	}

	var version string
	versions := ESOUI_VERSION.FindStringSubmatch(string(addon_body))
	if len(versions) > 1 {
		version = versions[1]
	} else {
		version = ""
	}

	path := string(ESOUI_DOWNLOAD.Find(download_body))
	if path == "" {
		return EsoAddon{}, errors.New("Download URI missing " + addon_url)
	}

	return EsoAddon{name, version, path}, nil
}

func eso_live_stat_init(eso_live_name string) (EsoAddon, error) {
	path := filepath.Join(args.Out_dir, eso_live_name)

	content, error := os.ReadFile(filepath.Join(path, eso_live_name+".txt"))
	if error != nil {
		return EsoAddon{}, error
	}

	var version string
	versions := LIVE_VERSION.FindStringSubmatch(string(content))
	if len(versions) > 1 {
		version = versions[1]
	} else {
		version = ""
	}

	return EsoAddon{eso_live_name, version, path}, nil
}

func eso_ui_get_unzip(esoui_url string, out_dir string) error {
	response, error := http.Get(esoui_url)
	if error != nil {
		return error
	}
	defer response.Body.Close()

	if response.StatusCode == http.StatusNotFound {
		return errors.New(http.StatusText(response.StatusCode))
	}

	body, error := io.ReadAll(response.Body)
	if error != nil {
		return error
	}

	reader := bytes.NewReader(body)
	zip_reader, error := zip.NewReader(reader, int64(len(body)))
	if error != nil {
		return error
	}

	for _, zipped_file := range zip_reader.File {
		if zipped_file.Mode().IsDir() {
			continue
		}

		zipped_file_open, error := zipped_file.Open()
		if error != nil {
			return error
		}

		name := filepath.Join(out_dir, zipped_file.Name)
		os.MkdirAll(filepath.Dir(name), os.ModePerm)

		create, error := os.Create(name)
		if error != nil {
			return error
		}
		defer create.Close()

		create.ReadFrom(zipped_file_open)
	}

	return nil
}

func ttc_update(out_path string) error {
	response, error := http.Get(TCC_PRICE_TABLE_URI)
	if error != nil {
		return error
	}
	defer response.Body.Close()

	if response.StatusCode == http.StatusNotFound {
		return errors.New(http.StatusText(response.StatusCode))
	}

	body, error := io.ReadAll(response.Body)
	if error != nil {
		return error
	}

	reader := bytes.NewReader(body)
	zip_reader, error := zip.NewReader(reader, int64(len(body)))
	if error != nil {
		return error
	}

	for _, zipped_file := range zip_reader.File {
		if zipped_file.Mode().IsDir() {
			continue
		}

		zipped_file_open, error := zipped_file.Open()
		if error != nil {
			return error
		}

		name := filepath.Join(out_path, zipped_file.Name)
		os.MkdirAll(filepath.Dir(name), os.ModePerm)

		create, error := os.Create(name)
		if error != nil {
			return error
		}
		defer create.Close()

		create.ReadFrom(zipped_file_open)
	}

	return nil
}
