import time
import logging
import tkinter as tk
from pynput import keyboard
import string
import threading
import win32ui
import subprocess
import win32gui
import win32con

TYPING_THRESHOLD = 0.019
DEBOUNCE_TIME = 0.5
LONG_PRESS_THRESHOLD = 1.0
IGNORED_KEY_GAP = 0.014
PASSWORD = "123"
last_key_time = None
last_trigger_time = None  
last_key = None  
key_press_duration = {}
listener = None
entered_password = ""
is_password_prompt_active = False
fast_typing_count = 0  

logging.basicConfig(filename='keystroke_log.log', level=logging.DEBUG,
                    format='%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

console_handler = logging.StreamHandler()  # Handler for console output
console_handler.setLevel(logging.DEBUG)  # Set console handler to DEBUG level
console_formatter = logging.Formatter('%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
console_handler.setFormatter(console_formatter)

logging.getLogger().addHandler(console_handler)  # Add the console handler to the logger

def log_event(message):
    logging.debug(message)

def is_valid_key(key):
    try:
        if isinstance(key, keyboard.KeyCode):
            char = key.char
            return char is not None and (char.isalnum() or char in string.punctuation)
        return False
    except AttributeError:
        return False

def show_password_prompt():
    global entered_password, is_password_prompt_active
    is_password_prompt_active = True
    window = tk.Toplevel()
    window.title("Password Prompt")
    window.geometry("400x300")
    window.protocol("WM_DELETE_WINDOW", lambda: None)
    window.attributes("-topmost", True)
    window.grab_set()

    label = tk.Label(window, text="Check the notepad for the executed script.\nEnter Password:")
    label.pack(pady=10)

    password_entry = tk.Entry(window, show="*")
    password_entry.pack(pady=10)
    password_entry.focus_set()

    result_label = tk.Label(window, text="", fg="red")
    result_label.pack(pady=5)

    def on_submit(event=None):
        global entered_password, is_password_prompt_active
        entered_password = password_entry.get()
        if entered_password == PASSWORD:
            log_event(f"Password entered correctly: {entered_password}")
            print("Password entered correctly! Access granted.")
            window.destroy()
        else:
            log_event(f"Incorrect password attempt: {entered_password}")
            print("Incorrect password entered.")
            result_label.config(text="Incorrect password, please try again.")
            password_entry.delete(0, tk.END)
        is_password_prompt_active = False

    submit_button = tk.Button(window, text="Submit", command=on_submit)
    submit_button.pack(pady=10)
    window.bind("<Return>", on_submit)

def on_press(key):
    global last_key_time, last_trigger_time, last_key, key_press_duration, fast_typing_count
    if is_password_prompt_active:
        return

    current_time = time.time()

    if last_key_time:
        time_diff = current_time - last_key_time
        if time_diff < IGNORED_KEY_GAP:
            return

    if key in key_press_duration:
        key_press_duration[key] = current_time - key_press_duration[key]
    else:
        key_press_duration[key] = current_time

    if not is_valid_key(key):
        return

    if last_key_time:
        time_diff = current_time - last_key_time
        if time_diff < TYPING_THRESHOLD:
            fast_typing_count += 1  
            if fast_typing_count >= 2:
                if last_trigger_time is None or (current_time - last_trigger_time > DEBOUNCE_TIME):
                    log_event("Fast typing detected! Triggering password entry...")
                    print("Fast typing detected! Triggering password entry...")
                    win32ui.MessageBox("Someone might be trying to inject keystrokes into your computer.\nPlease check your ports or any strange programs running.\nEnter your Password to unlock keyboard.", "KeyInjection Detected",4096)
                    show_password_prompt()
                    open_notepad_and_focus()
                    last_trigger_time = current_time
        else:
            fast_typing_count = 0
            log_event(f"Time between keys: {time_diff:.4f} seconds")
    else:
        log_event("First key press detected")

    last_key_time = current_time
    last_key = key

def on_release(key):
    if key == keyboard.Key.esc:
        return False

def start_listener():
    global listener
    listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    listener.start()

def stop_listener():
    global listener
    if listener:
        listener.stop()

def toggle_monitoring(button, label):
    if label["text"] == "Key monitoring is off":
        label.config(text="Key monitoring is on")
        button.config(text="Turn Off Monitoring")
        listener_thread = threading.Thread(target=start_listener)
        listener_thread.daemon = True
        listener_thread.start()
    else:
        label.config(text="Key monitoring is off")
        button.config(text="Turn On Monitoring")
        stop_listener()

def open_notepad_and_focus():
    """Opens Notepad and brings it into focus."""
    subprocess.Popen("notepad.exe")
    
    time.sleep(1)

    def bring_notepad_to_foreground():
        hwnd = win32gui.FindWindow(None, "Untitled - Notepad")
        if hwnd != 0:
            win32gui.SetForegroundWindow(hwnd)
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)

    bring_notepad_to_foreground()

def start_gui():
    root = tk.Tk()
    root.title("Key Press Monitor")
    root.geometry("400x200")
    
    message_label = tk.Label(root, text="Key monitoring is off", font=("Arial", 14))
    message_label.pack(pady=20)

    toggle_button = tk.Button(root, text="Turn On Monitoring", 
                              command=lambda: toggle_monitoring(toggle_button, message_label))
    toggle_button.pack(pady=10)

    root.mainloop()

start_gui()
