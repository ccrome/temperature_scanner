#!/usr/bin/env python3
import serial
import time


class Printer:
    def __init__(self, port, baud=115200):
        self.port = port
        self.baud = baud
        self.serial = serial.Serial(port, baud)


    def send(self, cmd):
        cmdstr = f"{cmd}"
        self.serial.write(cmdstr.encode('utf-8'))
        
    def home(self):
        self.send("G28")
        
printer = Printer("/dev/ttyUSB0")
printer.home()
