EXEs=banana.elf

all: tidy clean ${EXEs}

tidy:
	go mod tidy

banana.elf:
	go build -o banana.elf banana.go

clean:
	go clean
	-rm ${EXEs}

run:
	go run banana.go -h

install:
	GOBIN=~/.local/bin/ go install banana.go

install-steamos: banana.elf
	cp banana.elf /usr/bin/banana
	cp banana.timer banana.service /etc/systemd/system/
	systemctl enable banana.timer
	systemctl enable banana.service
