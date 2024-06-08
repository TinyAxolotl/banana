EXEs=banana.elf banana.exe

all: tidy clean ${EXEs}

tidy:
	go mod tidy

banana.elf:
	go build -o banana.elf banana.go

banana.exe:
	GOOS=windows go build -o banana.exe banana.go

clean:
	go clean
	-rm ${EXEs}

run:
	go run banana.go -i live/addons.list -o live/AddOns/

install:
	GOBIN=~/.local/bin/ go install banana.go

install-steamos: banana.elf
	cp banana.elf /usr/bin/banana
	cp banana.timer banana.service /etc/systemd/system/
	systemctl enable banana.timer
	systemctl enable banana.service
