import time
from enum import Enum

import serial


class LEDColor(Enum):
    RED = 1
    BLUE = 2
    PURPLE = 3
    GREEN = 4
    GREEN_YELLOW = 5
    LIGHT_BLUE = 6
    WHITE = 7


class LEDMode(Enum):
    BLINK = 1
    ON = 2
    OFF = 4


class R503LED:
    def __init__(self, port="/dev/ttyS0", baudrate=57600):
        """Initialize R503 LED controller"""
        self.port = port
        self.baudrate = baudrate
        self.ser = None

    def __enter__(self):
        """Context manager entry for 'with' statement"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit for 'with' statement"""
        self.disconnect()

    def connect(self):
        """Connect to the R503 sensor"""
        if self.ser is None or not self.ser.is_open:
            self.ser = serial.Serial(port=self.port, baudrate=self.baudrate, timeout=1)
            time.sleep(0.1)  # Give the serial connection time to initialize

    def disconnect(self):
        """Disconnect from the R503 sensor"""
        if self.ser and self.ser.is_open:
            self.ser.close()

    def calculate_checksum(self, data):
        """Calculate checksum for R503 commands"""
        checksum = sum(data)
        # Return high and low bytes
        return [(checksum >> 8) & 0xFF, checksum & 0xFF]

    def send_command(self, instruction, p1=0, p2=0, p3=0, p4=0):
        """Send a command to the R503 sensor"""
        # Standard header for R503
        header = [0xEF, 0x01, 0xFF, 0xFF, 0xFF, 0xFF]

        # Package identifier: 0x01 = command packet
        identifier = [0x01]

        # All parameters
        parameter = [p1, p2, p3, p4]

        # Calculate length (instruction + parameter bytes + 2 checksum bytes)
        length = 1 + len(parameter) + 2
        length_bytes = [0x00, length]

        # Prepare command without checksum
        command_without_checksum = identifier + length_bytes + [instruction] + parameter

        # Calculate checksum
        checksum = self.calculate_checksum(command_without_checksum)

        # Complete command
        command = header + command_without_checksum + checksum

        # Send command
        self.ser.write(bytes(command))

        # Wait for response
        time.sleep(0.1)

        # Read response if any
        if self.ser.in_waiting:
            response = list(self.ser.read(self.ser.in_waiting))
            return response
        return None

    def control_led(self, mode, color):
        """
        Control the LED with the specified mode and color

        Args:
            mode (LEDMode): The LED mode (BLINK, ON, OFF)
            color (LEDColor): The LED color

        Returns:
            The response from the sensor, if any
        """
        # Check if mode and color are enum values
        if isinstance(mode, LEDMode):
            mode = mode.value

        if isinstance(color, LEDColor):
            color = color.value

        # LED control instruction for R503 is 0x35
        instruction = 0x35

        # Send the command with the appropriate parameters
        # p1 = mode, p2 = 0, p3 = color, p4 = 0
        return self.send_command(instruction, mode, 0, color, 0)

    # Convenience methods
    def led_on(self, color=LEDColor.RED):
        """Turn LED on with specified color"""
        return self.control_led(LEDMode.ON, color)

    def led_off(self, color=LEDColor.BLUE):
        """Turn LED off (color doesn't matter much but needs to be specified)"""
        return self.control_led(LEDMode.OFF, color)

    def led_blink(self, color=LEDColor.RED):
        """Blink LED with specified color"""
        return self.control_led(LEDMode.BLINK, color)


# Simple command-line interface if run as a script
if __name__ == "__main__":
    import argparse

    # Set up command line argument parser
    parser = argparse.ArgumentParser(description="Control R503 fingerprint sensor LED")
    parser.add_argument("--port", default="/dev/ttyS0", help="Serial port (default: /dev/ttyS0)")
    parser.add_argument("--baudrate", type=int, default=57600, help="Baudrate (default: 57600)")
    parser.add_argument("--mode", choices=["blink", "on", "off"], required=True, help="LED mode: blink, on, or off")
    parser.add_argument(
        "--color",
        choices=["red", "blue", "purple", "green", "green_yellow", "light_blue", "white"],
        default="red",
        help="LED color (default: red)",
    )

    # Parse arguments
    args = parser.parse_args()

    # Map string arguments to enum values
    mode_map = {"blink": LEDMode.BLINK, "on": LEDMode.ON, "off": LEDMode.OFF}

    color_map = {
        "red": LEDColor.RED,
        "blue": LEDColor.BLUE,
        "purple": LEDColor.PURPLE,
        "green": LEDColor.GREEN,
        "green_yellow": LEDColor.GREEN_YELLOW,
        "light_blue": LEDColor.LIGHT_BLUE,
        "white": LEDColor.WHITE,
    }

    # Control the LED
    try:
        with R503LED(args.port, args.baudrate) as led:
            print(f"Controlling LED: mode={args.mode}, color={args.color}")
            led.control_led(mode_map[args.mode], color_map[args.color])
            print("Command sent successfully")
    except Exception as e:
        print(f"Error: {e}")
        exit(1)
