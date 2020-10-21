var express = require('express');
const ewelink = require('ewelink-api');
var minimist = require('minimist');
var app = express();


var args = minimist(process.argv.slice(2), {
  default: {
    r: 'eu',
    o: 8081
  }
});

console.log('args:', args);

if (!args['e'] || !args['p']) {
  console.log('Missing argument e(mail) or p(assword)');
  console.log('Exiting');
  return;
}
console.log('email', args['e']);
console.log('region', args['r']);
console.log('runing port', args['o']);

const connection = new ewelink({
      email: args['e'],
      password: args['p'],
      region: args['r']
});

const port = args['o'];

/* get all devices */
(async () => {
  const devices = await connection.getDevices();
  
  function findDevice(query) {
       var id = query.id;
       if (id) {
         return devices.find(device => device.deviceid === id);
       }
       var name = query.name;
       if (name) {
         return devices.find(device => device.name === name);
       }
       return null;
  }

  app.get('/list', function (req, res) {
       res.writeHead(200, {'Content-Type': 'application/json;utf-8', 'x-action':'list'});
       //res.end( '{"id":'+devices[0].deviceid+'"}' );
       res.end( JSON.stringify(devices));
     });
  
  app.get('/status', function (req, res) {
     var device = findDevice(req.query);
     if (device) {
       res.writeHead(200, {'Content-Type': 'application/json;utf-8', 'x-action':'status'});
       res.end( JSON.stringify(device));
     } else {
       res.writeHead(400, {'Content-Type': 'application/json;utf-8'});
       res.end( '{"error":"Missing id or name parameter"}');
     }
  });

  app.get('/toggle', async (req, res) => {
	var funciono = true;
	var device = findDevice(req.query);
	if (device) {
		res.writeHead(200, {'Content-Type': 'application/json;utf-8', 'x-action':'toggle'});
		while (funciono) {
			try {
				const status = await connection.toggleDevice(device.deviceid);
				res.end( JSON.stringify(status));
				console.log("ON" + status);
				var funciono = false;
			} catch (error) {
				console.log(error)
			}
		}
	} else {
		res.writeHead(400, {'Content-Type': 'application/json;utf-8'});
		res.end( '{"error":"Missing id or name parameter"}');
	}
  });
  
  app.get('/on', async (req, res) => {
	var funciono = true;
	var device = findDevice(req.query);
	if (device) {
		res.writeHead(200, {'Content-Type': 'application/json;utf-8', 'x-action':'on'});
		while (funciono) {
			try {
				const status = await connection.setDevicePowerState(device.deviceid, 'on');
				res.end( JSON.stringify(status));
				console.log("ON" + status);
				var funciono = false;
			} catch (error) {
				console.log(error)
			}
		}
	} else {
		res.writeHead(400, {'Content-Type': 'application/json;utf-8'});
		res.end( '{"error":"Missing id or name parameter"}');
	}
  });
  
  app.get('/off', async (req, res) => {
	var funciono = true;
	var device = findDevice(req.query);
	if (device) {
		res.writeHead(200, {'Content-Type': 'application/json;utf-8', 'x-action':'off'});
		while (funciono) {
			try {
				const status = await connection.setDevicePowerState(device.deviceid, 'off');
				res.end( JSON.stringify(status));
				console.log("ON" + status);
				var funciono = false;
			} catch (error) {
				console.log(error)
			}
		}
	} else {
		res.writeHead(400, {'Content-Type': 'application/json;utf-8'});
		res.end( '{"error":"Missing id or name parameter"}');
	}
  }); 
  
  var server = app.listen(port, function () {
  	   var host = server.address().address
  	   var port = server.address().port
  	   console.log("ewe server listening at http://%s:%s", host, port)
  })
})();
