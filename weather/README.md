This directory contains an arduino sketch which reads
EasyWeather packets off the air using an RFM01 FM receiver,
and spits them out over the serial port to a python script
which decodes them and submits them to a web URL

There's also some sample data from my weather
station, which you can use to test the python
script like this:

./capture_decode_serial.py -f weather-data-capture.txt

