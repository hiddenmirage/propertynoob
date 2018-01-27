import os
import sys
import json
from datetime import datetime

import requests
from flask import Flask, request

app = Flask(__name__)

THRESHOLD = 0.9


@app.route('/', methods=['GET'])
def verify():
    # when the endpoint is registered as a webhook, it must echo back
    # the 'hub.challenge' value it receives in the query arguments
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == os.environ["VERIFY_TOKEN"]:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200

    return "Hello world, beachesss", 200


value_property_button = {
    "content_type": "text",
    "title": "Value A Property",
    "payload": "start_property_valuation"
}
joke_button = {
    "content_type": "text",
    "title": "Tell a joke",
    "payload": "tell_joke"
}
location_button = {
    "content_type": "location"
}

default_quick_replies_buttons = [
    value_property_button,
    joke_button,
    location_button
]


@app.route('/', methods=['POST'])
def webhook():
    # endpoint for processing incoming messaging events

    data = request.get_json()
    log(data)  # you may not want to log every incoming message in production, but it's good for testing

    if data["object"] == "page":

        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:

                if messaging_event.get("message"):  # someone sent us a message

                    sender_id = messaging_event["sender"]["id"]  # the facebook ID of the person sending you the message
                    recipient_id = messaging_event["recipient"][
                        "id"]  # the recipient's ID, which should be your page's facebook ID
                    message_text = messaging_event["message"]["text"]  # the message's text

                    if "attachments" in messaging_event["message"]:  # received attachments
                        send_message(sender_id, "Can't read attachments yet. pai seh ah.")

                    if "quick_reply" in messaging_event["message"]:
                        if messaging_event["message"]["quick_reply"]["payload"] == "start_property_valuation":
                            send_message(sender_id, "Ok. Tell me where", [location_button])

                        elif messaging_event["message"]["quick_reply"]["payload"] == "tell_joke":
                            send_message(sender_id, "Bob is Alice's best friend. hahaha..")

                    elif "nlp" in messaging_event["message"]:
                        entities = messaging_event["message"]["nlp"]["entities"]

                        if "property_type" in entities and entities["property_type"][0][
                            "confidence"] >= THRESHOLD and \
                                "location" in entities and entities["location"][0]["confidence"] >= THRESHOLD:
                            result = check_property_price(entities)
                            send_message(sender_id, result)

                        if "insult" in entities and entities["insult"][0]["confidence"] >= THRESHOLD:
                            send_message(sender_id, "Don't be so rude can?")

                        if "greetings" in entities and entities["greetings"][0]["confidence"] >= THRESHOLD:
                            send_message(sender_id, "Hello.. What do you want to do?")

                    # send_message(sender_id, "roger that!")
                    # send_message(sender_id, "message text is: " + message_text)

                if messaging_event.get("delivery"):  # delivery confirmation
                    pass

                if messaging_event.get("optin"):  # optin confirmation
                    pass

                if messaging_event.get("postback"):  # user clicked/tapped "postback" button in earlier message
                    pass

    return "ok", 200


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
