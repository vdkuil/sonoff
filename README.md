# Sonoff project for enabeling sonoff devices in Domoticz
This project contains a server component and a domoticz plugin

## Server component
### Installation
Install the base modules using npm:
```bash
npm install ewelink-api
npm install express
npm install minimist
```
### Running
node server.js -e `email` -p `password` -r us -o 8081
The parameters -r and -o are optional


## Plugin component

### Installation
copy plugin/plugin.py  to domotiz/plugins/SonOff/plugin.py

You have to make sure you have python3 (and python3-dev) installed on your domoticz system. Usually this can be done with
```bash
apt-get install python3-dev
```
