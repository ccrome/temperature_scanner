import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import argparse


def get_args():
    p = argparse.ArgumentParser("Plot a temperature log output from scan.py")
    p.add_argument("filename", help="Filename of logfile to plot")
    args = p.parse_args()
    return args

def read_temps(filename):
    temps = pd.read_csv(filename, skiprows=4, names=("x", "y", "temp"))
    xs = temps["x"].to_numpy()
    ys = temps["y"].to_numpy()
    ts = temps["temp"].to_numpy()
    return xs, ys, ts

def make_heatmap(temps):
    xs, ys, ts = temps
    mean = np.mean(ts)
    minx = np.min(xs)
    maxx = np.max(xs)
    miny = np.min(ys)
    maxy = np.max(ys)
    dx=np.unique(np.diff(np.sort(np.unique(xs))))
    dy=np.unique(np.diff(np.sort(np.unique(ys))))
    assert(len(dx)==1)
    assert(len(dy)==1)
    dx = dx[0]
    dy = dy[0]
    nx=int((maxx-minx)/dx)+1
    ny=int((maxy-miny)/dy)+1
    grid = np.zeros((nx, ny))
    for x, y, temp in zip(xs, ys, ts):
        xi = int(round((x - minx)/dx))
        yi = int(round((y - miny)/dy))
        grid[xi, yi] = temp
    return grid

def plot(grid):
    plt.imshow(np.rot90(grid))
    plt.colorbar()
    plt.show()
    
args = get_args()
temps = read_temps(args.filename)
heatmap = make_heatmap(temps)

plot(heatmap)
#print(temps)
