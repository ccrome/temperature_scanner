# The $11 Infrared Camera
![First Scan!](images/title.png)

Here I convert a cheap infrared thermomitor into a high resoultion thermal 'camera'.  Yes, it's incredibly slow, and hard to set up, but perhaps it could be useful to somebody? 

It does actually work, and is reasonably sensitive.

Items required:
* [Non-Contact Pocket Thermometer](https://www.harborfreight.com/non-contact-pocket-thermometer-93983.html)
* 3d-printer.  I used a CR-10
* 3.3V Arduino of some sort
* Pogo pins if you're going to use the pogo pins. Otherwise, direct solder is fine
  * [Outer sleeve](https://www.aliexpress.com/item/1005002180771613.html?spm=a2g0s.9042311.0.0.d7954c4dfTWMrA)
  * [Pins](https://www.aliexpress.com/item/1005002186463260.html?spm=a2g0s.9042311.0.0.d7954c4dfTWMrA)


This project aims to scan a PCB to find shorts and other thermal dissipation issues with the stuff I have lying 
around.

I've got a short circuit on a PCB, and wanted to find out where it is.  Yes, I should have a thermal camera, but I don't.  So, I started probing it with this [$11 infrared sensor](https://www.harborfreight.com/non-contact-pocket-thermometer-93983.html) from Harbor Freight.   That helped me figure out where the short is, but I figured it'd be nifty to use my 3D printer to scan along the PCB and take a thermal 'picture' pixel by pixel of the PCB. 

I opened up the back of the sensor, and what do you know... under the battery are 4 test points under the battery.  

![Test Points](images/testpoints.jpg)

And opening the back of the case up reveals that those test points are...  Clock, Data, 3V and GND, in that order.
![Back of thermal sensor](images/battery-contacts.jpg)

I applied 3 volts, and voila!  We get data!

![Data format](images/data-capture.jpg)

There are 4 pins:  Clock, Data, 3V and GND.  Pretty self-explanatory.  To make things easier, I built up a little pogo pin holder to easily interface with the device.    This pogo holder serves two purposes, to hold the pogo pins in place, and do depress the 'measure' button continuously.

![Pogo holder](images/pogo-holder-cad.jpg)
![Pogo holder](images/pogo-holder1.jpg)
![Pogo holder](images/pogo-holder2.jpg)
![Pogo holder](images/pogo-holder3.jpg)

The design files for this holder are in the [3d-files](3d-files) directory.

## Data format
After searching online for what seemed like forever, but was probably about 30 seconds, I couldn't find any documentation of the data format.  

### Arduino code
In order to capture the data more easily, I built up a little arduino sketch that will sniff the data (with a lousy but functional software shift-register) and print it out.

The arduino software is in the [arduino-code](arduino-code) directory.  Load this up on 3.3V arduino, whatever kind should work fine, as long as it's 3.3Volts, and you should start getting data spit out to the COM port console that looks like this:

```
0x0000004c1322810d
0x0000004c1321800d
0x0000004c13207f0d
0x000000530000530d
0x0000004c13207f0d
0x000000530000530d
0x0000006612c9410d
0x0000004c1321800d
0x0000004c13207f0d
0x0000004c131f7e0d
0x000000530000530d
0x0000006612c9410d
0x0000004c131f7e0d
```

### Python code to read and parse the arduino output
There is a python library for connecting to the arduino in the [python](python) directory.

After a few hours of plotting bits and scratching my head, It turns the data format is 40-bits.  When bits `[39:32] == 0x4c`, that's a data frame with temperature.  In that data frame, bits `[31:16]` are the temperature.  

Here's a temperature plot of some captured data as i pointed the sensor at a piece of old PCB and heated it up with a hot air gun.  Then took the PCB away, and put it back for a while.

![temperature plot](images/temperature-plot.jpg)

The x-axis is seconds, the Y axis is 'temperature'.  Units TBD.

## Capture program
This data was captured from the arduino COM port with the temperature-plot.py program, which does a live-updating plot of the temperature returned from the arduino.

# Bring on the 3d printer!
Now, I hot-glued the thing to my 3-d printer, and after a bunch of messing around with protocols, finally was able to make a scan!  

![Heatmap](images/heatmap.jpeg)

The scan was done with the scanner/scan.py script.

```python scan.py -pp COM13 -sx 00 -sy 25  -dx 140 -dy 70 -g 1  -tp COM8 -sz 30 -sn 15 avail-fine.csv```

Help on the scan program is available.
```
usage: scan.py [-h] -pp PRINTER_PORT [-pb PRINTER_BAUD] -sx START_X -sy
               START_Y -dx DELTA_X -dy DELTA_Y -g GRIDSIZE [-sz SAFE_Z]
               [-sn SCAN_Z] -tp TEMP_PORT [-tb TEMP_BAUD] [--logfile LOGFILE]
               resultsfile

positional arguments:
  resultsfile           text File to put results into

optional arguments:
  -h, --help            show this help message and exit
  -pp PRINTER_PORT, --printer-port PRINTER_PORT
                        Printer port
  -pb PRINTER_BAUD, --printer-baud PRINTER_BAUD
                        Printer Baud. Default 115200
  -sx START_X, --start-x START_X
                        Start X location of scan
  -sy START_Y, --start-y START_Y
                        Start Y location of scan
  -dx DELTA_X, --delta-x DELTA_X
                        The X width of scan
  -dy DELTA_Y, --delta-y DELTA_Y
                        The Y width of scan
  -g GRIDSIZE, --gridsize GRIDSIZE
                        Scanning grid step
  -sz SAFE_Z, --safe-z SAFE_Z
                        Safe Z for all moves. Default=45
  -sn SCAN_Z, --scan-z SCAN_Z
                        Scan Z during actual scanning. Default=10
  -tp TEMP_PORT, --temp-port TEMP_PORT
                        Temperature scanner port
  -tb TEMP_BAUD, --temp-baud TEMP_BAUD
                        Temperature baud
  --logfile LOGFILE     name of logfile to dump to. Default is scanner.log
  ```

Enjoy!  Comments, fixes, all welcome!