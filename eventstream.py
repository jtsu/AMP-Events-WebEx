import json

import pika
import requests
import ssl
import config

def _post_stream(event_name):
	data = {
			"name": event_name
	}
	
	r = requests.post(
			url="https://api.amp.cisco.com/v1/event_streams",
			data=data,
			auth=(config.amp_client_id, config.amp_api_key)
	)
	if r.status_code == 201:
		j = json.loads(r.content)
		amqp_info = {
				"user_name": j["data"]["amqp_credentials"]["user_name"],
				"password": j["data"]["amqp_credentials"]["password"],
				"queue_name":  j["data"]["amqp_credentials"]["queue_name"],
				"host": j["data"]["amqp_credentials"]["host"],
				"port": j["data"]["amqp_credentials"]["port"],
				"proto": j["data"]["amqp_credentials"]["proto"]
		}
		return amqp_info
	elif r.status_code == 400:
		return 400
	else:
		return False
def _del_stream(stream_id):
	r = requests.delete(
			url=f"https://api.amp.cisco.com/v1/event_streams/{stream_id}",
			auth=(config.amp_client_id, config.amp_api_key)
	)
	if r.status_code == 200 or r.status_code == 201:
		return True
	else:
		return False
def create_stream():
	event_name = "Real Time Stream"
	amqp_info = _post_stream(event_name)
	if amqp_info is not False and amqp_info != 400:
		return amqp_info
	elif amqp_info == 400:
		r = requests.get(
				url="https://api.amp.cisco.com/v1/event_streams",
				auth=(config.amp_client_id, config.amp_api_key)
		)
		if r.status_code == 200:
			streams = json.loads(r.content)
			for stream in streams['data']:
				if stream['name'] == event_name:
					if _del_stream(stream['id']):
						amqp_info = _post_stream(event_name)
						return  amqp_info
			return False
		else:
			return False
		
	else:
		return False
	
def callback(channel,method, proterties, body):
	print(body)
	
def start_stream(amqp_info):
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
	
	channel.basic_consume(
			amqp_info['queue_name'],
			callback,
			auto_ack=False
	)
	
	return channel

