import time
import json
import os
import sys

from dxlbootstrap.util import MessageUtils
from dxlclient.client_config import DxlClientConfig
from dxlclient.client import DxlClient
from dxlclient.message import Event, Request, Message

# Import common logging and configuration
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/..")
from common import *

# Configure local logger
logging.getLogger().setLevel(logging.ERROR)
logger = logging.getLogger(__name__)

SERVICE_UNIQUE_ID = "test"

DOCUMENT_INDEX = "test_index"
DOCUMENT_TYPE = "test_doc"
DOCUMENT_ID = "12345"
EVENT_TOPIC = "/sample/elasticsearch/basicevent"
ELASTICSEARCH_API_TOPIC = "/opendxl-elasticsearch/service/elasticsearch-api"

# Create DXL configuration from file
config = DxlClientConfig.create_dxl_config_from_file(CONFIG_FILE)

# Create the client
with DxlClient(config) as client:

    # Connect to the fabric
    client.connect()

    logger.info("Connected to DXL fabric.")

    # Create the event
    event = Event(EVENT_TOPIC)

    # Set the payload
    event.payload = json.dumps({
        "event_id": DOCUMENT_ID,
        "message": "Hello from OpenDXL",
        "source": "Basic Event Example"}).encode(encoding="utf-8")

    # Send the event
    client.send_event(event)

    # Create the get request
    request_topic = "{}/{}/get".format(
        ELASTICSEARCH_API_TOPIC, SERVICE_UNIQUE_ID)
    req = Request(request_topic)

    # Set the payload for the get request
    req.payload = json.dumps({
        "index": DOCUMENT_INDEX,
        "doc_type": DOCUMENT_TYPE,
        "id": DOCUMENT_ID}).encode(encoding="utf-8")

    print("Waiting for event payload to be stored in Elasticsearch...")

    tries_remaining = 5
    # Send up to 5 requests to the elasticsearch DXL service to try to
    # retrieve the document that should be stored for the event.
    res = client.sync_request(req, timeout=30)
    while res.message_type == Message.MESSAGE_TYPE_ERROR and tries_remaining:
        tries_remaining -= 1
        time.sleep(2)
        res = client.sync_request(req, timeout=30)

    if res.message_type != Message.MESSAGE_TYPE_ERROR:
        # Display results for the get request
        res_dict = MessageUtils.json_payload_to_dict(res)
        print("Response to the get request:\n{}".format(
            MessageUtils.dict_to_json(res_dict, pretty_print=True)))
    else:
        print("Error invoking service with topic '{}': {} ({})".format(
            request_topic, res.error_message,
            res.error_code))
        if res.payload:
            # Display the payload in the error response
            res_dict = MessageUtils.json_payload_to_dict(res)
            print("Error payload:\n{}".format(
                MessageUtils.dict_to_json(res_dict, pretty_print=True)))
