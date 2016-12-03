#!/usr/bin/python -u

import serial
import time
import sys
import re
import calendar
from optparse import OptionParser
from easyweatherpkt import ew_check_and_decode

SECRET = "SubmissionSecretCode"

from collections import deque

pending_data = deque()

def submit_data(url, t, dec):
    import urllib, urllib2

    data = {
        'timestamp' : "%u" % (t),
        'temperature' : dec[0],
        'humidity' : dec[1],
        'avg_wind' : dec[2],
        'peak_wind' : dec[3],
        'rainfall_ctr' : int(dec[4] * 10),
        'wind_dir' : dec[5],
        'orig_avg_wind' : dec[6],
        'orig_peak_wind' : dec[7],
        'secret' : SECRET
    }
    pending_data.append(data)

    while len(pending_data):
	data = pending_data[0]
    	html_data = urllib.urlencode(data)
    	try:
        	resp = urllib2.urlopen(url, html_data)
		good_response = False
		error = ""
    		for l in resp:
        		if l.startswith("1 record added") or l.find("Duplicate") != -1:
				good_response = True
			else:
				error += l.strip()
		if not good_response:
        		print "Submission failed (%d pending): %s" % (len(pending_data), error)
			return False
    	except urllib2.URLError, e:
        	print "Submit error:", e.reason, "(%d pending)" % (len(pending_data))
        	return False

    	# for l in resp:
        	# print l
	pending_data.popleft()

    return True        
    
def process_file_line(l, url):
    dline = re.compile("([0-9]+) ((?:[0-9A-F]{1,2}[ ]){11})")
    m = dline.match(l)
    if m is None:
        # Check if it is a decoded line already
        #dline = re.compile("\(([0-9]+),((?:[0-9\.])\), ){11}")
        #m = dline.match(l)
        pass

    if m is None:
        return # Not a valid packet

    t = int (m.group(1))
    pkt = m.group(2).rstrip().split()
    pkt = map(lambda x: int (x, 16), pkt)
    return process_packet(t, pkt, url)

def process_serial_line (t, data, url):
    dline = re.compile("((?:[0-9A-F]{1,2}[ ]){11})")
    m = dline.match(data)
    if m is None:
        return # Not a valid packet

    pkt = m.group(1).rstrip().split()
    pkt = map(lambda x: int (x, 16), pkt)
    return process_packet(t, pkt, url)

def process_packet (t, data, url):
    # print "%u %s # %s" % (t, data, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t)))
    dec = ew_check_and_decode(data)
    if dec is None:
        return # Garbage packet
    if url is not None:
        if (submit_data(url, t, dec)):
            print (time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t)),) + dec, "OK"
        else:
            print (time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t)),) + dec, "Fail"
    else:
        print (t,) + dec, "#", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t))

def main_program():
    parser = OptionParser()
    parser.add_option("-f", "--file", dest="filename",
                  help="Read packets from file filename", metavar="FILE")
    parser.add_option("-s", "--serial", dest="serialport",
                  help="Read packets from serial device (default if no args are given = /dev/ttyUSB0)", metavar="SERIAL", default='/dev/ttyUSB0')
    parser.add_option("-u", "--url", dest="url",
                  help="weather_upload.php URL to submit data to", metavar="URL", default=None)
    parser.add_option("-l", "--log", dest="logfile",
                  help="Logfile for raw packet data (serial port mode only)", metavar="LOGFILE", default=None)
    (options, args) = parser.parse_args()

    if options.filename is not None:
        f = open(options.filename)
        for l in f:
            process_file_line(l, options.url)
        return 0

    done = False
    while not done:
    	try:
    		ser = serial.Serial(options.serialport, 115200)  # open serial port
    		while True:
        		l = ser.readline().rstrip()
        		t = time.time();
        		if options.logfile:
        			logfile = open(options.logfile, "a+", 1)
            			logfile.write("%u %s # %s\n" % (t, l, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t))))
				del logfile
        		process_serial_line(t, l, options.url)
    		ser.close()
	except serial.SerialException, e:
		print "Got serial exception %s" % (repr(e))
    		ser.close()
		time.sleep(1)
	except:
		print "Unknown exception. Exiting", sys.exc_info()[0]
		done = True

    return 0

if __name__ == '__main__':
    sys.exit(main_program())
