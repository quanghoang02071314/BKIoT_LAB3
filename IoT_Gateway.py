import geocoder # Using geocoder library to get the coordinate of the device base on IP
import json
import paho.mqtt.client as mqttclient
import serial
import time

# import serial.tools.list_ports as ports
# com_ports = list(ports.comports())  # create a list of com ['COM1','COM2']
# for i in com_ports:
#     print(i.device)

print("IoT Gateway")

BROKER_ADDRESS = "demo.thingsboard.io"
PORT = 1883
THINGS_BOARD_ACCESS_TOKEN = "itjJFJLDL8IUieSfuAB8"

ledStatus = False
fanStatus = False
mess = ""
bbc_port = "/dev/cu.usbmodem14102" #/dev/cu.usbmodem14102

if len(bbc_port) > 0:
    ser = serial.Serial(port=bbc_port, baudrate=115200)


def processData(data):
    global ledStatus, fanStatus
    
    data = data.replace("!", "")
    data = data.replace("#", "")
    splitData = data.split(":")
    print(splitData)
    #TODO: Add your source code to publish data to the server
    data = {splitData[1]:splitData[2]}

    if splitData[1] == 'ledValue' or splitData[1] == 'fanValue':
        if splitData[1] == 'ledValue':
            ledStatus = not ledStatus
        else:
            fanStatus = not fanStatus
        sendCmd() # Update the cmd to control 2 devices
        client.publish('v1/devices/me/attributes', json.dumps(data), 1)
    else:
        client.publish('v1/devices/me/telemetry', json.dumps(data), 1)



def readSerial():
    bytesToRead = ser.inWaiting()
    if (bytesToRead > 0):
        global mess
        mess = mess + ser.read(bytesToRead).decode("UTF-8")
        while ("#" in mess) and ("!" in mess):
            start = mess.find("!")
            end = mess.find("#")
            processData(mess[start:end + 1])
            if (end == len(mess)):
                mess = ""
            else:
                mess = mess[end+1:]


def subscribed(client, userdata, mid, granted_qos):
    print("Subscribed...")


def sendCmd():
    global ledStatus, fanStatus
    cmd = 0

    if not ledStatus and not fanStatus:
        cmd = 0
    elif ledStatus and not fanStatus:
        cmd = 1
    elif not ledStatus and fanStatus:
        cmd = 2
    elif ledStatus and fanStatus:
        cmd = 3

    if len(bbc_port) > 0:
        ser.write((str(cmd) + "#").encode())


def recv_message(client, userdata, message):
    temp_data = {'value': True}
    global ledStatus, fanStatus

    print("Received: ", message.payload.decode("utf-8"))
    
    try:
        jsonobj = json.loads(message.payload)
        if jsonobj['method'] == "setLED":
            temp_data['value'] = jsonobj['params']
            client.publish('v1/devices/me/attributes', json.dumps(temp_data), 1)
            ledStatus = temp_data['value']
        elif jsonobj['method'] == "setFAN":
            temp_data['value'] = jsonobj['params']
            client.publish('v1/devices/me/attributes', json.dumps(temp_data), 1)
            fanStatus = temp_data['value']
    except:
        pass

    # Update the cmd to control 2 devices
    sendCmd()


def connected(client, usedata, flags, rc):
    if rc == 0:
        print("Thingsboard connected successfully!!")
        client.subscribe("v1/devices/me/rpc/request/+")
        return True
    else:
        print("Connection is failed")
        return False


client = mqttclient.Client("Gateway_Thingsboard")
client.username_pw_set(THINGS_BOARD_ACCESS_TOKEN)

client.on_connect = connected
client.connect(BROKER_ADDRESS, 1883)
client.loop_start()

client.on_subscribe = subscribed
client.on_message = recv_message

counter = 0
latitude = 0
longitude = 0

while True:
    counter = counter + 1
    if counter == 10:
        counter = 0
        collect_data = {
            'longitude': longitude,
            'latitude': latitude
        }
        
        g = geocoder.ip('me') # Return a list [<latitude>, <longtitude>] base on IP of this pic
        latitude = g.latlng[0]
        longitude = g.latlng[1]

        client.publish('v1/devices/me/telemetry', json.dumps(collect_data), 1)

    if len(bbc_port) > 0:
        readSerial()
        
    time.sleep(1)