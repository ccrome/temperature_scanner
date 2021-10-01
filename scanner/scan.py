import serial
from serial.threaded import LineReader, ReaderThread
from sys import stdout
import time
import traceback
import numpy as np
import re
import threading
import logging
import time


def close_enough(a, b, tolerance=0.01):
    if a is not None and b is not None and len(a) == 3 and len(b) == 3:
        a_x, a_y, a_z = a
        b_x, b_y, b_z = b
        okay = True
        if a_x is not None and b_x is not None:
            if abs(a_x-b_x) > tolerance:
                okay = False
        if a_y is not None and b_y is not None:
            if abs(a_y-b_y) > tolerance:
                okay = False
        if a_z is not None and b_z is not None:
            if abs(a_z-b_z) > tolerance:
                okay = False
        return okay
    else:
        mprint("not close enough")
        return False


def fprint(*x):
    print(*x)
    stdout.flush()
def mprint(*x):
    logging.info(*x)
    

STATE_DISCONNECTED          = 1
STATE_WAITING_FOR_STARTUP   = 2
STATE_FIRST_MESSAGE_ARRIVED = 3
STATE_IS_HOMED              = 5

class TempScanner(LineReader):
    def connection_made(self, transport):
        super(TempScanner, self).connection_made(transport)
        self._temperature = 0
        self._temp_count = 0

    def handle_line(self, data):
        try:
            data = int(data[2:], 16)
            t = self.get_temp(data)
            if t is not None:
                self._temperature = t
                self._temp_count += 1
        except:
            pass

    def temperature(self, timeout=2):
        start = self._temp_count
        starttime = time.time()
        while self._temp_count == start:
            time.sleep(0.01)
            if time.time() > starttime+timeout:
                raise Exception("Timed out waiting for temperature update!")
        return self._temperature
    
    def connection_lost(self, exc):
        fprint(f"Temp scanner conneciton lost {exc}")

    def get_temp(self, x):
        if (x >> 32) & 0xFF == 0x4c:
            return (x>> 16) & 0xFFFF
        else:
            return None
        

class GcodePrinter(LineReader):
    def connection_made(self, transport):
        super(GcodePrinter, self).connection_made(transport)
        self._location = None
        self.feed = 5000
        self._state = STATE_WAITING_FOR_STARTUP
        self._busy = False
        self.TERMINATOR = b'\n'

    def handle_line(self, data):
        if self._state < STATE_FIRST_MESSAGE_ARRIVED:
            self._state = STATE_FIRST_MESSAGE_ARRIVED
        mprint(f'line received "{data}"')
        self.parse_line(data)
    
    def parse_line(self, line):
        if line.startswith("ok"):
            self._busy = False
            if self._state < STATE_IS_HOMED:
                self._state = STATE_IS_HOMED
        
        m = re.match("X:(\d+.\d+) +Y:(\d+.\d+) +Z:(\d+.\d+) +.*$", line)
        if m:
            x = float(m.group(1))
            y = float(m.group(2))
            z = float(m.group(3))
            self._location = np.array((x, y, z))

    def is_homed(self):
        homed = self._state >= STATE_IS_HOMED
        logging.debug(homed)
        return homed

    def connection_lost(self, exc):
        self._state = STATE_DISCONNECTED
        print(exc)
        print('port closed')
        logging.info("Port Close")

    def is_alive(self):
        return self._state >= STATE_FIRST_MESSAGE_ARRIVED

    def location(self):
        return self._location

    def is_dead(self):
        return self._state == STATE_DISCONNECTED

    def home(self):
        logging.debug("homing command")
        print("homing...")
        self.wait_for_alive()
        self._busy = True
        self.write_line("G28")
        
        while(self._busy):
            logging.debug("waiting")
            time.sleep(0.1)
    

    def wait_for_close_enough(self, coord, timeout):
        logging.debug(f"wait_for_close_enough {coord}")
        start = time.time()
        while True:
            self.write_line("M114 R")
            if close_enough(self.location(), coord):
                break
            if (time.time()-start) > timeout:
                raise Exception("Timed out waitng to get to target.")
            time.sleep(0.1)
        
    def goto(self, x=None, y=None, z=None, wait=True, timeout=10):
        logging.debug(f"goto {x} {y} {z}")
        xs = ys = zs = ""
        if x is not None:
            xs=f"X{x}"
        if y is not None:
            ys=f"Y{y}"
        if z is not None:
            zs=f"Z{z}"
        self.write_line(f"G0 {xs} {ys} {zs} F{self.feed}")
        if wait:
            self.wait_for_close_enough((x, y, z), timeout)

    def wait_for_alive(self, timeout = 30):
        start = time.time()
        while not self.is_alive():
            time.sleep(1)
            if (time.time() - start ) > timeout:
                raise Exception("Timed out waiting to come alive")
    
    def busy(self):
        return self._busy


class Scanner:
    def __init__(self, printer_port, printer_baud, safe_z, scan_z, temp_port, temp_baud):
        self.ser = serial.Serial(printer_port, printer_baud, timeout=0.5)
        self.reader_thread = ReaderThread(self.ser, GcodePrinter)
        self.reader_thread.start()
        self.protocol = self.reader_thread.protocol
        self.safe_z = safe_z
        self.scan_z = scan_z
        self.present_x = 0
        self.present_y = 280

        self.temp_ser = serial.Serial(temp_port, temp_baud, timeout=5)
        self.temp_reader_thread = ReaderThread(self.temp_ser, TempScanner)
        self.temp_reader_thread.start()
        self.temp_protocol = self.temp_reader_thread.protocol

        self.protocol.home()
        # self.protocol.write_line(f"M140 S60")

    def scan(self, start_x, start_y, delta_x, delta_y, stepsize):
        fprint("Scanning")
        p = self.protocol
        p.goto(z=self.safe_z)
        p.goto(x=start_x, y=start_y)
        p.goto(z=self.scan_z)
        x = start_x
        while x <= start_x + delta_x:
            y = start_y
            while y <= start_y + delta_y:
                p.goto(x=x, y=y)
                temperature = self.temp_protocol.temperature()
                fprint(f"{x:4},{y:4},{temperature}")
                y += stepsize
            x += stepsize
        p.goto(z=self.safe_z)
        p.goto(x=self.present_x, y = self.present_y)
        

if __name__ == "__main__":
    import argparse
    def get_args():
        p = argparse.ArgumentParser()
        p.add_argument("-pp", "--printer-port", help="Printer port", required=True)
        p.add_argument("-pb", "--printer-baud", help="Printer Baud.  Default 115200", type=int, default=115200)
        p.add_argument("-sx", "--start-x", help="Start X location of scan", type=int, required=True)
        p.add_argument("-sy", "--start-y", help="Start Y location of scan", type=int, required=True)
        p.add_argument("-dx", "--delta-x", help="The X width of scan", type=int, required=True)
        p.add_argument("-dy", "--delta-y", help="The Y width of scan", type=int, required=True)
        p.add_argument("-g",  "--gridsize", help="Scanning grid step", type=int, required=True)
        p.add_argument("-sz", "--safe-z", help="Safe Z for all moves. Default=45", type=int, default=45)
        p.add_argument("-sn", "--scan-z", help="Scan Z during actual scanning. Default=10", type=int, default=10)
        p.add_argument("-tp", "--temp-port", help="Temperature scanner port", required=True)
        p.add_argument("-tb", "--temp-baud", help="Temperature baud", type=int, default=115200)
        p.add_argument("--logfile", help="name of logfile to dump to.  Default is scanner.log", default="scanner.log")
        args = p.parse_args()
        return args

    args = get_args()
    fprint("Starting Scan. Homing")
    logging.basicConfig(filename=args.logfile, encoding='utf-8', level=logging.DEBUG)
    s = Scanner(args.printer_port, args.printer_baud, args.safe_z, args.scan_z,
                args.temp_port, args.temp_baud)
    fprint("Homing complete")
    s.scan(args.start_x, args.start_y, args.delta_x, args.delta_y, args.gridsize)
