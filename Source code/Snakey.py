import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
import pyttsx3
import json
import os
import pygame
import webbrowser
import random
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Initialize settings file
SETTINGS_FILE = "SnakeyData.json"
DEFAULT_SETTINGS = {
    "image": None,
    "image_moving": None,
    "speech_enabled": True,
    "user_data": {},
    "PLAYED_BEFORE": "no",
}

def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        save_settings(DEFAULT_SETTINGS)
    try:
        with open(SETTINGS_FILE, "r") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        logging.error(f"Failed to load settings: {e}")
        data = DEFAULT_SETTINGS
    
    for key, value in DEFAULT_SETTINGS.items():
        if key not in data:
            data[key] = value
    
    return data

def save_settings(data):
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        logging.error(f"Failed to save settings: {e}")

# Load initial settings
settings = load_settings()

# Speech Engine
engine = pyttsx3.init()

def speak(text):
    if settings.get("speech_enabled", True):
        try:
            engine.say(text)
            engine.runAndWait()
        except Exception as e:
            logging.error(f"Speech engine error: {e}")

# Initialize pygame for sound
try:
    pygame.mixer.init()
except pygame.error as e:
    logging.warning(f"Pygame mixer initialization failed: {e}")

def play_intro_music():
    try:
        music_path = os.path.join(os.path.dirname(__file__), "Snakey_intro.wav")
        if not os.path.exists(music_path):
            raise FileNotFoundError(f"No file '{music_path}' found.")
        pygame.mixer.music.load(music_path)
        pygame.mixer.music.play(-1)  # Loop the intro music
    except Exception as e:
        logging.error(f"Failed to play intro music: {e}")

def stop_intro_music():
    try:
        pygame.mixer.music.stop()
    except Exception as e:
        logging.error(f"Failed to stop music: {e}")

class SnakeyApp:
    def __init__(self, root):
        self.root = root
        self.root.overrideredirect(True)
        self.root.geometry("200x200+500+300")
        self.root.attributes("-topmost", True)  # Always on top

        try:
            self.root.attributes("-transparentcolor", "white")
        except tk.TclError:
            logging.warning("Transparent color not supported on this system.")

        self.canvas = tk.Canvas(root, width=200, height=200, bg='white', highlightthickness=0)
        self.canvas.pack(expand=True)

        self.snake_id = None
        self.update_image(settings.get("image"))

        self.schedule_random_movement()
        self.schedule_talk()

        self.canvas.bind("<Button-1>", self.start_drag)
        self.canvas.bind("<B1-Motion>", self.drag)

        self.menu = tk.Menu(root, tearoff=0)
        self.menu.add_command(label="Settings", command=self.open_settings)
        self.menu.add_command(label="Surf the Web!", command=self.surf_web)
        self.menu.add_command(label="Quit", command=root.destroy)
        self.menu.add_command(label="Tell me a joke!", command=self.tell_joke)
        self.menu.add_command(label="Talk!", command=self.open_tts_window)  # TTS button
        self.canvas.bind("<Button-3>", self.show_menu)

        self.greet_user()

    def schedule_random_movement(self):
        # Move more often (every 5-15 seconds)
        delay = random.randint(5000, 15000)
        self.root.after(delay, self.random_move)

    def random_move(self):
        # Move up to 1000 pixels away from current position
        current_x = self.root.winfo_x()
        current_y = self.root.winfo_y()

        move_x = random.randint(-1000, 1000)
        move_y = random.randint(-1000, 1000)

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        new_x = min(max(0, current_x + move_x), screen_width - 200)
        new_y = min(max(0, current_y + move_y), screen_height - 200)

        self.glide_to_new_position(current_x, current_y, new_x, new_y)

        # Show the moving image for 5 seconds
        self.update_image(settings.get("image_moving"))
        
        # Switch back to "not moving" image after 5 seconds
        self.root.after(5000, self.update_image, settings.get("image"))
        
        self.schedule_random_movement()

    def glide_to_new_position(self, start_x, start_y, end_x, end_y, duration=5000, steps=100):
        # Calculate the total number of steps based on the duration
        step_delay = duration // steps
        step_x = (end_x - start_x) / steps
        step_y = (end_y - start_y) / steps

        def move_step(i):
            if i < steps:
                current_x = start_x + i * step_x
                current_y = start_y + i * step_y
                self.root.geometry(f"+{int(current_x)}+{int(current_y)}")
                self.root.after(step_delay, move_step, i + 1)

        move_step(0)

    def schedule_talk(self):
        # Talk every 10 seconds to 1 minute
        delay = random.randint(10000, 60000)
        self.root.after(delay, self.speak_random_phrase)

    def speak_random_phrase(self):
        phrases = [
            "nice computer you got here! can i have it?",
            "haha im digging into your files!",
            "An SSD? let me see!",
            "La la la la la",
            "haha im a little snakey guy"
        ]
        phrase = random.choice(phrases)
        speak(phrase)
        self.schedule_talk()

    def start_drag(self, event):
        self.start_x = event.x
        self.start_y = event.y

    def drag(self, event):
        x_offset = event.x - self.start_x
        y_offset = event.y - self.start_y
        new_x = self.root.winfo_x() + x_offset
        new_y = self.root.winfo_y() + y_offset
        self.root.geometry(f"+{new_x}+{new_y}")

    def show_menu(self, event):
        self.menu.post(event.x_root, event.y_root)

    def greet_user(self):
        if settings["PLAYED_BEFORE"] == "no":
            speak("Thanks for waking me up! My name's Snakey, and how about yours?")
            self.show_name_input()
            play_intro_music()  # Play intro music on first run
        else:
            name = settings["user_data"].get("name", "there")
            greeting = f"Hello there, {name}. It's nice to see you!"
            self.show_notification(greeting)
            speak(greeting)
            stop_intro_music()  # Stop the intro music if user has played before

    def show_name_input(self):
        name_input_window = tk.Toplevel(self.root)
        name_input_window.title("BFDC - Best Friend Data Collector")
        name_input_window.geometry("300x150")

        label = tk.Label(name_input_window, text="What's your name?")
        label.pack(pady=10)

        name_entry = tk.Entry(name_input_window)
        name_entry.pack(pady=5)

        def save_name():
            name = name_entry.get()
            if name:
                settings["user_data"]["name"] = name
                settings["PLAYED_BEFORE"] = "yes"
                save_settings(settings)
                speak(f"Nice to meet you, {name}!")
                name_input_window.after(2000, name_input_window.destroy)
                stop_intro_music()  # Stop the music once the name is entered

        tk.Button(name_input_window, text="Submit", command=save_name).pack(pady=10)

    def show_notification(self, text):
        notif = tk.Toplevel(self.root)
        notif.geometry("200x100+500+300")
        tk.Label(notif, text=text, wraplength=180).pack(expand=True)
        self.root.after(2000, notif.destroy)

    def open_settings(self):
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("300x200")

        def select_image():
            file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")])
            if file_path:
                settings["image"] = file_path
                save_settings(settings)
                self.update_image(file_path)

        tk.Button(settings_window, text="Select Image When Not Moving", command=select_image).pack(pady=5)

        def select_moving_image():
            file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")])
            if file_path:
                settings["image_moving"] = file_path
                save_settings(settings)

        tk.Button(settings_window, text="Select Image When Moving", command=select_moving_image).pack(pady=5)

        def clear_data():
            response = messagebox.askyesno("Clear Data", "Are you sure you want to clear all collected data?")
            if response:
                save_settings(DEFAULT_SETTINGS)
                self.root.quit()  # Close the app

        tk.Button(settings_window, text="Clear Collected Data", command=clear_data).pack(pady=5)

    def update_image(self, image_path):
        self.canvas.delete("all")
        if image_path:
            try:
                self.image = tk.PhotoImage(file=image_path)
                self.canvas.create_image(100, 100, image=self.image)
            except Exception as e:
                logging.error(f"Failed to load image: {e}")
        else:
            self.snake_id = self.canvas.create_oval(40, 40, 160, 160, fill="green")

    def surf_web(self):
        webbrowser.open("https://www.google.com")

    def tell_joke(self):
        jokes = [
            "Why don't skeletons fight each other? They don't have the guts.",
            "Why can't your nose be 12 inches long? Because then it would be a foot!",
            "I'm reading a book on anti-gravity. It's impossible to put down!"
        ]
        joke = random.choice(jokes)
        speak(joke)
        self.show_notification(joke)

    def open_tts_window(self):
        tts_window = tk.Toplevel(self.root)
        tts_window.title("Text-to-Speech")

        label = tk.Label(tts_window, text="Type something to say:")
        label.pack(pady=10)

        text_entry = tk.Entry(tts_window)
        text_entry.pack(pady=5)

        def speak_text():
            text = text_entry.get()
            if text:
                speak(text)

        tk.Button(tts_window, text="Speak", command=speak_text).pack(pady=10)


def run():
    root = tk.Tk()
    app = SnakeyApp(root)
    root.mainloop()


if __name__ == "__main__":
    run()
