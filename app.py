import os
import sys
import json
from datetime import datetime

import requests
from flask import Flask, request
from wit import Wit

app = Flask(__name__)

THRESHOLD = 0.9
access_token = "77L3MJRKODLLSTFYUCTSWRLAT66ZKQHJ"
client = Wit(access_token=access_token)
ERROR_MESSAGE = "Sorry, I didn't get what you mean. Could you repeat again?"


@app.route('/', methods=['GET'])
def verify():
    # when the endpoint is registered as a webhook, it must echo back
    # the 'hub.challenge' value it receives in the query arguments
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == os.environ["VERIFY_TOKEN"]:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200

    return "Hello world, beachesss", 200


@app.route('/', methods=['POST'])
def webhook():
    # endpoint for processing incoming messaging events
    # ***********WIT AI TOKEN TO USE APP**************

    data = request.get_json()
    log(data)  # you may not want to log every incoming message in production, but it's good for testing
    try:
        if data["object"] == "page":

            for entry in data["entry"]:
                for messaging_event in entry["messaging"]:

                    # **********************************DONT REMOVE**********************************************************************************
                    if messaging_event.get("message"):  # someone sent us a message

                        sender_id = messaging_event["sender"]["id"]  # the facebook ID of the person sending you the message
                        recipient_id = messaging_event["recipient"]["id"]  # the recipient's ID, which should be your page's facebook ID
                        message_text = messaging_event["message"]["text"]  # the message's text
                    # **********************************DONT REMOVE**********************************************************************************

                        response = wit_response(message_text)

                        entity = response[0]
                        value = response[1]

                        if entity == 'insult':
                            send_message(sender_id,
                                         "Sorry, please do not hurl any vulgarities at me. I am too cute to be abused!")
                        elif entity == 'greeting':
                            send_message(sender_id, "Hi! Whatzzup! I am your friendly property noob!")
                        elif entity == 'property':
                            send_message(sender_id, "So you are looking for " + value)
                            send_message(sender_id,
                                         "Give me a moment. I will find out the prices of " + value + " in Singapore")
                        elif entity == 'location':
                            send_message(sender_id, "So you are looking for apartments in " + value)
                            send_message(sender_id, "Give me a moment. I will find out all the prices in " + value)
                        elif entity == None:
                            send_message(sender_id, "I don't understand you.")


                        # send_message(sender_id, "resp is: " + str(resp))

                    if messaging_event.get("delivery"):  # delivery confirmation
                        pass

                    if messaging_event.get("optin"):  # optin confirmation
                        pass

                    if messaging_event.get("postback"):  # user clicked/tapped "postback" button in earlier message
                        pass
    except:
        send_message("383819208755566", "sorry no reply!")
    return "ok", 200


def wit_response(message_text):
    resp = client.message(message_text)
    entity = None
    value = None
    try:
        entity = list(resp['entities'])[0]
        value = resp['entities'][entity][0]['value']
    except:
        pass
    return (entity, value)


def check_property_price(entities):
    property_type = entities["property_type"][0]["value"] if "property_type" in entities else None
    property_number_room = entities["property_number_room"][0]["value"] if "property_number_room" in entities else None
    location = entities["location"][0]["value"] if "location" in entities else None

    result = property_type

    if property_number_room is not None:
        result = property_number_room + " " + result

    result = result + " at " + location + " cost $99999999"

    return result


def send_message(recipient_id, message_text):
    log("sending message to {recipient}: {text}".format(recipient=recipient_id, text=message_text))

    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "text": message_text
        }
    })
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)


def log(msg, *args, **kwargs):  # simple wrapper for logging to stdout on heroku
    try:
        if type(msg) is dict:
            msg = json.dumps(msg)
        else:
            msg = unicode(msg).format(*args, **kwargs)
        print u"{}: {}".format(datetime.now(), msg)
    except UnicodeEncodeError:
        pass  # squash logging errors in case of non-ascii text
    sys.stdout.flush()


if __name__ == '__main__':
    app.run(debug=True)
