from canard import can
from canard.hw import cantact
import sys

dev = cantact.CantactDev(sys.argv[1])
dev.set_bitrate(1000000)
dev.start()
count = 0
while True:
    frames = dev.recv_buff(8192)
    for data in frames:
    	count = count + 1
    	print("%d: %s" % (count, str(data)))
