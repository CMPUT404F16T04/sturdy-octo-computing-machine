import requests
import json
from socknet.serializers import *

def send_friend_request(node, author_data, friend_data):
    """
    Builds a friend request for sending to another node.
    """
    url = "%s/friendrequest" % node.url # I am not accounting for groups who may append with /api/ here.... maybe
                                        # we can add a flag to the Node model if needed to signal /api/ should be in url?
    data = {
                "query": "friendrequest",
                "author": author_data, # This is from the data in the original request
                "friend": friend_data
            }
    json_data = json.dumps(data) # encode
    return requests.post(url=url, headers={"content-type": "application/json"}, data=json_data)
