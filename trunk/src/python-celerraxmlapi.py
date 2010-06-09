import time
import urllib
import urllib2
import cookielib
import threading

from xml.dom.minidom import Document

class CelerraAPISleeper ( threading.Thread ):
    """ 
    Sleeper thread for sending keepalive messages to
    the API, needs to run every 15 minutes
    """
    
    def __init__(self,APIConnection):
        self.Connection = APIConnection
        self._finished= threading.Event()
        self._paused = threading.Event()
        self._interval = 1800
        threading.Thread.__init__(self)

    def shutdown(self):
        self._finished.set()

    def pause(self):
        self._paused.set()

    def unpause(self):
        self._paused.clear()

    def _sendKeepAlive(self):

        print "KeepAlive"
        # Empty Packet info (used for keepalive
        data = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><RequestPacket xmlns="http://www.emc.com/schemas/celerra/xml_api"/>'

        req = urllib2.Request(self.Connection._url,data,self.Connection._useragent)
        req.add_header('Content-Type','text/xml')
        response = self.Connection._opener.open(req)

        print response.read()

    def run(self):

        while True:
            if self._finished.isSet(): return
            if self._paused.isSet():
                pass
            else:
                self._sendKeepAlive()
            self._finished.wait(self._interval)

class CelerraAPIConnection:
    def __init__(self,nasIP,nasUser,nasPass):
    
        self._isConnected = False
            
        # Setup our CookieJar and Opener
        self._cj = cookielib.LWPCookieJar()
         
        self._opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self._cj))
        
        # Our URLs for connection
        self._loginurl = 'https://' + nasIP + '/Login'
        self._url = 'https://' + nasIP + '/servlets/CelerraManagementServices'
        
        # We fake out the User-agent, just in case EMC gets funny with us
        self._useragent = {'User-agent' : 'Mozilla/4.0 (compatible; MSIE5.5; Windows NT)'}
        
        # Setup our login values
        self._loginValues = {'Login':'Login', 'user':nasUser, 'password':nasPass}

    def connect(self):
       
        data = urllib.urlencode(self._loginValues)
        req = urllib2.Request(self._loginurl,data,self._useragent)

        response = self._opener.open(req)
        if len(self._cj) == 0:   # We should have a cookie if we got authenticated
            return 1   # Should throw an exception here probably
        else :
            self._isConnected = True
            self._sleeper = CelerraAPISleeper(self)
            self._sleeper.start()

    def disconnect(self):
        self._killSleeper()
        self._isConnected = False
        
    def _killSleeper(self):
        print "Sleeper for "+ self._url +" Shutdown"
        self._sleeper.shutdown()

def __main__():
    NP2=CelerraAPIConnection('172.16.99.30','nasadmin','nasadmin')
    NP2.connect()
    NP1=CelerraAPIConnection('172.16.101.85','nasadmin','nasadmin')
    NP1.connect()

__main__()


