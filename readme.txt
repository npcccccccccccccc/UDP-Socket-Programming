UDP Socket Programming

1. Environments
python=3.9

2. Preparation
client:
import datetime
from socket import *
import struct
import time
from statistics import mean, stdev

server:
import datetime
import random
import threading
from socket import *
import struct
import time

client按提示输入SERVER_IP、SERVER_PORT、PACKET_NUM
server修改常量SERVER_IP为guest的ip

3. Running
python UDPserver.py(guest os)
python UDPclient.py(host os)
