import curses
import time
import threading
from SX127x.LoRa import *
from SX127x.board_config import BOARD
from termcolor import colored
import re

#import os
#os.system("printf '\033[8;60;150t'")


# APRS header um sim am APRS als solches zu identifizieren
#prefix = [ord('<'), 255, 1]

# Ohne APRS-Symbole kann direkt 1:1 Chat gemacht werden
# hierzu sollte mein_text auch gekürzt werden
#prefix = ""

# Eigenes Rufzeichen! Ändere dies! 
# Du kannst zur Laufzeit mit STRG-K die Konfiguration öffnen
# Du kannst auch eine SSID wie z.b. -10 anfügen
CALL_SIGN = "DL0xxx-10"
CALL_SIGN_STOP = ">"

APRS_PATH = "APRS,WIDE1-1"

SEPERATOR = "::"

# Dieser Text entfällt nun und wird nicht mehr genutzt
#mein_text = "DC2WA>APRS,WIDE2-2::ALL      :"

# LoRa initialisieren
BOARD.setup()
BOARD.reset()

SEND_FREQ = 433.775  # Sendefrequenz in MHz
#RECV_FREQ = 433.775  # Empfangsfrequenz in MHz
RECV_FREQ = 433.900  # Empfangsfrequenz in MHz
BW = BW.BW125  # Bandbreite
CODING_RATE = CODING_RATE.CR4_5  # Codierungsrate
SPREADING_FACTOR = 12  # Spreizfaktor
SYNC_WORD = 0x12  # Synchronisierungswort

MESSAGES_FILE = "messages433_1.txt"

# Rufzeichenliste gefüllt mit Platzhaltern zur Demo.
# APRSPH ist für den APRS Thursday-Server. Nehme diesen als Ziel wenn du mitmachen möchtest
callsigns = ["Calls:", "", "ALL", "APRSPH", "DC2WA-15"] #, "DB4XYZ", "DL2DEF", "DK5GHJ", "DM0KLM"]
# Du kannst weitere Rufzeichen hier einfügen. Somit dient die Liste als Übersicht.
# Neue Rufzeichen im Chat tauchen automatisch in der Liste auf. Begrenz auf 20 Stück

# Definiere Fenster als globale Variablen
callsign_win = None
chat_win = None

# Zielrufzeichen definieren (kann durch Benutzer geändert werden)
destination_callsign = "ALL      "

def check_terminal_size(stdscr, min_height=60, min_width=150):
    """Überprüft, ob das Terminal groß genug ist, und fordert den Nutzer ggf. auf, es zu vergrößern."""
    while True:
        stdscr.clear()
        max_y, max_x = stdscr.getmaxyx()  # Terminalgröße abrufen

        if max_y >= min_height and max_x >= min_width:
            return  # Terminal ist groß genug, normal fortfahren

        # ❗ Terminal ist zu klein → Hinweis anzeigen
        stdscr.addstr(0, 0, "⚠ TERMINAL ZU KLEIN ⚠", curses.A_BOLD)
        stdscr.addstr(2, 0, f"Bitte vergrößere dein Terminal auf mindestens {min_width}x{min_height}.")
        stdscr.addstr(4, 0, f"Aktuelle Größe: {max_x}x{max_y}")
        stdscr.addstr(6, 0, "Drücke eine beliebige Taste, um die Größe erneut zu prüfen...")
        stdscr.refresh()
        stdscr.getch()  # Nutzer drückt eine Taste → prüfe erneut


def extract_callsign(message):
    """
    Extrahiert das Rufzeichen aus dem empfangenen String.
    Erwartetes Format: < 0xff 0x01 CALLSIGN>
    """
    message = message[9:]
    #match = re.search(r'<\xff\x01([A-Z0-9]+)>', message)
    #match = re.search(r'<\xff\x01([A-Za-z0-9-]+)>', message)
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

        #messages.append(("Debug", f"Extracted: {callsign}"))  # Debug für Rufzeichen
                #callsign_win.refresh()  # Stelle sicher, dass das Fenster aktualisiert wird				

        messages.append(("Jemand", message))
       # messages.append(("Rufzeichen", callsign))

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
        
        # prefix APRS_header. Wenn du direkt für Chat nutzen willst, kommentiere die Zeile aus 
        # prefix = ""

        end_char = ":"
        prefix = [ord('<'), 255, 1] # auskommentieren wenn obere Zeile drin ist


        prefix.extend([ord(char) for char in CALL_SIGN])
        prefix.extend([ord(char) for char in CALL_SIGN_STOP])
        prefix.extend([ord(char) for char in APRS_PATH])
        prefix.extend([ord(char) for char in SEPERATOR])
        #prefix.extend([ord(char) for char in mein_text])
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
                #messages = file.readlines()
                if line.startswith("Ich"):
                    #sender, message = line[5:].strip()
                    #sender = "Ich"
                    messages.append(("Ich", line[4:].strip()))
                elif line.startswith("Jemand"):
                    #line[7:].strip()
                    messages.append(("Jemand", line[17:].strip()))

                #sender, message = line.strip().split(": ", 1)
                #messages.append((sender, message))
    except FileNotFoundError:
        pass
		
	
	

# def load_messages():
        # """Lädt und zeigt alte Nachrichten beim Start an."""
        # try:
            # with open(MESSAGES_FILE, 'r') as file:
                # messages = file.readlines()
                # print(colored("\nGesprächsverlauf:\n", "magenta"))
                # for line in messages:
                    # if line.startswith("sent:"):
                        # print(colored("Ich: ", "white") + colored(line[5:].strip(), "yellow"))
                    # elif line.startswith("received:"):
                        # print(colored("Jemand: ", "red") + colored(line[9:].strip(), "cyan"))
        # except FileNotFoundError:
            # print(colored(WELCOME_MESSAGE, "blue"))
            # self.save_message(WELCOME_MESSAGE, 'received')

# Globale Variablen

messages = []
lora = LoRaSender(verbose=False)
load_messages()

def setup_window(stdscr):
    global callsign_win, chat_win
    curses.start_color()
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)  # Kopf und Fußzeile
    curses.init_pair(2, curses.COLOR_CYAN , curses.COLOR_BLACK) # Textchat "Ich"
    curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK) # Textchat "Jemand"
    #curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_BLACK)

    curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK)# Rufzeichenliste
    curses.init_pair(5, curses.COLOR_RED, curses.COLOR_BLUE)# Rufzeichenliste
    
    
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
    chat_win.bkgd(curses.color_pair(4) | curses.A_BOLD)
    update_chat_window(chat_win)

    input_win = curses.newwin(1, width - 2, height - 2, 1)
    input_win.bkgd(curses.color_pair(4))
    input_win.addstr(0, 0, "> ", curses.color_pair(4))
    input_win.refresh()

    footer_win = curses.newwin(1, width, height - 1, 0)
    footer_win.bkgd(curses.color_pair(1))
    #footer_win.addstr(0, 0, f"Ctrl-C zum Beenden | Ctrl-K für Konfiguration | APRS-Pfad: {APRS_PATH} | Ctrl-R für Ziel | Aktuelles Ziel: {destination_callsign}")
    footer_win.addstr(0, 0, f"Ctrl-C zum Beenden | Ctrl-K_onfiguration | APRS-Pfad: {APRS_PATH} | Ctrl-R für Ziel: ") #, curses.color_pair(1)) #{destination_callsign}")
    
    footer_win.addstr(destination_callsign, curses.color_pair(5) | curses.A_BOLD)
    footer_win.refresh()

    return callsign_win, chat_win, input_win, footer_win

#def update_callsigns(callsign_win):
#    for i, callsign in enumerate(callsigns[:20]):
#        callsign_win.addstr(i + 1, 1, f"{callsign}", curses.color_pair(4))
#    callsign_win.refresh()

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
            chat_win.addstr(y_offset, 1, f"Ich: {message}", curses.color_pair(2) | curses.A_BOLD)
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

            if key == 18:  # Strg+R wurde gedrückt
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

                    new_callsign = ''.join(c for c in new_callsign if c.isalnum() or c == '-')

                    input_win.clear()
                    input_win.addstr(0, 0, f"  Aktuelles Ziel: {destination_callsign} (drücke Enter um zu bestätigen)")
                    input_win.addstr(0, 59, f"> {new_callsign}", curses.color_pair(4))
                    input_win.refresh()

            elif key == 11:  # Strg+K wurde gedrückt
                open_config_window(stdscr)  # Konfigurationsfenster öffnen
                update_chat_window(chat_win)
                footer_win.refresh()
                continue

            if key in [10, 13]:  # Enter gedrückt
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


        #footer_win.addstr(0, 0, f"Ctrl-C zum Beenden | Ctrl-K für Konfiguration | APRS-Pfad: {APRS_PATH} | Ctrl-R für Ziel | Aktuelles Ziel: {destination_callsign}")
        footer_win.addstr(0, 0, f"Ctrl-C zum Beenden | Ctrl-K für Konfiguration | APRS-Pfad: {APRS_PATH} | Ctrl-R für Ziel | Aktuelles Ziel: ", curses.color_pair(1)) #{destination_callsign}")
    
        footer_win.addstr(destination_callsign, curses.color_pair(5) | curses.A_BOLD)
        footer_win.refresh()

        lora.send_message(user_input)


def open_config_window(stdscr):
    global SEND_FREQ, RECV_FREQ, CALL_SIGN, BW, SPREADING_FACTOR, CODING_RATE, SYNC_WORD, APRS_PATH

    # Fenstergröße und Position
    height, width = stdscr.getmaxyx()
    win_height = 12
    win_width = 40
    win_y = (height - win_height) // 2
    win_x = (width - win_width) // 2

    # Fenster für die Konfiguration
    config_win = curses.newwin(win_height, win_width, win_y, win_x)
    config_win.bkgd(curses.color_pair(1))  # Hintergrundfarbe (weiß auf blau)

    # Titel
    title = "Konfiguration"
    try:
        config_win.addstr(0, (win_width - len(title)) // 2, title, curses.color_pair(1))
    except curses.error as e:
        print(f"Fehler beim Hinzufügen des Titels: {e}")
        return

    # Eingabefelder
    #labels = ["Sendefrequenz: ", "Empfangsfrequenz: ", "Eigenes Rufzeichen: "]#, "Bandbreite (kHz): ", "Spreadingfactor: ", "CodingRate: "]
    #values = [f"{SEND_FREQ:.3f}", f"{RECV_FREQ:.3f}", CALL_SIGN, str(BW), str(SPREADING_FACTOR), str(CODING_RATE)]
    
    labels = ["Sendefrequenz: ", "Empfangsfrequenz: ", "Eigenes Rufzeichen: ", "APRS-Pfad: "]
    values = [f"{SEND_FREQ:.3f}", f"{RECV_FREQ:.3f}", CALL_SIGN, str(APRS_PATH)]

    # Zeige Labels und Werte an
    try:
        for i, label in enumerate(labels):
            config_win.addstr(i + 2, 1, label)
            config_win.addstr(i + 2, len(label) + 1, values[i])

        # Infozeile unterhalb der Felder
        config_win.addstr(len(labels) + 4, 1, "ESC=Beenden", curses.color_pair(1))

    except curses.error as e:
        print(f"Fehler beim Hinzufügen der Labels/Werte: {e}")
        return

    config_win.refresh()

    current_field = 0  # Anfangsfeld (Sendefrequenz)
    editing_value = True  # Direkt in den Bearbeitungsmodus starten

    while True:
        # Wenn wir in einem Bearbeitungsmodus sind
        if editing_value:
            config_win.clear()
            config_win.addstr(0, (win_width - len(title)) // 2, title, curses.color_pair(1))  # Titel wieder anzeigen

            # Labels und Werte anzeigen, aber das aktuelle Feld wird bearbeitet
            for i, label in enumerate(labels):
                config_win.addstr(i + 2, 1, label)
                if i == current_field:
                    # Markiere das aktuelle Feld für Bearbeitung
                    config_win.addstr(i + 2, len(label) + 1, values[i], curses.color_pair(3))
                else:
                    config_win.addstr(i + 2, len(label) + 1, values[i])

            # Infozeile
            config_win.addstr(len(labels) + 3, 1, "ESC=Beenden", curses.color_pair(1))

            config_win.refresh()

            key = config_win.getch()
            if key == 27:  # ESC-Taste
                # Abbruch, zurück zum Konfigurationsbildschirm
                editing_value = False
                
                # Hier keine Eingabewerte speichern, sondern zurückkehren
                #values[current_field] = f"{SEND_FREQ:.3f}" if current_field == 0 else f"{RECV_FREQ:.3f}" if current_field == 1 else CALL_SIGN

            elif 32 <= key <= 126:  # Zeichen eingeben
                values[current_field] += chr(key)

            elif key in [8, 127, curses.KEY_BACKSPACE]:  # Backspace
                values[current_field] = values[current_field][:-1]

            if key == 9:  # Tab-Taste
                # Eingabewert sofort übernehmen, wenn das Feld gewechselt wird
                if current_field == 0:  # Sendefrequenz
                    try:
                        SEND_FREQ = round(float(values[current_field]), 3)
                        values[current_field] = f"{SEND_FREQ:.3f}"
                    except ValueError:
                        values[current_field] = str(SEND_FREQ)
                elif current_field == 1:  # Empfangsfrequenz
                    try:
                        RECV_FREQ = round(float(values[current_field]), 3)
                        values[current_field] = f"{RECV_FREQ:.3f}"
                    except ValueError:
                        values[current_field] = str(RECV_FREQ)
                elif current_field == 2:  # Rufzeichen
                    CALL_SIGN = values[current_field].upper()#.ljust(9)[:9]
                elif current_field == 3:  # APRS-Pfad
                    APRS_PATH = values[current_field].upper().strip()
                    
                # elif current_field == 3:  # Bandbreite
                    # BW = values[current_field].upper().strip()
                # elif current_field == 4:  # Spreadingfactor
                    # SPREADING_FACTOR = values[current_field].upper().strip()
                # elif current_field == 5:  # CodingRate
                    # CODING_RATE = values[current_field].upper().strip()

                # Zum nächsten Feld wechseln
                current_field = (current_field + 1) % len(labels)

        else:
            # Benutzer befindet sich nicht in der Eingabe, sondern beim Wechseln der Felder
            key = config_win.getch()

            if key == 9:  # Tab-Taste
                # Bearbeitung des aktuellen Feldes beginnen
                editing_value = True

            elif key == 27:  # ESC-Taste
                # Abbruch, das Fenster schließen
                break

            # Anzeigen der Felder ohne Bearbeitung
            config_win.clear()
            config_win.addstr(0, (win_width - len(title)) // 2, title, curses.color_pair(1))  # Titel wieder anzeigen

            # Labels und Werte anzeigen
            for i, label in enumerate(labels):
                config_win.addstr(i + 2, 1, label)
                config_win.addstr(i + 2, len(label) + 1, values[i])

            # Infozeile
            config_win.addstr(len(labels) + 4, 1, "ESC=Beenden", curses.color_pair(1))

            config_win.refresh()


def main(stdscr):

    check_terminal_size(stdscr)  # Prüfe die Terminalgröße vor dem Start
    #lora = LoRaSender(verbose=False)
    lora.set_pa_config(pa_select=1, max_power=21, output_power=20)
    lora.set_bw(BW)
    lora.set_coding_rate(CODING_RATE)
    lora.set_spreading_factor(SPREADING_FACTOR)
    
    lora.set_rx_crc(True)
    lora.set_low_data_rate_optim(True)

    stdscr.nodelay(True)
    curses.curs_set(0)
    callsign_win, chat_win, input_win, footer_win = setup_window(stdscr)

    # Übergib Fenster an LoRaSender
    #lora = LoRaSender(verbose=False, callsign_win=callsign_win, chat_win=chat_win)


    update_chat_window(chat_win)
    update_callsigns(callsign_win)
    handle_input(stdscr, chat_win, input_win, callsign_win, footer_win)

recv_thread = threading.Thread(target=lora.set_mode, args=(MODE.RXCONT,), daemon=True)
recv_thread.start()

if __name__ == "__main__":
    curses.wrapper(main)
