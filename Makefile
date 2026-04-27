PIO ?= /home/hitcrt/.platformio/penv/bin/pio
ENV ?= esp32-s3-devkitc-1
PORT ?=

.PHONY: all build upload upload-port monitor clean devices erase help

all: build

build:
	$(PIO) run -e $(ENV)

upload:
	$(PIO) run -e $(ENV) -t upload

upload-port:
	@test -n "$(PORT)" || (echo "Usage: make upload-port PORT=/dev/ttyACM0" && exit 1)
	$(PIO) run -e $(ENV) -t upload --upload-port $(PORT)

monitor:
	$(PIO) device monitor -e $(ENV)

clean:
	$(PIO) run -e $(ENV) -t clean

devices:
	$(PIO) device list

erase:
	$(PIO) run -e $(ENV) -t erase

help:
	@echo "Targets:"
	@echo "  make build                         Build firmware"
	@echo "  make upload                        Build and upload using auto-detected port"
	@echo "  make upload-port PORT=/dev/ttyACM0 Build and upload using a specific port"
	@echo "  make monitor                       Open serial monitor"
	@echo "  make devices                       List serial devices"
	@echo "  make clean                         Clean build output"
	@echo "  make erase                         Erase flash"
	@echo ""
	@echo "Variables:"
	@echo "  PIO=$(PIO)"
	@echo "  ENV=$(ENV)"
