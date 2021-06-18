import json
import pika
import requests
import ssl
import config
from webexteamssdk import WebexTeamsAPI


def _post_stream(event_name: str):
    """
	Creates event stream in AMP Read/Write API key is needed,
	If Event Stream is already created then this function is not needed
	:param event_name(str): Name of event stream to create
	:return: Dict of streams information to create stream channel,  if stream cannot be create system will return 400 code
	"""
    data = {"name": event_name}

    r = requests.post(url="https://api.amp.cisco.com/v1/event_streams",
                      data=data,
                      auth=(config.amp_client_id, config.amp_api_key))
    if r.status_code == 201:
        j = json.loads(r.content)
        # amqp_info = {
        #		"user_name" : ["user_name"],
        #		"password"  : j["data"]["amqp_credentials"]["password"],
        #		"queue_name": j["data"]["amqp_credentials"]["queue_name"],
        #		"host"      : j["data"]["amqp_credentials"]["host"],
        #		"port"      : j["data"]["amqp_credentials"]["port"],
        #		"proto"     : j["data"]["amqp_credentials"]["proto"]
        # }
        return j["data"]["amqp_credentials"]
    elif r.status_code == 400:
        return 400
    else:
        return False


def _del_stream(stream_id: str):
    """
	Deletes Stream from AMP
	:param stream_id: Stream ID to be removed
	:return: True if deleted, false if delete failed
	"""
    r = requests.delete(
        url=f"https://api.amp.cisco.com/v1/event_streams/{stream_id}",
        auth=(config.amp_client_id, config.amp_api_key))
    if r.status_code == 200 or r.status_code == 201:
        return True
    else:
        return False


def create_stream():
    """
		Creates event stream need to set this up to read a JSON file for the stream and only create a new stream if one does not exits
		If stream exisits today the code will dele the stream and recreate a new stream with the same name the if you get an erro running the script re run and it will work
	:return:
	"""
    event_name = "Test Stream2"
    amqp_info = _post_stream(event_name)
    if amqp_info is not False and amqp_info != 400:
        return amqp_info
    elif amqp_info == 400:
        r = requests.get(url="https://api.amp.cisco.com/v1/event_streams",
                         auth=(config.amp_client_id, config.amp_api_key))
        if r.status_code == 200:
            streams = json.loads(r.content)
            for stream in streams['data']:
                if stream['name'] == event_name:
                    if _del_stream(stream['id']):
                        amqp_info = _post_stream(event_name)
                        return amqp_info
            return False
        else:
            return False

    else:
        return False


def process(data):
    """
    Function to filter the data for the specific event types in our list.
    List of  event types can be found here:
      https://api-docs.amp.cisco.com/api_actions/details?api_action=GET+%2Fv1%2Fevent_types&api_host=api.apjc.amp.cisco.com&api_resource=Event+Type&api_version=v1
    """
    filter = {
        "filter": ["Scan Started", "Scan Completed, No Detections", \
        "Scan Completed With Detections", "Scan Failed", "Vulnerable Application Detected"]
        }

    if data["event_type"] in filter["filter"]:
        if data["event_type"] == "Vulnerable Application Detected":
            if data["vulnerabilities"]["score"] >= 10:
                return {
                       "event_type": data["event_type"],
                       "cve": data["vulnerabilities"]["cve"],
                       "score": data["vulnerabilities"]["score"],
                       "url": data["vulnerabilities"]["url"]
                }
        else:
            return {
                   "event_type": data["event_type"],
                   "computer_name": data["computer"]["hostname"]
            }


def callback(channel, method, proterties, body):
    """
	Function is called when a new event is received from the event stream
	Currently the function will print the message to the screen this is where the message can be
	forward to the Webex teams proccessor function to send the message or open a service now ticket
	:param channel:
	:param method:
	:param proterties:
	:param body:Body of the message in Byte JSON Format
	:return:
	"""

    # Convert the data from Byte format to Dict
    json_data = json.loads(body)

    # run the data through the filters
    dataset  = process(json_data)


    # Using the Webex SDK. More info can be found here: https://webexteamssdk.readthedocs.io/en/latest/index.html
    webex = WebexTeamsAPI()

    # Post the filtered dataset to the webex room
    webex.messages.create(config.webex_room_id, markdown=json.dumps(dataset))
    print(dataset)
    print('- ' * 30)


def start_stream(amqp_info):
    """
	sets up evebt stream to be called
	:param amqp_info: DiCT of event stream information
	:return: Channel Object
	"""
    amqp_url = f"amqps://{amqp_info['user_name']}:{amqp_info['password']}@{amqp_info['host']}:{amqp_info['port']}"
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    amqp_ssl = pika.SSLOptions(context)
    credentials = pika.PlainCredentials(amqp_info['user_name'],
                                        amqp_info['password'])
    params = pika.ConnectionParameters(host=amqp_info['host'],
                                       port=amqp_info['port'],
                                       credentials=credentials,
                                       ssl_options=amqp_ssl)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    #setting up the event channel with the amqp queue name and the function that ill be called
    #when a new message arrives
    channel.basic_consume(amqp_info['queue_name'], callback, auto_ack=False)

    return channel
