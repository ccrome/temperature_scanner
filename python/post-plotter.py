import numpy as np
import collections
import matplotlib.pyplot as plt
import argparse
import itertools

def plot_by_nibbles(times, values):
    for frame in range(1):
        curvalues = values
        curtimes = times
        curtimes = np.array(range(len(curvalues)))

        #curvalues = curvalues[120:160]
        #curtimes = curtimes[120:160]

        data_mask = (curvalues >> 32) == 0x4c
        curvalues = curvalues[data_mask]
        curtimes = curtimes[data_mask]
        linestyle = args.linespoints
        spacer = 1.0
        zero=1

        fig, ((ax0, ax1), (ax2, ax3)) = plt.subplots(nrows = 2, ncols=2, sharex=True)
        maybe =  (curvalues >> (16)) & 0x0fff
        maybe2 = (curvalues >> (0))  & 0x03ff
        ax1.plot(curtimes, maybe)
        ax1.plot(curtimes, maybe2)
        for n in range(3):
            nibble = np.array([ (x>>(n*16)) & 0xFFFF for x in curvalues])
            ax0.plot(curtimes, (nibble*spacer)+(65536*n*zero), linestyle, label=f"{n}")
            ax0.set_title("16bits")
        for n in range(5):
            nibble = np.array([ (x>>(n*8)) & 0xFF for x in curvalues])
            ax1.plot(curtimes, (nibble*spacer)+(256*n*zero), linestyle, label=f"{n}")
            ax1.set_title("8bits")
        for n in range(10):
            nibble = np.array([ (x>>(n*4)) & 0xF for x in curvalues])
            ax2.plot(curtimes, (nibble*spacer)+(16*n*zero), linestyle, label=f"{n}")
            ax2.set_title("4bits")
        for n in range(40):
            nibble = np.array([ (x>>(n)) & 0x1 for x in curvalues])
            ax3.plot(curtimes, (nibble*spacer)+(n*zero), "*-", label=f"{n}")
            ax3.set_title("1bit")
        ax3.grid()
        #plt.legend()
        plt.show()
	
def bitrev(x):
    y = 0
    for i in range(40):
        y = y << 1
        y = y + (x & 1)
        x = x >> 1
    return y

def get_args():
    p = argparse.ArgumentParser()
    p.add_argument("file", help="Filename of file to parse.  Should be a csv of (time, hex value).")
    p.add_argument("-l", "--linespoints", help="Lines or points.  default is '-', but can be '*' for points, or '*-' for lines and points", default="-")
    args = p.parse_args()
    return args

args = get_args()
lines = open(args.file).readlines()
lines = [x.split(",") for x in lines]
lines = [(float(x[0]),int(x[1][2:].strip(), 16)) for x in lines]

times = np.array([x[0] for x in lines])
times = times-times[0]
values = np.array([x[1] for x in lines])

#values = [bitrev(x) for x in values]

freqs = {}
for i in range(10):
    freqs[i] = np.array([((x >> (i*4)) & 0xF) for x in values])
    n = np.unique(freqs[i])
    print(i, len(n), n)

# Bits 32-40:
#    0x4c = data frame
#    0x53 = not data frame
#    0x66 = another not data frame
#
# Bits 16-32 seems to be temperature

# plot_by_nibbles(times, values)
# frametypes = [0x4c, 0x53, 0x66]
frametypes = [0x4c]
for frametype in frametypes:
    mask = ((values >> 32) & 0xFF) == frametype
    t = times[mask]
    v = (values[mask] >> 16) & 0xFFFF
    plt.plot(t, v, label=f"frametype = {frametype}")
plt.legend()
plt.show()


