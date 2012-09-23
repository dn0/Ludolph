#!/usr/bin/python

import sys
try:
#    import jabberbot
    from jabberbot import JabberBot, botcmd
except ImportError:
    print >> sys.stderr, """
    You need to install jabberbot from http://thp.io/2007/python-jabberbot.
    On Debian-based systems, install the python-jabberbot package.
    """
    sys.exit(-1)

import subprocess
import threading
import time
import logging
import os

try:
    from config import *
except ImportError:
    print >> sys.stderr, """
    You need to create a config file. You can rename config.example.py and
    update required variables. 
    File is located: """ + os.getcwd() +"\n"
    sys.exit(-1)

class RPI(JabberBot):
    def __init__(self):
        super(RPI, self).__init__(JID, PWD, RES)
        # create console handler
        # chandler = logging.StreamHandler()
        # create file handler
        chandler = logging.FileHandler(LOG)
        # create formatter
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        # add formatter to handler
        chandler.setFormatter(formatter)
        # add handler to logger
        self.log.addHandler(chandler)
        # set level to INFO
        self.log.setLevel(logging.INFO)

        self.message_queue = []
        self.thread_killed = False

    @botcmd
    def uptime(self, mess, args):
        """
        Server uptime
        """
        return subprocess.check_output('uptime')

    def idle_proc(self):
        if not len(self.message_queue):
            return

        # copy the message queue, then empty it
        messages = self.message_queue
        self.message_queue = []

        for message in messages:
            self.log.info('sending message to %s with text: "%s"' % (message[0], message[1]))
            self.send(message[0], message[1])

    def thread_proc(self):
        with open(PIPE, 'r') as fifo:
            while not self.thread_killed:
                line = fifo.readline().strip()
                if line:
                    data = line.split(';', 1)
                    if len(data) == 2:
                        self.message_queue.append(data)
                    else:
                        self.log.error('bad message format ("%s")' % (line))
                time.sleep(1)
                if self.thread_killed:
                    return

def start():
    rpi = RPI()
    th = threading.Thread(target = rpi.thread_proc)
    rpi.serve_forever(connect_callback = lambda: th.start())
    rpi.thread_killed = True

if __name__ == '__main__':
    os.mkfifo(PIPE, 0600)
    try:
        start()
    finally:
        os.remove(PIPE)