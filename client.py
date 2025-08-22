import bluetooth
import socket
import sys
import tkinter as tk
from tkinter import messagebox
from pystray import MenuItem as item, Icon as icon
from PIL import Image, ImageDraw
import threading

# --- Global variables ---
bt_socket = None
root = None  # To hold the tkinter root window
tray_icon = None # To hold the pystray icon instance

# --- System Tray Icon Creation ---
def create_image():
    """Creates a simple image to be used as the system tray icon."""
    width = 64
    height = 64
    # A simple blue and white design
    color1 = (0, 140, 186) 
    color2 = 'white'
    image = Image.new('RGB', (width, height), color1)
    dc = ImageDraw.Draw(image)
    # Draw a simple 'B' for Bluetooth
    dc.rectangle(((18, 10), (46, 20)), fill=color2)
    dc.rectangle(((18, 10), (28, 54)), fill=color2)
    dc.rectangle(((18, 30), (40, 40)), fill=color2)
    dc.rectangle(((18, 44), (46, 54)), fill=color2)
    return image

# --- Bluetooth Functions ---
def find_esp32_device(device_name="ESP32_Motor_Control"):
    """Scans for a Bluetooth device and returns its address."""
    print(f"Scanning for Bluetooth devices... Looking for '{device_name}'")
    try:
        nearby_devices = bluetooth.discover_devices(duration=8, lookup_names=True, flush_cache=True, lookup_class=False)
        for addr, name in nearby_devices:
            if device_name == name:
                print(f"Found '{name}' with address: {addr}")
                return addr
        print(f"Could not find a device named '{device_name}'.")
        return None
    except Exception as e:
        print(f"Error during device discovery: {e}")
        return None

def connect_to_device(target_address):
    """Establishes a Bluetooth connection."""
    global bt_socket
    port = 1
    print(f"Attempting to connect to {target_address} on Port {port}...")
    try:
        bt_socket = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
        bt_socket.connect((target_address, port))
        print("Successfully connected to the ESP32!")
        return True
    except socket.error as e:
        print(f"Socket Error: {e}")
        messagebox.showerror("Connection Failed", f"Could not connect to the ESP32.\nError: {e}")
        return False

def send_command(command):
    """Sends a command over the Bluetooth socket."""
    global bt_socket
    if bt_socket:
        try:
            bt_socket.send(command.encode('utf-8'))
            print(f"Sent: '{command}'")
        except socket.error as e:
            print(f"Failed to send command: {e}")
            messagebox.showerror("Send Error", "Lost connection to the ESP32.")

# --- GUI and Tray Functions ---

def show_window():
    """Shows the main tkinter window."""
    global root
    # No need to stop the icon, just show the window.
    root.deiconify() 

def on_closing_window():
    """Hides the window when the 'X' is clicked instead of closing."""
    global root
    # No need to restart the icon thread, as it's always running.
    root.withdraw()

def exit_application():
    """Closes socket, stops tray icon, and exits the app."""
    global bt_socket, tray_icon, root
    print("Closing application...")
    if tray_icon:
        tray_icon.stop()
    if bt_socket:
        bt_socket.close()
    if root:
        root.destroy()
    sys.exit(0)

def setup_gui():
    """Creates and configures the tkinter GUI."""
    global root
    root = tk.Tk()
    root.title("Motor Controller")
    root.geometry("300x400")
    root.resizable(False, False)

    status_label = tk.Label(root, text="Connected", fg="green", font=("Helvetica", 12))
    status_label.pack(pady=10)

    forward_btn = tk.Button(root, text="FORWARD", font=("Helvetica", 20, "bold"), bg="#4CAF50", fg="white", relief="raised")
    forward_btn.pack(expand=True, fill="both", padx=20, pady=10)
    forward_btn.bind("<ButtonPress-1>", lambda e: send_command('f'))
    forward_btn.bind("<ButtonRelease-1>", lambda e: send_command('s'))

    backward_btn = tk.Button(root, text="BACKWARD", font=("Helvetica", 20, "bold"), bg="#008CBA", fg="white", relief="raised")
    backward_btn.pack(expand=True, fill="both", padx=20, pady=10)
    backward_btn.bind("<ButtonPress-1>", lambda e: send_command('b'))
    backward_btn.bind("<ButtonRelease-1>", lambda e: send_command('s'))
    
    root.protocol("WM_DELETE_WINDOW", on_closing_window)
    root.withdraw() # Start with the window hidden

def run_tray_icon():
    """Creates and runs the system tray icon in a non-blocking way."""
    global tray_icon
    image = 'icon.png'
    menu = (item('Show Controller', show_window, default=True), item('Exit', exit_application))
    tray_icon = icon("MotorController", image, "ESP32 Motor Controller", menu)
    tray_icon.run()

# --- Main Application ---
if __name__ == "__main__":
    esp32_address = find_esp32_device()
    
    if not esp32_address:
        messagebox.showerror("Device Not Found", "Could not find 'ESP32_Motor_Control'.")
        sys.exit(1)

    if connect_to_device(esp32_address):
        setup_gui() # Prepare the GUI window
        
        # Run the pystray icon in a separate thread so it doesn't block tkinter
        tray_thread = threading.Thread(target=run_tray_icon, daemon=True)
        tray_thread.start()
        
        # Start the tkinter main loop in the main thread
        root.mainloop()
