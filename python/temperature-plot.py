import serial
from sys import stdout
import time
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import threading

port = "COM8"
com = serial.Serial(port)
f = open("temperature.log", "w")

def get_temp(x):
    if (x >> 32) & 0xFF == 0x4c:
        return (x>> 16) & 0xFFFF
    else:
        return None

def animate(i, ax, xs, ys):
    ax.clear()
    ax.plot(xs, ys)
    
def temp_reader_thread(times, values):
    while True:
        #c = com.read(size=1).decode('utf-8')
        c = com.readline().decode('utf-8')
        try:
            if c.startswith("0x"):
                value = int(c, 16)
                now = time.time()
                tstr  = f"{now:15.15},0x{value:010x}\n"
                for o in [f]:
                    o.write(tstr)
                    o.flush()
                v = get_temp(value)
                if v is not None:
                    times.append(now)
                    values.append(v)
        except:
            pass

times = []
values = []

x= threading.Thread(target=temp_reader_thread, args=(times, values), daemon=True)

fig, ax0 = plt.subplots(nrows=1, ncols=1)
ani = animation.FuncAnimation(fig, animate, fargs=(ax0, times, values), interval = 100)
x.start()
plt.show()
#fig, ax0 = plt.subplots(nrows=1, ncols=1)
