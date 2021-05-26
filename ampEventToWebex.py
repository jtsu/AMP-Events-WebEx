import requests
import json
import config


# Function to get AMP events
def getEvents():

    request = requests.get(config.amp_url, auth=(
        config.amp_client_id, config.amp_api_key))

    return(request.json())



    


# Function for posting a message to a WebEx space using incoming webhooks.
# The webhooks url is defined in config.py
def post(message):

    response = requests.post(config.url,
                             headers={"Content-Type": "application/json"},
                             data=json.dumps({"markdown": message}),
                             verify=True)

    if response.status_code == 200 or response.status_code == 204:
        print("Successfully posted to WebEx.")
        print("  Status Code: %d" % response.status_code)
    else:
        print("Failed to post to WebEx.")
        print("  Status Code: %d" % response.status_code)


# Function to save message to file
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


    #####  Save All Events to local file  #####
    #saveEvents("savedAll", getEvents())


    #####  Get filtered CVE related events  #####
    vulnMsgs = vulnEvents()
    print (len(vulnMsgs))

    # If dataset is too large, webex will not post the message correctly.
    # So following is to split the list, each sub-list of size n elements

    # How many elements each list should have
    n = 25
    
    splitVulnMsgs = [vulnMsgs[i:i + n] for i in range(0, len(vulnMsgs), n)]

    #post CVE list to webex 
    for i in splitVulnMsgs:
        msgPost = json.dumps(''.join(map(str, i)))

        #print (msgPost)
        post(msgPost)
        
        
    #####  post Scan Details  ######
    post (json.dumps(scanEvents(),indent=4))
    
    
    
    
