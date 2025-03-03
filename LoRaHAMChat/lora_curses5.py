import curses
import time
import threading
from SX127x.LoRa import *
from SX127x.board_config import BOARD
from termcolor import colored
import re

# Text, den du hinzufügen möchtest. Dadurch ist das Chatten direkt möglich.
mein_text = "DL0xxx>APRS,WIDE1-1::" # Rufzeichenziel wird angehängt und formatiert, da es immer 9 Zeichen haben muss


# LoRa initialisieren
BOARD.setup()
BOARD.reset()

SEND_FREQ = 433.775  # Sendefrequenz in MHz
RECV_FREQ = 433.900  # Empfangsfrequenz in MHz
BW = BW.BW125  # Bandbreite
CODING_RATE = CODING_RATE.CR4_5  # Codierungsrate
SPREADING_FACTOR = 12  # Spreizfaktor

MESSAGES_FILE = "messages433_1.txt"

# Rufzeichenliste gefüllt mit Platzhaltern zur Demo oder als Adressbuchvorlage
callsigns = ["Calls:", "", "ALL", "APRSPH", "DC2WA-15"] #, "DB4XYZ", "DL2DEF", "DK5GHJ", "DM0KLM"]

# Definiere Fenster als globale Variablen
callsign_win = None
chat_win = None

# Zielrufzeichen definieren (kann durch Benutzer geändert werden)
destination_callsign = "ALL      "

def extract_callsign(message):
    """
    Extrahiert das Rufzeichen aus dem empfangenen String.
    Erwartetes Format: < 0xff 0x01 CALLSIGN>
    """
    message = message[9:]
    match = re.search(r'([A-Za-z0-9-]+)>', message)
    return match.group(1) if match else None

class LoRaSender(LoRa):
    def __init__(self, verbose=False):
        super(LoRaSender, self).__init__(verbose)
        self.set_mode(MODE.SLEEP)
        self.set_dio_mapping([0] * 6)
        self.set_freq(RECV_FREQ)
        self.set_mode(MODE.RXCONT)

    def on_rx_done(self):
        payload = self.read_payload(nocheck=True)
        message = repr(bytes(payload))[2:-1]
		
        # Extrahiere das Rufzeichen
        callsign = extract_callsign(message)
        if callsign:
            if callsign not in callsigns:
                callsigns.append(callsign)
                update_callsigns(callsign_win)

        messages.append(("Jemand", message))
        save_message("Jemand", message)
        update_chat_window(chat_win)

        time.sleep(0.2)
        self.clear_irq_flags(RxDone=1)
        self.reset_ptr_rx()
        self.set_mode(MODE.RXCONT)

    def send_message(self, message):
        self.set_mode(MODE.SLEEP)
        self.set_freq(SEND_FREQ)
        if not message.strip():
            return
        
        # prefix APRS_header. Wenn du direkt für Chat nutzen willst, kommentiere die Zeile aus und ändere die Frequenzen
        # prefix = ""

        end_char = ":"
        prefix = [ord('<'), 255, 1] # auskommentieren wenn obere Zeile drin ist

        prefix.extend([ord(char) for char in mein_text])
        prefix.extend([ord(char) for char in destination_callsign])
        prefix.extend([ord(char) for char in end_char])
        
        payload = prefix + [ord(c) for c in message]
        
        self.write_payload(payload)
        self.set_mode(MODE.TX)

        messages.append(("Ich", message))
        save_message("Ich", message)

        update_chat_window(chat_win)

        #print(message)        
        self.set_mode(MODE.SLEEP)
        self.set_freq(RECV_FREQ)
        self.set_mode(MODE.RXCONT)

def save_message(sender, message):
    with open(MESSAGES_FILE, 'a') as file:
        file.write(f"{sender}: {message}\n")

def load_messages():
    try:
        with open(MESSAGES_FILE, 'r') as file:
            for line in file:
                if line.startswith("Ich"):
                    messages.append(("Ich", line[4:].strip()))
                elif line.startswith("Jemand"):
                    messages.append(("Jemand", line[7:].strip()))

    except FileNotFoundError:
        pass
		
	
	
# Globale Variablen

messages = []
lora = LoRaSender(verbose=False)
load_messages()

def setup_window(stdscr):
    global callsign_win, chat_win
    curses.start_color()
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)
    curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)
    #curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_BLACK) # etwas mit den Farben spielen

    curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    stdscr.clear()
    stdscr.refresh()

    height, width = stdscr.getmaxyx()
    title = "Willkommen im LoRaHAM_Pi Amateurfunk Chat"
    title_win = curses.newwin(1, width, 0, 0)
    title_win.bkgd(curses.color_pair(1))
    title_win.addstr(0, (width - len(title)) // 2, title)
    title_win.refresh()

    callsign_win = curses.newwin(22, 11, 2, 0)
    callsign_win.bkgd(curses.color_pair(4))
    update_callsigns(callsign_win)

    chat_win = curses.newwin(height - 7, width - 11, 2, 11)
    chat_win.bkgd(curses.color_pair(4))
    update_chat_window(chat_win)

    input_win = curses.newwin(1, width - 2, height - 2, 1)
    input_win.bkgd(curses.color_pair(4))
    input_win.addstr(0, 0, "> ", curses.color_pair(4))
    input_win.refresh()

    footer_win = curses.newwin(1, width, height - 1, 0)
    footer_win.bkgd(curses.color_pair(1))
    footer_win.addstr(0, 0, f"Ctrl-C zum Beenden | Ctrl-R für Ziel = {destination_callsign}")
    footer_win.refresh()

    return callsign_win, chat_win, input_win, footer_win

def update_callsigns(callsign_win):
    callsign_win.clear()
    callsign_win.bkgd(curses.color_pair(4))  # Hintergrundfarbe beibehalten
    for i, callsign in enumerate(callsigns):
        callsign_win.addstr(i + 1, 1, callsign, curses.color_pair(4))
    callsign_win.refresh()  # Aktualisiere die Anzeige im Fenster


def update_chat_window(chat_win):
    chat_win.clear()
    chat_win.bkgd(curses.color_pair(4))
    max_lines = chat_win.getmaxyx()[0] - 2
    y_offset = max_lines - 1
    for sender, message in reversed(messages[-max_lines:]):
        if sender == "Ich":
            chat_win.addstr(y_offset, 1, f"Ich: {message}", curses.color_pair(2))
        else:
            chat_win.addstr(y_offset, 1, f"Jemand: {message}", curses.color_pair(3))
        y_offset -= 1
    chat_win.refresh()

def handle_input(stdscr, chat_win, input_win, callsign_win, footer_win):
    global destination_callsign

    while True:
        input_win.clear()
        input_win.addstr(0, 0, "> ", curses.color_pair(4))
        input_win.refresh()
        user_input = ""
        while True:
            key = input_win.getch()

            if key == 18:  # Ctrl-R wurde gedrückt
             # Rufzeichen eingeben
             input_win.clear()
             input_win.addstr(0, 0, f"  Aktuelles Ziel: {destination_callsign} (drücke Enter um zu bestätigen)")
             input_win.addstr(0, 59, "> ", curses.color_pair(4))
             input_win.refresh()

             new_callsign = ""
             while True:
                 key = input_win.getch()
                 if key in [10, 13]:  # Enter gedrückt
                     destination_callsign = new_callsign.upper().ljust(9)[:9]  # Rufzeichen auf 9 Zeichen begrenzen
                     break
                 elif key in [8, 127, curses.KEY_BACKSPACE]:
                     new_callsign = new_callsign[:-1]
                 elif 32 <= key <= 126:
                     new_callsign += chr(key)

                 # Rufzeichen validieren (nur A-Z, 0-9, Bindestrich)
                 new_callsign = ''.join(c for c in new_callsign if c.isalnum() or c == '-')

                 input_win.clear()
                 input_win.addstr(0, 0, f"  Aktuelles Ziel: {destination_callsign} (drücke Enter um zu bestätigen)")
                 input_win.addstr(0, 59, f"> {new_callsign}", curses.color_pair(4))
                 input_win.refresh()


            if key in [10, 13]:
                break
            elif key in [8, 127, curses.KEY_BACKSPACE]:
                user_input = user_input[:-1]
            elif 32 <= key <= 126:
                user_input += chr(key)
            input_win.clear()
            input_win.addstr(0, 0, f"> {user_input}", curses.color_pair(4))
            input_win.refresh()

        if user_input.lower() == "exit":
            break

        footer_win.addstr(0, 0, f"Ctrl-C zum Beenden | Ctrl-R für Ziel | Aktuelles Ziel: {destination_callsign}")
        footer_win.refresh()
        
        lora.send_message(user_input)
        

def main(stdscr):
    lora.set_pa_config(pa_select=1, max_power=21, output_power=20)
    lora.set_bw(BW)
    lora.set_coding_rate(CODING_RATE)
    lora.set_spreading_factor(SPREADING_FACTOR)
    
    lora.set_rx_crc(True)
    lora.set_low_data_rate_optim(True)

    stdscr.nodelay(True)
    curses.curs_set(0)
    callsign_win, chat_win, input_win, footer_win = setup_window(stdscr)

    update_chat_window(chat_win)
    update_callsigns(callsign_win)
    handle_input(stdscr, chat_win, input_win, callsign_win, footer_win)

recv_thread = threading.Thread(target=lora.set_mode, args=(MODE.RXCONT,), daemon=True)
recv_thread.start()

if __name__ == "__main__":
    curses.wrapper(main)
