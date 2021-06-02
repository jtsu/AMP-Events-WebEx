import time
import requests
import json
from webexteamssdk import WebexTeamsAPI
import config


# https://webexteamssdk.readthedocs.io/en/latest/index.html
api = WebexTeamsAPI()


# Function to get AMP events
def getEvents():

    request = requests.get(config.amp_url, auth=(
        config.amp_client_id, config.amp_api_key))

    return(request.json())


# Create a webex room
def webexCreateRoom(roomName):
    return (api.rooms.create(roomName))


# delete webex room
def webexDeleteRoom(roomName):
    all_rooms = api.rooms.list()
    demo_rooms = [room for room in all_rooms if roomName in room.title]

    # Delete all of the demo rooms
    for room in demo_rooms:
        api.rooms.delete(room.id)
        print("Room '{}' deleted.".format(room.id))

# Add user to webex room
def webexAddUsers(email, id):
    api.memberships.create(id, personEmail=email)


#check if webex room exists
def webexRoomExist(roomName):
    all_rooms = api.rooms.list()
    existing_rooms = [room for room in all_rooms if roomName in room.title]
    return (existing_rooms)

# Save message to file for testing
def saveEvents(filename, message):

    saveFile = filename +".cfg"
    with open(saveFile, "w") as f:
        f.write(json.dumps(message, indent=4))
        print(saveFile + ": Successfully written.")


def scanEvents():
    message = []

    for d in getEvents()["data"]:
        if "event_type" in d.keys():
            if d["event_type"] == "Scan Completed, No Detections":
                message.append(d['event_type'])
                message.append(d['computer']['hostname'])
                message.append(d['date'])
                message.append(d['timestamp'])
                message.append(d["scan"])
        else:
            continue
    return(message)


def vulnEvents():
    targetScore = 10
    message = []

    for d in getEvents()["data"]:
        if "event_type" in d.keys():
            if d["event_type"] == "Vulnerable Application Detected":
                message.append(d['event_type'])

                if "vulnerabilities" in d.keys():
                    for i in d["vulnerabilities"]:
                        s = float(i['score'])

                        if s >= targetScore:
                            message.append("[" + str(i['cve']) + "](" + str(i['url']) + "): Score = " + str(i['score']) +"<br/>")
                else:
                    continue
        else:
            continue
    return(message)



if __name__ == '__main__':

    roomName = 'AMP_Testing-UNC'
    email = 'jtsu@cisco.com'

    if webexRoomExist(roomName):
        print("Found {} existing room(s)."
          "".format(len(webexRoomExist(roomName))))
        for room in webexRoomExist(roomName):
            demo_room = room
            print (room.id)
    else:
        demo_room = webexCreateRoom(roomName)
        webexAddUsers(email, demo_room.id)
    

    #####  Save All Events to local file  #####
    #saveEvents("savedAll", getEvents())


    #####  Get filtered CVE related events  #####
    vulnMsgs = vulnEvents()
    # print (len(vulnMsgs))

    # If dataset is too large, webex will not post the message correctly.
    # So following is to split the list, each sub-list of size n elements

    # How many elements each list should have
    n = 25

    splitVulnMsgs = [vulnMsgs[i:i + n] for i in range(0, len(vulnMsgs), n)]
    

    # Post CVE list to WebEx Room
    for i in splitVulnMsgs:
        msgPost = json.dumps(''.join(map(str, i)))
        time.sleep(3)
        api.messages.create(demo_room.id, markdown=json.dumps(msgPost))


    # Post Client Scan Details to WebEx Room
    api.messages.create(demo_room.id, markdown=json.dumps(scanEvents()))