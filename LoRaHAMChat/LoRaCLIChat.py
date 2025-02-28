# Benötigt:
# pip install termcolor
import time
import threading
from SX127x.LoRa import *
from SX127x.board_config import BOARD
import os
from termcolor import colored

# Text, den du hinzufügen möchtest
#mein_text = "DC2WA>APRS,WIDE1-1::ALL      :"
mein_text = "DC2WA>APRS,WIDE1-1::DF2FK    :"
#mein_text = "DC2WA>APRS,WIDE1-1::DL6JOE-R :"
#mein_text = "DC2WA>APRS,WIDE1-1::DC2WA-15 :"
#mein_text = "DC2WA>APRS,WIDE1-1::DB0ARD-10:"


BOARD.setup()
BOARD.reset()

SEND_FREQ = 433.775  # Sendefrequenz in MHz
RECV_FREQ = 433.900  # Empfangsfrequenz in MHz
BW = BW.BW125  # Bandbreite
CODING_RATE = CODING_RATE.CR4_5  # Codierungsrate
SPREADING_FACTOR = 12  # Spreizfaktor

MESSAGES_FILE = "messages433.txt"
WELCOME_MESSAGE = "Willkommen im Amateurfunk LoRaHAM Pi-Chat!"

# Funktion zum Erzeugen und Anzeigen einer zentrierten Titelleiste
def zeige_titelleiste(titelleiste, breite=80, terminal_height=24):
    print("")
    # Speichere die aktuelle Cursor-Position
    print("\033[s", end="")  # Speichert die aktuelle Position des Cursors
    
    # Setze den Cursor an den Anfang des Terminals (obere linke Ecke)
    print("\033[H", end="")  # Cursor an den Anfang setzen
    
    # Funktion zum Zentrieren von Text
    def zentriere_text(text, breite):
        # Berechne die Länge des Textes
        text_länge = len(text)
        padding = (breite - text_länge) // 2  # Berechne den Abstand zum Zentrieren
        return ' ' * padding + text + ' ' * padding  # Text mit Leerzeichen an den Rändern

    # Zentriere den Text
    zentrierter_text = zentriere_text(titelleiste, breite)

    # Erzeuge den farbigen Hintergrund mit weißem Text
    titelleiste_mit_farbe = colored(zentrierter_text, 'white', 'on_blue')

    # Ausgabe der Titelleiste
    print(titelleiste_mit_farbe)
    print(f"\033[{terminal_height-1}H\033[1D", end="")   
    print("Geben Sie 'exit' ein, um das Programm zu beenden.")
    print(f"\033[{terminal_height}H\033[1D", end="")   

    #print(">") 
    # Wiederherstellen der gespeicherten Cursor-Position
    #print("\033[u", end="")  # Cursor zurück zur gespeicherten Position



# # Funktion zum Erzeugen und Anzeigen einer zentrierten Titelleiste
# def zeige_titelleiste(titelleiste, breite=80):

    # # ANSI-Escape-Sequenzen, um den Cursor an den Anfang des Terminals zu setzen
    # print("\033[H", end="")  # Setzt den Cursor auf die obere linke Ecke des Terminals


    # # Funktion zum Zentrieren von Text
    # def zentriere_text(text, breite):
        # # Berechne die Länge des Textes
        # text_länge = len(text)
        # padding = (breite - text_länge) // 2  # Berechne den Abstand zum Zentrieren
        # return ' ' * padding + text + ' ' * padding  # Text mit Leerzeichen an den Rändern

    # # Zentriere den Text
    # zentrierter_text = zentriere_text(titelleiste, breite)

    # # Erzeuge den farbigen Hintergrund mit weißem Text
    # titelleiste_mit_farbe = colored(zentrierter_text, 'white', 'on_blue')

    # # Ausgabe der Titelleiste
    # print(titelleiste_mit_farbe)



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
        #print(colored(f"\nJemand: ", "red") + colored(message, "cyan"))

        time.sleep(0.2)
        self.clear_irq_flags(RxDone=1)
        self.reset_ptr_rx()
        self.set_mode(MODE.RXCONT)

        self.save_message(message, 'received')
        self.load_messages()
        #print("> ")
        print("> ", end=" ")

    def send_message(self, message):
        self.set_mode(MODE.SLEEP)
        self.set_freq(SEND_FREQ)
        
        prefix = [ord('<'), 255, 1]
        prefix.extend([ord(char) for char in mein_text])
        payload = prefix + [ord(c) for c in message]
        
        self.write_payload(payload)
        self.set_mode(MODE.TX)
        time.sleep(0.2)
        #print(colored("Ich: ", "cyan") + colored(message, "yellow"))
        
        self.set_mode(MODE.SLEEP)
        self.set_freq(RECV_FREQ)
        self.set_mode(MODE.RXCONT)

        self.save_message(message, 'sent')
        self.load_messages()


    def on_cad_done(self):
        print("\non_CadDone")
        print(self.get_irq_flags())        

    def save_message(self, message, direction):
        with open(MESSAGES_FILE, 'a') as file:
            file.write(f"{direction}: {message}\n")

    def load_messages(self):
        """Lädt und zeigt alte Nachrichten beim Start an."""
        try:
            with open(MESSAGES_FILE, 'r') as file:
                messages = file.readlines()
                print(colored("\nGesprächsverlauf:\n", "magenta"))
                for line in messages:
                    if line.startswith("sent:"):
                        print(colored("Ich:    ", "white") + colored(line[5:].strip(), "yellow")) # colored(zentrierter_text, 'white', 'on_blue')
                    elif line.startswith("received:"):
                        print(colored("Jemand: ", "white", 'on_blue') + colored(line[9:].strip(), "cyan"))
        except FileNotFoundError:
            print(colored(WELCOME_MESSAGE, "blue"))
            self.save_message(WELCOME_MESSAGE, 'received')
        zeige_titelleiste(WELCOME_MESSAGE)
        


    def start_receiving(self):
        """Startet eine Schleife, um dauerhaft Nachrichten zu empfangen."""
        while True:
            self.set_mode(MODE.RXCONT)
            time.sleep(0.1)

def main():
    lora = LoRaSender(verbose=False)
    lora.set_pa_config(pa_select=1, max_power=21, output_power=20)
    lora.set_bw(BW)
    lora.set_coding_rate(CODING_RATE)
    lora.set_spreading_factor(SPREADING_FACTOR)
    
    lora.set_rx_crc(True)
    lora.set_low_data_rate_optim(True)

    # Lade vorherige Nachrichten
    lora.load_messages()

    # Starte den Empfangs-Thread
    recv_thread = threading.Thread(target=lora.start_receiving, daemon=True)
    recv_thread.start()

    while True:
        message = input(colored("> ", "yellow"))
        if message.lower() == 'exit':
            print("Chat wird beendet...")
            break
        lora.send_message(message)
        lora.load_messages()
        #print("Geben Sie 'exit' ein, um das Programm zu beenden.")
        #zeige_titelleiste(WELCOME_MESSAGE)
        
        time.sleep(1)


if __name__ == "__main__":
    main()
