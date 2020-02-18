# SonOff Plugin
#
# Author: GizMoCuz
#
"""
<plugin key="BasePlug" name="SonOff Plugin" author="Roy van der Kuil" version="1.0.0" wikilink="http://www.domoticz.com/wiki/plugins/plugin.html" externallink="https://github.com/vdkuil/sonoff">
    <description>
        <h2>SonOff Plugin</h2><br/>
    </description>
    <params>
        <param field="Address" label="IP Address" width="200px" required="true" default="127.0.0.1"/>
        <param field="Port" label="Port" width="30px" required="true" default="8081"/>
    </params>
</plugin>
"""
import Domoticz
import json

class BasePlugin:
    #enabled = False
    deleted = True
    httpConn = None
    sendData = None
    runAgain = 6
    disconnectCount = 0
    sProtocol = "HTTP"


    def __init__(self):
        #self.var = 123
        return

    def onStart(self):
        Domoticz.Log("onStart called")
        if (Parameters["Port"] == "443"): self.sProtocol = "HTTPS"
        self.sendData = { 'Verb' : 'GET',
                     'URL'  : '/list',
                     'Headers' : { 'Content-Type': 'application/json; charset=utf-8', \
                                   'Connection': 'keep-alive', \
                                   'Accept': 'Content-Type: application/json; charset=UTF-8', \
                                   'Host': Parameters["Address"]+":"+Parameters["Port"], \
                                   'User-Agent':'Domoticz/1.0' }
                   }
        self.httpConn = Domoticz.Connection(Name="SonOff EWELink connection", Transport="TCP/IP", Protocol=self.sProtocol, Address=Parameters["Address"], Port=Parameters["Port"])
        self.httpConn.Connect()

    def onStop(self):
        Domoticz.Log("onStop called")
        self.httpConn.Disconnect()

    def onConnect(self, Connection, Status, Description):
        Domoticz.Log("onConnect called ")
        if (Status == 0):
            Domoticz.Debug("SonOff connected successfully.")
            if (self.sendData != None):
                Connection.Send(self.sendData)
        else:
            Domoticz.Log("Failed to connect ("+str(Status)+") to: "+Parameters["Address"]+":"+Parameters["Port"]+" with error: "+Description)

    def onMessage(self, Connection, Data):
        Domoticz.Log("onMessage called")
        strData = Data["Data"].decode("utf-8", "ignore")
        json_data = json.loads(strData);
        json_headers = Data["Headers"]
        Status = int(Data["Status"])
        #LogMessage(strData)
        #Domoticz.Log("Received data ("+strData+"), Name: " + json_data[0]['name'] + ", Devices: ("+str(len(Devices))+"), Connection: "+json_headers['x-action']);
        Domoticz.Log("Received data ("+strData+"), Devices: ("+str(len(Devices))+"), Connection: "+json_headers['x-action']);
        if (json_headers['x-action'] == 'list'):
            if (self.deleted == False):
                self.deleted = True;
                for x in Devices:
                    Domoticz.Log("Device:           " + str(x) + " - " + str(Devices[x]))
                    Devices[x].Delete();
            if (len(Devices) == 0):
                for sonoff_device in json_data:
                    Domoticz.Log("Creating device (Name="+sonoff_device['name']+", TypeName=Light/Switch");
                    myDevice = Domoticz.Device(Name=sonoff_device['name'], Unit=1, Type=244, Subtype=62, Switchtype=0, Image=0, Options={}, Used=1, DeviceID=sonoff_device['deviceid']).Create();
        else:
            Domoticz.Log("Unsupported action found "+json_headers['x-action']);

        if (Status == 200):
            if ((self.disconnectCount & 1) == 1):
                Domoticz.Log("Good Response received from server, Disconnecting.")
                self.httpConn.Disconnect()
            else:
                Domoticz.Log("Good Response received from server, Dropping connection.")
                self.httpConn = None
            self.disconnectCount = self.disconnectCount + 1
        elif (Status == 302):
            Domoticz.Log("Server returned a Page Moved Error.")
            sendData = { 'Verb' : 'GET',
                         'URL'  : Data["Headers"]["Location"],
                         'Headers' : { 'Content-Type': 'text/xml; charset=utf-8', \
                                       'Connection': 'keep-alive', \
                                       'Accept': 'Content-Type: text/html; charset=UTF-8', \
                                       'Host': Parameters["Address"]+":"+Parameters["Mode1"], \
                                       'User-Agent':'Domoticz/1.0' }
                        }
            Connection.Send(sendData)
        elif (Status == 400):
            Domoticz.Error("Server returned a Bad Request Error.")
        elif (Status == 500):
            Domoticz.Error("Server returned a Server Error.")
        else:
            Domoticz.Error("Server returned a status: "+str(Status))

    def onCommand(self, Unit, Command, Level, Hue):
        Domoticz.Log("onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level) + "," + Devices[Unit].Name +","+Devices[Unit].DeviceID)
        if (self.httpConn != None and (self.httpConn.Connecting() or self.httpConn.Connected())):
            Domoticz.Log("onCommand connected");
        else:
            Domoticz.Log("onCommand NOT connected");
            self.sendData = { 'Verb' : 'GET',
                         'URL'  : '/dummy?id=' + Devices[Unit].DeviceID,
                         'Headers' : { 'Content-Type': 'application/json; charset=utf-8', \
                                       'Connection': 'keep-alive', \
                                       'Accept': 'Content-Type: application/json; charset=UTF-8', \
                                       'Host': Parameters["Address"]+":"+Parameters["Port"], \
                                       'User-Agent':'Domoticz/1.0' }
                       }
            self.httpConn = Domoticz.Connection(Name="SonOff EWELink connection", Transport="TCP/IP", Protocol=self.sProtocol, Address=Parameters["Address"], Port=Parameters["Port"])
            self.httpConn.Connect()
        #Connection.Send(sendData)

    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        Domoticz.Log("Notification: " + Name + "," + Subject + "," + Text + "," + Status + "," + str(Priority) + "," + Sound + "," + ImageFile)

    def onDisconnect(self, Connection):
        Domoticz.Log("onDisconnect called")

    def onHeartbeat(self):
        Domoticz.Log("onHeartbeat called")
        if (self.httpConn != None and (self.httpConn.Connecting() or self.httpConn.Connected())):
            Domoticz.Debug("onHeartbeat called, Connection is alive.")
        else:
            self.runAgain = self.runAgain - 1
            if self.runAgain <= 0:
                if (self.httpConn == None):
                    self.httpConn = Domoticz.Connection(Name="SonOff EWELink connection", Transport="TCP/IP", Protocol=self.sProtocol, Address=Parameters["Address"], Port=Parameters["Port"])
                self.sendData = { 'Verb' : 'GET',
                             'URL'  : '/list',
                             'Headers' : { 'Content-Type': 'application/json; charset=utf-8', \
                                           'Connection': 'keep-alive', \
                                           'Accept': 'Content-Type: application/json; charset=UTF-8', \
                                           'Host': Parameters["Address"]+":"+Parameters["Port"], \
                                           'User-Agent':'Domoticz/1.0' }
                           }
                self.httpConn.Connect()
                self.runAgain = 6
            else:
                Domoticz.Debug("onHeartbeat called, run again in "+str(self.runAgain)+" heartbeats.")
        #Domoticz.Trace(False)

global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onStop():
    global _plugin
    _plugin.onStop()

def onConnect(Connection, Status, Description):
    global _plugin
    _plugin.onConnect(Connection, Status, Description)

def onMessage(Connection, Data):
    global _plugin
    _plugin.onMessage(Connection, Data)

def onCommand(Unit, Command, Level, Hue):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Hue)

def onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile):
    global _plugin
    _plugin.onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile)

def onDisconnect(Connection):
    global _plugin
    _plugin.onDisconnect(Connection)

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

    # Generic helper functions
def DumpConfigToLog():
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Debug( "'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Debug("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Debug("Device:           " + str(x) + " - " + str(Devices[x]))
        Domoticz.Debug("Device ID:       '" + str(Devices[x].ID) + "'")
        Domoticz.Debug("Device Name:     '" + Devices[x].Name + "'")
        Domoticz.Debug("Device nValue:    " + str(Devices[x].nValue))
        Domoticz.Debug("Device sValue:   '" + Devices[x].sValue + "'")
        Domoticz.Debug("Device LastLevel: " + str(Devices[x].LastLevel))
    return
