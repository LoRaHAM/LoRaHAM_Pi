import tkinter as tk
from tkinter import scrolledtext, messagebox
import time
from SX127x.LoRa import *
from SX127x.board_config import BOARD
import os  # für die Überprüfung, ob die Datei existiert

BOARD.setup()
BOARD.reset()

# Definition der Einstellungen und Farben zu Beginn
SEND_FREQ = 433.775  # Sendefrequenz in MHz
RECV_FREQ = 433.900  # Empfangsfrequenz in MHz
BW = BW.BW125  # Bandbreite
CODING_RATE = CODING_RATE.CR4_5  # Codierungsrate
SPREADING_FACTOR = 12  # Spreizfaktor

MESSAGES_FILE = "messages433.txt"
WELCOME_MESSAGE = "Willkommen im Amateurfunk LoRa-Chat!"

# Farbkonfiguration und Textoptionen
SEND_COLOR = "blue"  # Farbe für gesendete Nachrichten
RECEIVE_COLOR = "brown"  # Farbe für empfangene Nachrichten
BG_COLOR = "lightgray"  # Hintergrundfarbe des Chat-Fensters
TEXT_COLOR = "black"  # Textfarbe für Nachrichten
SENDER_NAME = "Ich"  # Text für gesendete Nachrichten
RECEIVER_NAME = "Jemand"  # Text für empfangene Nachrichten

class LoRaSender(LoRa):
    def __init__(self, verbose=False, incoming_message_callback=None):
        super(LoRaSender, self).__init__(verbose)
        self.set_mode(MODE.SLEEP)
        self.set_dio_mapping([0] * 6)
        self.set_freq(RECV_FREQ)  # Empfangsfrequenz wird hier gesetzt
        self.set_mode(MODE.RXCONT)
        
        # Speichern des Callback-Handlers für eingehende Nachrichten
        self.incoming_message_callback = incoming_message_callback

    def on_rx_done(self):
        print("\nRxDone")
        payload = self.read_payload(nocheck=True)
        message = repr(bytes(payload))[2:-1]  # Die empfangene Nachricht in lesbare Form umwandeln
        print(message)

        time.sleep(0.2)
        self.clear_irq_flags(RxDone=1)
        self.reset_ptr_rx()
        self.set_mode(MODE.RXCONT)

        # Nachricht in die Datei schreiben
        self.save_message(message, 'received')
        
        # Wenn ein Callback definiert ist, rufe es auf
        if self.incoming_message_callback:
            self.incoming_message_callback(message)

    def send_message(self, message):
        self.set_mode(MODE.SLEEP)
        self.set_freq(SEND_FREQ)  # Sendefrequenz wird hier gesetzt
        
        # Erstelle die drei zusätzlichen Bytes
        prefix = [ord('<'), 255, 1]
        
        # Konvertiere die Nachricht in eine Liste von Bytes und hänge sie an die Prefix-Bytes an
        payload = prefix + [ord(c) for c in message]
        
        self.write_payload(payload)
        self.set_mode(MODE.TX)
        print(f"Message sent: {message}")
        self.set_mode(MODE.SLEEP)
        self.set_freq(RECV_FREQ)  # Empfangsfrequenz zurücksetzen
        self.set_mode(MODE.RXCONT)

        # Nachricht in die Datei schreiben
        self.save_message(message, 'sent')

    def save_message(self, message, direction):
        """Speichert eine Nachricht in der Datei."""
        with open(MESSAGES_FILE, 'a') as file:
            file.write(f"{direction}: {message}\n")

    def load_messages(self):
        """Lädt alle Nachrichten aus der Datei und gibt sie zurück."""
        try:
            with open(MESSAGES_FILE, 'r') as file:
                return file.readlines()
        except FileNotFoundError:
            return []

    def start(self, message):
        print("Start..")

class ChatApp():
    def __init__(self, root):
        self.root = root
        self.root.title("LoRaHAM Pi-Chat")
        self.root.geometry("800x500")
        self.root.resizable(True, True)
        self.center_window(self.root)

        # Chat-Bereich mit konfigurierbarem Hintergrund
        self.chat_area = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, state=tk.DISABLED, 
                                                     height=20, width=60, bg=BG_COLOR, fg=TEXT_COLOR)
        self.chat_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Tag-Konfigurationen für Farben der Nachrichten
        self.chat_area.tag_configure("right", justify="right", foreground=SEND_COLOR)
        self.chat_area.tag_configure("left", justify="left", foreground=RECEIVE_COLOR)
        self.chat_area.tag_configure("message", foreground=TEXT_COLOR)

        # Eingabefeld für Nachrichten
        self.input_frame = tk.Frame(self.root)
        self.input_frame.pack(padx=10, pady=(0, 10), fill=tk.X, side=tk.BOTTOM)

        self.message_entry = tk.Entry(self.input_frame, width=48)
        self.message_entry.pack(padx=10, pady=5, side=tk.LEFT, fill=tk.X, expand=True)

        self.send_button = tk.Button(self.input_frame, text="Senden", command=self.send_message)
        self.send_button.pack(padx=10, pady=5, side=tk.RIGHT)

        self.message_entry.bind("<Return>", self.send_message_event)

        self.lora = LoRaSender(verbose=False, incoming_message_callback=self.incoming_message)
        self.lora.set_pa_config(pa_select=1, max_power=21, output_power=20)
        self.lora.set_bw(BW)
        self.lora.set_coding_rate(CODING_RATE)
        self.lora.set_spreading_factor(SPREADING_FACTOR)

        self.lora.set_rx_crc(True)
        self.lora.set_low_data_rate_optim(True)
        self.lora.start("Start")

        # Nachrichten beim Start aus der Datei laden und anzeigen
        self.load_saved_messages()

        # Wenn es der erste Start ist (Datei existiert nicht), füge die Willkommensnachricht hinzu
        if not os.path.exists(MESSAGES_FILE):
            self.lora.save_message(WELCOME_MESSAGE, 'received')
            self.display_message(WELCOME_MESSAGE, "left")

        self.menü_leiste = tk.Menu(self.root)
        self.root.config(menu=self.menü_leiste)

        # Menü für LoRa-Einstellungen
        # self.settings_menu = tk.Menu(self.menü_leiste)
        # self.menü_leiste.add_cascade(label="Einstellungen", menu=self.settings_menu)
        # self.settings_menu.add_command(label="LoRa Einstellungen", command=self.open_lora_settings)

        # Menü für Chat-Einstellungen
        self.chat_settings_menu = tk.Menu(self.menü_leiste)
        self.menü_leiste.add_cascade(label="Chat Einstellungen", menu=self.chat_settings_menu)
        self.chat_settings_menu.add_command(label="Farben und Texte anpassen", command=self.open_chat_settings)

        # Fenster-Attribut für Chat-Einstellungen initialisieren
        self.settings_window = None

    def open_lora_settings(self):
        """Zeigt ein Fenster zum Anpassen der LoRa-Einstellungen."""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("LoRa Einstellungen")

        # Widgets zum Anpassen der Parameter
        tk.Label(settings_window, text="Sendefrequenz (MHz):").pack(pady=5)
        self.send_freq_entry = tk.Entry(settings_window)
        self.send_freq_entry.insert(tk.END, str(SEND_FREQ))
        self.send_freq_entry.pack(pady=5)

        tk.Label(settings_window, text="Empfangsfrequenz (MHz):").pack(pady=5)
        self.recv_freq_entry = tk.Entry(settings_window)
        self.recv_freq_entry.insert(tk.END, str(RECV_FREQ))
        self.recv_freq_entry.pack(pady=5)

        tk.Label(settings_window, text="Bandbreite:").pack(pady=5)
        self.bw_entry = tk.Entry(settings_window)
        self.bw_entry.insert(tk.END, str(BW))
        self.bw_entry.pack(pady=5)

        tk.Label(settings_window, text="Codierungsrate:").pack(pady=5)
        self.coding_rate_entry = tk.Entry(settings_window)
        self.coding_rate_entry.insert(tk.END, str(CODING_RATE))
        self.coding_rate_entry.pack(pady=5)

        tk.Label(settings_window, text="Spreizfaktor:").pack(pady=5)
        self.spreading_factor_entry = tk.Entry(settings_window)
        self.spreading_factor_entry.insert(tk.END, str(SPREADING_FACTOR))
        self.spreading_factor_entry.pack(pady=5)

        tk.Button(settings_window, text="Speichern", command=self.save_lora_settings).pack(pady=10)

    def save_lora_settings(self):
        """Speichert die aktualisierten LoRa-Einstellungen."""
        send_freq = self.send_freq_entry.get()
        recv_freq = self.recv_freq_entry.get()
        bandwidth = self.bw_entry.get()
        coding_rate = self.coding_rate_entry.get()
        spreading_factor = self.spreading_factor_entry.get()

        self.lora.update_lora_settings(send_freq, recv_freq, bandwidth, coding_rate, spreading_factor)

    def open_chat_settings(self):
        """Zeigt ein Fenster zum Anpassen der Chat-Einstellungen (Farben und Texte)."""
        if self.settings_window is not None and self.settings_window.winfo_exists():
            self.settings_window.lift()
            return

        self.settings_window = tk.Toplevel(self.root)
        self.settings_window.title("Chat Einstellungen")

        # Dropdown für Farben
        color_options = ["lightgray","brown","green", "blue", "red", "yellow", "black", "white"]

        tk.Label(self.settings_window, text="Farbe für gesendete Nachrichten:").pack(pady=5)
        self.send_color_var = tk.StringVar(value=SEND_COLOR)
        self.send_color_menu = tk.OptionMenu(self.settings_window, self.send_color_var, *color_options)
        self.send_color_menu.pack(pady=5)

        tk.Label(self.settings_window, text="Farbe für empfangene Nachrichten:").pack(pady=5)
        self.recv_color_var = tk.StringVar(value=RECEIVE_COLOR)
        self.recv_color_menu = tk.OptionMenu(self.settings_window, self.recv_color_var, *color_options)
        self.recv_color_menu.pack(pady=5)

        tk.Label(self.settings_window, text="Hintergrundfarbe:").pack(pady=5)
        self.bg_color_var = tk.StringVar(value=BG_COLOR)
        self.bg_color_menu = tk.OptionMenu(self.settings_window, self.bg_color_var, *color_options)
        self.bg_color_menu.pack(pady=5)

        tk.Label(self.settings_window, text="Textfarbe:").pack(pady=5)
        self.text_color_var = tk.StringVar(value=TEXT_COLOR)
        self.text_color_menu = tk.OptionMenu(self.settings_window, self.text_color_var, *color_options)
        self.text_color_menu.pack(pady=5)

        tk.Label(self.settings_window, text="Text für 'Ich':").pack(pady=5)
        self.sender_name_entry = tk.Entry(self.settings_window)
        self.sender_name_entry.insert(tk.END, SENDER_NAME)
        self.sender_name_entry.pack(pady=5)

        tk.Label(self.settings_window, text="Text für 'Jemand':").pack(pady=5)
        self.receiver_name_entry = tk.Entry(self.settings_window)
        self.receiver_name_entry.insert(tk.END, RECEIVER_NAME)
        self.receiver_name_entry.pack(pady=5)

        tk.Button(self.settings_window, text="Speichern", command=self.save_chat_settings).pack(pady=10)

    def save_chat_settings(self):
        """Speichert die aktualisierten Chat-Einstellungen (Farben und Texte) und schließt das Fenster."""
        global SEND_COLOR, RECEIVE_COLOR, BG_COLOR, TEXT_COLOR, SENDER_NAME, RECEIVER_NAME

        SEND_COLOR = self.send_color_var.get()
        RECEIVE_COLOR = self.recv_color_var.get()
        BG_COLOR = self.bg_color_var.get()
        TEXT_COLOR = self.text_color_var.get()
        SENDER_NAME = self.sender_name_entry.get()
        RECEIVER_NAME = self.receiver_name_entry.get()

        # Setze die neuen Farben für das Chat-Fenster und die Nachrichten
        self.chat_area.config(bg=BG_COLOR, fg=TEXT_COLOR)
        self.chat_area.tag_configure("right", justify="right", foreground=SEND_COLOR)
        self.chat_area.tag_configure("left", justify="left", foreground=RECEIVE_COLOR)
        self.chat_area.tag_configure("message", foreground=TEXT_COLOR)

        # Fenster schließen
        if self.settings_window is not None and self.settings_window.winfo_exists():
            self.settings_window.destroy()
            self.settings_window = None

    def send_message(self, event=None):
        message = self.message_entry.get()
        if message != "":
            self.lora.send_message(message)
            self.display_message(message, "right")
            self.message_entry.delete(0, tk.END)

    def send_message_event(self, event):
        self.send_message()

    def display_message(self, message, position):
        self.chat_area.config(state=tk.NORMAL)

        if position == "right":
            self.chat_area.insert(tk.END, f"{SENDER_NAME}: ", "right")
        else:
            self.chat_area.insert(tk.END, f"{RECEIVER_NAME}: ", "left")
        
        self.chat_area.insert(tk.END, f"{message}\n", "message")
        self.chat_area.config(state=tk.DISABLED)
        self.chat_area.yview(tk.END)

    def incoming_message(self, message):
        """Verarbeitet eingehende Nachrichten."""
        self.display_message(message, "left")

    def load_saved_messages(self):
        """Lädt Nachrichten aus der Datei und zeigt sie im Chat-Fenster an."""
        messages = self.lora.load_messages()
        for message in messages:
            if message.startswith('sent'):
                self.display_message(message[6:].strip(), "right")
            elif message.startswith('received'):
                self.display_message(message[9:].strip(), "left")

    def center_window(self, window):
        window.update_idletasks()
        width = window.winfo_width()
        height = window.winfo_height()
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        position_top = int(screen_height / 2 - height / 2)
        position_right = int(screen_width / 2 - width / 2)
        window.geometry(f'{width}x{height}+{position_right}+{position_top}')

def main():
    root = tk.Tk()
    app = ChatApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
