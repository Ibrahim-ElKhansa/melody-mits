import serial
import time

# Update this port to match your system (e.g., "COM5" on Windows, "/dev/tty.SLAB_USBtoUART" on macOS,
# or "/dev/rfcomm0" on Linux if you bind the device with rfcomm)
bluetooth_port = "COM4"  
baud_rate = 115200

try:
    ser = serial.Serial(bluetooth_port, baud_rate, timeout=1)
    print(f"Connected to {bluetooth_port} at {baud_rate} baud.")
except Exception as e:
    print(f"Error opening serial port: {e}")
    exit(1)

time.sleep(2)  # Allow time for the connection to stabilize

try:
    while True:
        line = ser.readline().decode('utf-8').rstrip()
        if line:
            print(line)
except KeyboardInterrupt:
    print("Exiting...")

ser.close()