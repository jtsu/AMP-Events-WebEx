import requests
import json
import config
from eventstream import start_stream, create_stream


if __name__ == '__main__':


    print  ("Verify Stream")
    request = requests.get(config.amp_stream_url, auth=(config.amp_client_id, config.amp_api_key))
    print (json.dumps(request.json(),indent=4))

    amqp_info = create_stream()

    if amqp_info is not False:
        if amqp_info == 400:
            amqp_info = create_stream()

        print ("Setting up the event stream and creating the event channel.")
        amqp_channel = start_stream(amqp_info)
        # Starting the event channel the system will now wait and act like a service and wait
        # for new messages to come in and proccess the messages

        try:
            print ("Start consuming stream.")
            amqp_channel.start_consuming()
        except KeyboardInterrupt:
            print ("Stop consuming stream.")
            amqp_channel.stop_consuming()
