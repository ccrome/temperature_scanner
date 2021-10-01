#!/usr/bin/env python3
import serial
import time
from sys import stdout
import re
import numpy as np


def mprint(*args):
    print(*args)
    stdout.flush()


def close_enough(x, y, z, a_x, a_y, a_z, tolerance=0.01):
    okay = True
    if x is not None:
        if abs(x-a_x) > tolerance:
            okay = False
    if y is not None:
        if abs(y-a_y) > tolerance:
            okay = False
    if z is not None:
        if abs(z-a_z) > tolerance:
            okay = False
    return okay


class Printer:
    def __init__(self, port, baud=115200, debug=False):
        self.port = port
        self.baud = baud
        self.serial = serial.Serial(port, baud)
        self.debug=debug
        self.wait_for_stuff()
        time.sleep(5)
        self.feed=30000
        self.home()
        self.send([
            "M82",
            "M201 X500.00 Y500.00 Z100.00 E5000.00 ;Setup machine max acceleration",
            "M203 X500.00 Y500.00 Z10.00 E50.00 ;Setup machine max feedrate",
            "M204 P500.00 R1000.00 T500.00 ;Setup Print/Retract/Travel acceleration",
            "M205 X8.00 Y8.00 Z0.40 E5.00 ;Setup Jerk",
            "M220 S100 ;Reset Feedrate",
            "M221 S100 ;Reset Flowrate",
            "M501",
        ])

    def readline(self):
        return self.serial.readline().decode('utf-8').strip()
        
    def wait_for_stuff(self, ):
        mprint(self.readline())

    def send(self, cmd, interval=0.01):
        if isinstance(cmd, str):
            cmd = [cmd]
        for c in cmd:
            cmdstr = f"{c}\r\n"
            if self.debug:
                mprint(f'sending {cmdstr}')
            bytes_written = self.serial.write(cmdstr.encode('utf-8'))
            time.sleep(interval)

    def wait_for_ok(self):
        done = False
        while not done:
            line = self.readline()
            if len(line) == 0:
                time.sleep(0.01)
            else:
                mprint(line)
                if line.lower().startswith("ok"):
                    done = True
    
    def home(self):
        self.send("G28")
        self.wait_for_ok()

    def goto_xy(self, x, y):
        self.send(f"G0 X{x} Y{y} F{self.feed}")
        self.wait_for_position(x=x, y=y)

    def goto_xyz(self, x, y, z):
        self.send(f"G0 X{x} Y{y} Z{z} F{self.feed}")
        self.wait_for_position(x=x, y=y, z=z)

    def goto_z(self, z):
        self.send(f"G0 Z{z} F{self.feed}")
        self.wait_for_position(z=z)

    def goto_x(self, x):
        self.send(f"G0 X{x} F{self.feed}")
        self.wait_for_position(x=x)

    def goto_y(self, y):
        self.send(f"G0 Y{y} F{self.feed}")
        self.wait_for_position(y=y)

    def get_position(self):
        done = False
        while not done:
            self.send("M114 R")
            line = self.readline()
            if len(line) == 0:
                pass
            else:
                if self.debug:
                    mprint(line)
                # looking for a line like: X:160.00 Y:190.00 Z:5.00 E:0.00 Count X:12800 Y:15200 Z:2000
                m = re.match("X:(\d+.\d+) +Y:(\d+.\d+) +Z:(\d+.\d+) +.*$", line)
                if m:
                    x = float(m.group(1))
                    y = float(m.group(2))
                    z = float(m.group(3))
                    return (x, y, z)
            time.sleep(0.01)
        
    def wait_for_position(self, x=None, y=None, z=None):
        done = False
        while not done:
            actual_x, actual_y, actual_z = self.get_position()
            if close_enough(x, y, z, actual_x, actual_y, actual_z):
                done = True

class Scanner:
    def __init__(self, printer, x0, y0, width, length, grid, scanning_z, safe_z=30):
        self.printer = printer
        self.x0 = x0
        self.y0 = y0
        self.x = width
        self.y = length
        self.grid = grid
        self.safe_z = safe_z
        self.scanning_z = scanning_z


    def compute_position_list(self):
        x = self.x0
        y = self.y0
        z = self.scanning_z
        self.positions = []
        while x < self.x+self.x0:
            while y < self.y+self.y0:
                self.positions.append((x, y, z))
                y += self.grid
            x += self.grid
            y = self.y0
        
    def start(self):
        self.printer.goto_z(self.safe_z)
        self.printer.goto_xy(self.x0, self.y0)
        self.compute_position_list()

    def next(self):
        x, y, z = self.positions.pop()
        self.printer.goto_xyz(x, y, z)
        time.sleep(0.25)
        return len(self.positions)

    def scan(self):
        done = False
        while not done:
            togo = self.next()
            mprint(f"{togo}: {printer.get_position()}")
            if togo == 0:
                done = True
        mprint("Scanning Complete")

    def present(self):
        mprint("Presenting")
        self.printer.goto_z(z=self.safe_z)
        mprint("going to z")
        self.printer.goto_x(x=0)
        mprint("going to x")
        self.printer.goto_y(y=250)
        mprint("going to y")
        

#scanner = Scanner(None, x0=100, y0=100, width=160, length=57, grid=10, scanning_z=20, safe_z=30)
#scanner.compute_position_list()
#mprint(scanner.positions)
#exit()

mprint("Scanner starting")
printer = Printer("COM13", debug=False)
mprint("Got printer")
scanner = Scanner(printer, x0=40, y0=40, width=10, length=10, grid=4, scanning_z=20, safe_z=30)
mprint("Starting"); 
scanner.start()
scanner.scan()
scanner.present()
