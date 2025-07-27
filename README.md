![LoRaHAM_Pi](https://github.com/LoRaHAM/LoRaHAM_Pi/blob/main/LoRaHAM_logo.png?raw=true)

# LoRaHAM Pi (english)

LoRaHAM Pi is a Raspberry Pi hardware upgrade project for radio amateurs to enable LoRa with high transmission power and thus long range on a single board computer.

First code for the LoRaHAM Pi hardware | https://www.loraham.de/produkt/loraham-pi-now/

Raspberry Pi 3 Image for Meshtastic (8 GB SD-Card): [Meshtastic 433 MHz 1 Watt](https://www.loraham.de/downloads/Meshtastic_433_LoRaHAM_Pi.img)

![LoRaHAM_Pi](https://github.com/LoRaHAM/LoRaHAM_Pi/blob/main/LoRaHAM_P1_3.jpg?raw=true)

* Raspberry Pi 3/4/5
* Raspbian Image on RPi

Need follow parts on the Raspberry Pi image:

[https://pypi.org/project/RPi.GPIO/](https://pypi.org/project/RPi.GPIO/)

[https://pypi.org/project/spidev/](https://pypi.org/project/spidev/)

[https://pypi.org/project/pyLoRa/](https://pypi.org/project/pyLoRa/)

In order to install spidev download the source code and run setup.py manually:
```bash
wget https://pypi.python.org/packages/source/s/spidev/spidev-3.1.tar.gz
tar xfvz  spidev-3.1.tar.gz
cd spidev-3.1
sudo python setup.py install
```

or use the following setup:
```bash
sudo raspi-config nonint do_spi 0
sudo apt-get install python-dev python3-dev
```

```bash
sudo apt-get install python-pip python3-pip
pip install RPi.GPIO
pip install spidev
pip install pyLoRa
```



the used pySX17x is a Fork of 
https://github.com/mayeranalytics/pySX127x

with correct Pin assignment for the LoRaHAM Pi on 433 and 868 MHz

Note:
The needed configuration files is in the pySX127x-Folder, but you neet to install it first for the RPi enviroment!



# Warnings
This code is provided at your own risk and responsibility. This code is experimental.
For radio amateur or laboratory use only.

# Credits and license

    Copyright (c) 2020-2025 Alexander Walter
    Licensed under GPL v2 (text)
    Maintained by Alexander Walter 


![LoRaHAM_Pi](https://github.com/LoRaHAM/LoRaHAM_Pi/blob/main/LoRaHAM_logo.png?raw=true)

# LoRaHAM Pi (deutsch)

LoRaHAM Pi ist ein Raspberry Pi Hardware-Upgrade-Projekt für Funkamateure, um LoRa mit hoher Sendeleistung und damit großer Reichweite auf einem Einplatinencomputer zu ermöglichen.

Erster Code für die LoRaHAM Pi Hardware | https://www.loraham.de/produkt/loraham-pi-now/

![LoRaHAM_Pi](https://github.com/LoRaHAM/LoRaHAM_Pi/blob/main/LoRaHAM_P1_3.jpg?raw=true)

* Raspberry Pi 3/4/5
* Raspbian Image auf RPi

Folgende Teile werden für das Raspberry Pi Image benötigt:

https://pypi.org/project/RPi.GPIO/

https://pypi.org/project/spidev/

https://pypi.org/project/pyLoRa/

Um spidev zu installieren, laden Sie den Quellcode herunter und führen Sie setup.py manuell aus:
```bash
wget https://pypi.python.org/packages/source/s/spidev/spidev-3.1.tar.gz
tar xfvz spidev-3.1.tar.gz
cd spidev-3.1
sudo python setup.py installieren
```

oder verwenden Sie das folgende Setup:
```bash
sudo raspi-config nonint do_spi 0
sudo apt-get install python-dev python3-dev
```

```bash
sudo apt-get install python-pip python3-pip
pip install RPi.GPIO
pip install spidev
pip install pyLoRa
```



das verwendete pySX17x ist ein Fork von 
https://github.com/mayeranalytics/pySX127x

mit korrekter Pin-Belegung für den LoRaHAM Pi auf 433 und 868 MHz

Anmerkung:
Die benötigten Konfigurationsdateien befinden sich im pySX127x-Ordner, müssen aber erst für die RPi-Umgebung installiert werden!



# Warnungen
Dieser Code wird auf eigenes Risiko und eigene Verantwortung zur Verfügung gestellt. Dieser Code ist experimentell.
Er ist nur für Funkamateure oder Labore geeignet.

# Credits und Lizenz

    Copyright (c) 2020-2025 Alexander Walter
    Licensed under GPL v2 (text)
    Maintained by Alexander Walter 
