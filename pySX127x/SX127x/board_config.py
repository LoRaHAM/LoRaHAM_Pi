""" Defines the __class__.class that contains the board pin mappings and RF module HF/LF info. """
# -*- coding: utf-8 -*-

# Copyright 2015-2018 Mayer Analytics Ltd. and Rui Silva
#
# This file is part of rpsreal/pySX127x.
#
# pySX127x is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public
# License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# pySX127x is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public License for more
# details.
#
# You can be released from the requirements of the license by obtaining a commercial license. Such a license is
# mandatory as soon as you develop commercial activities involving pySX127x without disclosing the source code of your
# own applications, or shipping pySX127x with a closed source product.
#
# You should have received a copy of the GNU General Public License along with pySX127.  If not, see
# <http://www.gnu.org/licenses/>.


import RPi.GPIO as GPIO
import spidev

import time

class BOARD:
    """ Board initialisation/teardown and pin configuration is kept here.
        Also, information about the RF module is kept here.
        This is the Raspberry Pi board with one LED and a Ra-02 Lora.
    """
    def __init__(self, freq = ["433", "868"]):
        if freq == "433":
            self.DIO0 = 25
            self.DIO1 = 24
            self.DIO2 = 23
            self.DIO3 = 22
            self.RST  = 5
            self.LED  = 13

            # The spi object is kept here
            self.spi = None
            self.SPI_BUS = 0
            self.SPI_CS = 0
            
            # tell pySX127x here whether the attached RF module uses low-band (RF*_LF pins) or high-band (RF*_HF pins).
            # low band (called band 1&2) are 137-175 and 410-525
            # high band (called band 3) is 862-1020
            self.low_band = True
        else:
            # Note that the BCOM numbering for the GPIOs is used.
            self.DIO0 = 16
            self.DIO1 = 12
            self.DIO2 = 20
            self.DIO3 = 21
            self.RST  = 6
            self.LED  = 19

            # The spi object is kept here
            self.spi = None
            self.SPI_BUS = 0
            self.SPI_CS = 1
            
            # tell pySX127x here whether the attached RF module uses low-band (RF*_LF pins) or high-band (RF*_HF pins).
            # low band (called band 1&2) are 137-175 and 410-525
            # high band (called band 3) is 862-1020
            self.low_band = False

        # Configure the Raspberry GPIOs
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.LED, GPIO.OUT)
        GPIO.setup(self.RST, GPIO.OUT)
        GPIO.output(self.LED, 0)
        GPIO.output(self.RST, 1)

        for gpio_pin in [self.DIO0, self.DIO1, self.DIO2, self.DIO3]:
            GPIO.setup(gpio_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

        # blink 2 times to signal the is set up
        self.blink(.1, 2)

    def teardown(self):
        """Cleanup GPIO and SpiDev"""
        if self.spi:
            self.spi.close()
        GPIO.cleanup()

    def SpiDev(self):
        """Init and return the SpiDev object
        :return: SpiDev object
        :param spi_bus: The RPi SPI bus to use: 0 or 1
        :param spi_cs: The RPi SPI chip select to use: 0 or 1
        :rtype: SpiDev
        """
        spi_bus = self.SPI_BUS
        spi_cs = self.SPI_CS
        self.spi = spidev.SpiDev()
        self.spi.open(spi_bus, spi_cs)
        self.spi.max_speed_hz = 5000000    # SX127x can go up to 10MHz, pick half that to be safe
        return self.spi

    @staticmethod
    def add_event_detect(dio_number, callback):
        """Wraps around the GPIO.add_event_detect function
        :param dio_number: DIO pin 0..5
        :param callback: The function to call when the DIO triggers an IRQ.
        """
        GPIO.add_event_detect(dio_number, GPIO.RISING, callback=callback)

    def add_events(self, cb_dio0, cb_dio1, cb_dio2, cb_dio3, cb_dio4, cb_dio5, switch_cb=None):
        self.add_event_detect(self.DIO0, callback=cb_dio0)
        self.add_event_detect(self.DIO1, callback=cb_dio1)
        self.add_event_detect(self.DIO2, callback=cb_dio2)
        self.add_event_detect(self.DIO3, callback=cb_dio3)
        # the modtronix inAir9B does not expose DIO4 and DIO5

    def led_on(self, value=True):
        """Switch the proto shields LED"""
        GPIO.output(self.LED, value)

    def led_off(self):
        """Switch LED off"""
        GPIO.output(self.LED, 0)
    
    def reset(self):
        """Manual reset"""
        GPIO.output(self.RST, 0)
        time.sleep(.01)
        GPIO.output(self.RST, 1)
        time.sleep(.01)

    def blink(self, time_sec, n_blink):
        if n_blink == 0:
            return
        self.led_on()
        for _ in range(n_blink):
            time.sleep(time_sec)
            self.led_off()
            time.sleep(time_sec)
            self.led_on()
        self.led_off()

