.PHONY: app kill red green red3 green3  off

APP_PORT=/dev/ttyS0
BAUD=57600

app:
	uv run app.py

kill:
	pkill -f '/home/pi/Desktop/TU/FingerprintR503/.venv/bin/python3 app.py'

red:
	uv run fingerprint/r503led.py --port $(APP_PORT) --baudrate $(BAUD) --mode on --color red

green:
	uv run fingerprint/r503led.py --port $(APP_PORT) --baudrate $(BAUD) --mode on --color green

red3:
	uv run fingerprint/r503led.py --port $(APP_PORT) --baudrate $(BAUD) --mode on --color red --duration 3

green3:
	uv run fingerprint/r503led.py --port $(APP_PORT) --baudrate $(BAUD) --mode on --color green --duration 3

off:
	uv run fingerprint/r503led.py --port $(APP_PORT) --baudrate $(BAUD) --mode off --color red
