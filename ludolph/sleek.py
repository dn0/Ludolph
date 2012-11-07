import sys
import os
import logging
import subprocess
import time
from sleekxmpp import ClientXMPP
from sleekxmpp.exceptions import IqError, IqTimeout
from version import __version__
# In order to make sure that Unicode is handled properly
# in Python 2.x, reset the default encoding.
if sys.version_info < (3, 0):
    from ConfigParser import RawConfigParser
else:
    from configparser import RawConfigParser

log = logging.getLogger(__name__)

class LudolphBot(ClientXMPP):

    def __init__(self, config):
        ClientXMPP.__init__(self,
                config.get('login','username'),
                config.get('login','password'))

        self.config = config
        self.add_event_handler("session_start", self.session_start)
        self.add_event_handler("message", self.message)
        self._start_thread('thread_proc', self._thread_proc)
        # If you wanted more functionality, here's how to register plugins:
        # self.register_plugin('xep_0030') # Service Discovery
        # self.register_plugin('xep_0199') # XMPP Ping

        # Here's how to access plugins once you've registered them:
        # self['xep_0030'].add_feature('echo_demo')

        # If you are working with an OpenFire server, you will
        # need to use a different SSL version:
        # import ssl
        # self.ssl_version = ssl.PROTOCOL_SSLv3

    def session_start(self, event):
        self.send_presence()
        self.get_roster()

        # Most get_*/set_* methods from plugins use Iq stanzas, which
        # can generate IqError and IqTimeout exceptions
        #
        # try:
        #     self.get_roster()
        # except IqError as err:
        #     logging.error('There was an error getting the roster')
        #     logging.error(err.iq['error']['condition'])
        #     self.disconnect()
        # except IqTimeout:
        #     logging.error('Server is taking too long to respond')
        #     self.disconnect()

    def message(self, msg):
        if msg['type'] in ('chat', 'normal'):
            # Seek received text in available commands
            if msg['body'] in self.available_commands():
                # transform string into executable function
                function = getattr(self, msg['body'])
                function(msg)
            else:
                # Send message that command was not understod and what to do
                self.send_message(mto=msg['from'],
                                mbody="I dont understand %(body)s." % msg,
                                mtype='chat')
                self.send_message(mto=msg['from'],
                                mbody="Please type help for more info",
                                mtype='chat')

    def available_commands(self):
        # List of all available commands for bot
        config_commands = {}
        for command in self.config.items('available_commands'):
            config_commands[command[0]] = command[1]
        return config_commands

    def who(self, msg):
        self.send_message(mto=msg['from'],
                    mbody=str(subprocess.check_output('who')),
                    mtype='chat')

    def uptime(self, msg):
        self.send_message(mto=msg['from'],
                    mbody=str(subprocess.check_output('uptime')),
                    mtype='chat')

    def help(self, msg):
        self.send_message(mto=msg['from'],
                        mbody='List of known commands:',
                        mtype='chat')
        all_commands = self.available_commands()
        for command in all_commands:
            self.send_message(mto=msg['from'],
                    mbody=command +" - "+ all_commands[command],
                    mtype='chat')
        # Function to send out available commands if called

    def version(self, msg):
        msg.reply('Version: '+ __version__).send()
        # pely with a Ludolph version to user

    def about(self, msg):
        msg.reply("""
            Ludolph - Monitoring Jabber bot
            Version: """+ __version__ +"""
            Homepage: https://github.com/ricco386/Ludolph
            Copyright (C) 2012 Richard Kellner & Daniel Kontsek
            This program comes with ABSOLUTELY NO WARRANTY. For details type
            'about'.
            This is free software, and you are welcome to redistribute it under
            certain conditions.""").send()
        # details about what is this project aobut

    def _thread_proc(self):
        with open(self.config.get('zabbix','pipe_file'), 'r') as fifo:
            while not self.stop.is_set():
                line = fifo.readline().strip()
                if line:
                    data = line.split(';', 1)
                    if len(data) == 2:
                        self.send_message(mto=data[0],
                                mbody=data[1],
                                mtype='chat')
                    else:
                        log.warning('Bad message format ("%s")' % (line))
                time.sleep(1)
                if self.stop.is_set():
                    self._end_thread('thread_proc')
                    return


def start():
    config = RawConfigParser()
    path = os.path.dirname(os.path.abspath(__file__))

    try:
        config.readfp(open(path +'/config.cfg'))
    except IOError:
        print >> sys.stderr, """
        You need to create a config file. You can rename config.example.cfg
        and update required variables. See example file for more
        details.
        File is located: """+ path +"\n"
        sys.exit(-1)

    logging.basicConfig(filename=config.get('loging','filename'),
                        level=config.get('loging','level'),
                        format='%(asctime)s %(levelname)-8s %(message)s')

    os.mkfifo(config.get('zabbix','pipe_file'), 0o600)
    try:
        xmpp = LudolphBot(config)
        xmpp.connect()
        xmpp.process(block=True)
    finally:
        os.remove(config.get('zabbix','pipe_file'))

if __name__ == '__main__':
    start()
