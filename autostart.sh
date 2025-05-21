#!/usr/bin/env bash

LOG="/home/pi/Desktop/TU/FingerprintR503/autostart.log"

# prepend empty line + timestamp
{
  echo
  date --iso-8601=seconds
} >> "$LOG"

# redirect all stdout/stderr to the log
exec >> "$LOG" 2>&1

# Navigate to project directory
cd /home/pi/Desktop/TU/FingerprintR503 || exit 1

# Turn LED red for 3 s
/usr/bin/make red3

# Try to kill the app, in case it is already running
pkill -f '/home/pi/Desktop/TU/FingerprintR503/.venv/bin/python3 app.py'

# Launch app in background
/usr/bin/make app &

# Give the app a moment to start
sleep 2

# Turn LED green for 3 s
/usr/bin/make green3
