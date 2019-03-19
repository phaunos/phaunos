from flask import jsonify


def build_response(messages, extra_data={}):
    if not isinstance(messages, list):
        messages = [messages]
    data = {'messages': messages}
    for k, v in extra_data.items():
        data[k] = v
    return jsonify(data)
