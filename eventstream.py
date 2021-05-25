import json
import pika
import requests
import ssl
import config

def create_stream():
	data = {
			"name"      : "Real Time Stream"
	}
	r = requests.post(
			url=config.amp_url,
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
		return  amqp_info
	else:
		return False
	
def callback(channel,method, proterties, body):
	print(body)
	
def start_stream(amqp_info):
	amqp_url = f"amqps://{amqp_info['user_name']}:{amqp_info['password']}@{amqp_info['host']}:{amqp_info['port']}"
	context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
	amqp_ssl = pika.SSLOptions(context)
	params = pika.URLParameters(amqp_url)
	params.ssl_options = amqp_ssl
	connection = pika.BlockingConnection(params)
	channel = connection.channel()
	
	channel.basic_consume(
			amqp_info['queue_name'],
			callback,
			auto_ack=False
	)
	
	return channel
	
