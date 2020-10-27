# SonOff Plugin
#
# Author: vdkuil
#
"""
<plugin key="BasePlug" name="SonOff Plugin" author="Roy van der Kuil" version="1.0.0" wikilink="http://www.domoticz.com/wiki/plugins/plugin.html" externallink="https://github.com/vdkuil/sonoff">
    <description>
        <h2>SonOff Plugin</h2><br/>
    </description>
    <params>
        <param field="Address" label="IP Address" width="200px" required="true" default="127.0.0.1"/>
        <param field="Port" label="Port" width="30px" required="true" default="8081"/>
        <param field="Mode6" label="Debug" width="75px">
            <options>
                <option label="Verbose" value="Verbose"/>
                <option label="True" value="Debug"/>
                <option label="False" value="Normal" default="true" />
            </options>
        </param>		
    </params>
</plugin>
"""
import Domoticz
import json

runDevice = 1

class BasePlugin:
    #enabled = False
    httpConn = None
    sendData = None
    runAgain = 6
    
    disconnectCount = 0
    sProtocol = "HTTP"


    def __init__(self):

        #self.var = 123
        return

    def onStart(self):
        Domoticz.Debug("onStart called")
        self.debugging = Parameters["Mode6"]
        if self.debugging == "Verbose":
            Domoticz.Debugging(2+4+8+16+64)
        if self.debugging == "Debug":
            Domoticz.Debugging(2)		
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
        Domoticz.Debug("onStop called")
        self.httpConn.Disconnect()

    def onConnect(self, Connection, Status, Description):
        Domoticz.Debug("onConnect called ")
        if (Status == 0):
            Domoticz.Debug("SonOff connected successfully.")
            if (self.sendData != None):
                Connection.Send(self.sendData)
        else:
            Domoticz.Log("Failed to connect ("+str(Status)+") to: "+Parameters["Address"]+":"+Parameters["Port"]+" with error: "+Description)

    def onMessage(self, Connection, Data):
        Domoticz.Debug("onMessage called")
        strData = Data["Data"].decode("utf-8", "ignore")
        Domoticz.Debug("Received data ("+strData+"), Devices: "+str(len(Devices)));        
        #Domoticz.Debug("Received data from "+str(len(Devices))+" devices.");        
        json_data = json.loads(strData)
        json_headers = Data["Headers"]
        Status = int(Data["Status"])
        #LogMessage(strData)
        #Domoticz.Debug("Received data ("+strData+"), Name: " + json_data[0]['name'] + ", Devices: ("+str(len(Devices))+"), Connection: "+json_headers['x-action']);
        #Domoticz.Debug("Received data ("+strData+"), Devices: ("+str(len(Devices))+"), Connection: "+json_headers['x-action']);
        y=0
        if (json_headers['x-action'] == 'list'):
            for sonoff_device in json_data:
                deviceId = sonoff_device['deviceid']
                device = [x for x in Devices if Devices[x].DeviceID == deviceId]
                if (len(device) == 0):
                    unitNr = nextUnitNr();
                    type = sonoff_device['type']
                    Domoticz.Log("Device not found " + deviceId + ", trying to create a new one " + type + " with id " + str(unitNr));
                    if (type == "10"):
                        myDevice = Domoticz.Device(Name=sonoff_device['name'], Unit=unitNr, Type=244, Subtype=62, Switchtype=0, Image=0, Options={}, Used=1, DeviceID=sonoff_device['deviceid']).Create();
                else:
                    Domoticz.Debug("Found existing device " + deviceId);                 
        elif (json_headers['x-action'] == 'on'):
            Domoticz.Debug("Action found "+json_headers['x-action']);        
        elif (json_headers['x-action'] == 'off'):
            Domoticz.Debug("Action found "+json_headers['x-action']);  
        elif (json_headers['x-action'] == 'status'):
            Domoticz.Debug("Action found "+json_headers['x-action']);
            if('error' in json_data):
                Domoticz.Debug("Msg with error. Don't procesing.");
            else:
                deviceId = json_data['deviceid']  
                state = json_data['state']      
                for x in Devices: 
                    if (Devices[x].DeviceID == deviceId):                  
                        if(state=='on' and Devices[x].nValue==0):
                            Devices[x].Update(nValue=1, sValue=Devices[x].sValue);
                            Domoticz.Debug("Found existing device with ID:" + deviceId + " with different states. Updating to state:" + state);
                        elif(state=='off' and Devices[x].nValue==1):
                            Devices[x].Update(nValue=0, sValue=Devices[x].sValue);        
                            Domoticz.Debug("Found existing device with ID:" + deviceId + " with different states. Updating to state:" + state);                                                 
        elif (json_headers['x-action'] == 'toggle'):
            Domoticz.Debug("Action found "+json_headers['x-action']);                    
        else:
            Domoticz.Log("Unsupported action found "+json_headers['x-action']);

        if (Status == 200):
            if ((self.disconnectCount & 1) == 1):
                Domoticz.Debug("Good Response received from server, Disconnecting.")
                self.httpConn.Disconnect()
            else:
                Domoticz.Debug("Good Response received from server, Dropping connection.")
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
        Domoticz.Debug("onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level) + "," + Devices[Unit].Name +","+Devices[Unit].DeviceID)
        if (self.httpConn != None and (self.httpConn.Connecting() or self.httpConn.Connected())):
            Domoticz.Debug("onCommand connected");
        else:
            Domoticz.Log("onCommand NOT connected");
            if(str(Command) == 'On'):
                self.sendData = { 'Verb' : 'GET',
                    'URL'  : '/on?id=' + Devices[Unit].DeviceID,
                    'Headers' : { 'Content-Type': 'application/json; charset=utf-8', \
                        'Connection': 'keep-alive', \
                        'Accept': 'Content-Type: application/json; charset=UTF-8', \
                        'Host': Parameters["Address"]+":"+Parameters["Port"], \
                        'User-Agent':'Domoticz/1.0' }
                    }
                Devices[Unit].Update(nValue=1, sValue=Devices[Unit].sValue);
            elif(str(Command) == 'Off'):
                self.sendData = { 'Verb' : 'GET',
                    'URL'  : '/off?id=' + Devices[Unit].DeviceID,
                    'Headers' : { 'Content-Type': 'application/json; charset=utf-8', \
                        'Connection': 'keep-alive', \
                        'Accept': 'Content-Type: application/json; charset=UTF-8', \
                        'Host': Parameters["Address"]+":"+Parameters["Port"], \
                        'User-Agent':'Domoticz/1.0' }
                    }
                Devices[Unit].Update(nValue=0, sValue=Devices[Unit].sValue);
            else:
                self.sendData = { 'Verb' : 'GET',
                    'URL'  : '/toggle?id=' + Devices[Unit].DeviceID,
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
        Domoticz.Debug("Notification: " + Name + "," + Subject + "," + Text + "," + Status + "," + str(Priority) + "," + Sound + "," + ImageFile)

    def onDisconnect(self, Connection):
        Domoticz.Debug("onDisconnect called")
        
    def onStatus(self, Unit):
        global runDevice
        if (self.httpConn != None and (self.httpConn.Connecting() or self.httpConn.Connected())):
            Domoticz.Debug("onStatus connected");
        else:        
            Domoticz.Debug("onStatus called for Unit " + str(Unit) + " con ID " + Devices[Unit].DeviceID)
            if(runDevice==Unit):
                self.sendData = { 'Verb' : 'GET',
                    'URL'  : '/status?id=' + Devices[Unit].DeviceID,
                    'Headers' : { 'Content-Type': 'application/json; charset=utf-8', \
                        'Connection': 'keep-alive', \
                        'Accept': 'Content-Type: application/json; charset=UTF-8', \
                        'Host': Parameters["Address"]+":"+Parameters["Port"], \
                        'User-Agent':'Domoticz/1.0' }
                    }
                self.httpConn = Domoticz.Connection(Name="SonOff EWELink connection", Transport="TCP/IP", Protocol=self.sProtocol, Address=Parameters["Address"], Port=Parameters["Port"])
                self.httpConn.Connect()
            runDevice+=1
            if (len(Devices) < runDevice):
                runDevice = 1

    def onHeartbeat(self):
        global runDevice    
        Domoticz.Debug("onHeartbeat called")
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
        onStatus(runDevice)          
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
    
def onStatus(Unit):
    global _plugin
    _plugin.onStatus(Unit)    

def onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile):
    global _plugin
    _plugin.onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile)

def onDisconnect(Connection):
    global _plugin
    _plugin.onDisconnect(Connection)

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

def nextUnitNr():
    unitNr = 1
    while unitNr in Devices:
        unitNr = unitNr + 1;
    return unitNr

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
