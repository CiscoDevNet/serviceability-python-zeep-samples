"""Risport70 <selectCmDevice> sample script

Dependency Installation:

    $ pip install -r requirements.txt

Copyright (c) 2018 Cisco and/or its affiliates.
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from lxml import etree
import requests
from requests import Session
from requests.auth import HTTPBasicAuth

from zeep import Client, Settings, Plugin
from zeep.transports import Transport
from zeep.exceptions import Fault
import time

import os
import sys

# Edit .env file to specify your Webex site/user details
from dotenv import load_dotenv

load_dotenv()

# Set DEBUG=True in .env to enable output of request/response headers and XML
DEBUG = os.getenv("DEBUG") == "True"

# The WSDL is a local file in the root directory, see README
WSDL_FILE = "schema/RISService70.wsdl"

# This class lets you view the incoming and outgoing http headers and XML


# This class lets you view the incoming and outgoing HTTP headers and XML
class MyLoggingPlugin(Plugin):
    def egress(self, envelope, http_headers, operation, binding_options):
        if not DEBUG:
            return

        # Format the request body as pretty printed XML
        xml = etree.tostring(envelope, pretty_print=True, encoding="unicode")

        print(f"\nRequest\n-------\nHeaders:\n{http_headers}\n\nBody:\n{xml}")

    def ingress(self, envelope, http_headers, operation):
        if not DEBUG:
            return

        # Format the response body as pretty printed XML
        xml = etree.tostring(envelope, pretty_print=True, encoding="unicode")

        print(f"\nResponse\n-------\nHeaders:\n{http_headers}\n\nBody:\n{xml}")


# The first step is to create a SOAP client session
session = Session()

# We disable certificate verification by default
session.verify = False
# Suppress the console warning about the resulting insecure requests
requests.packages.urllib3.disable_warnings(
    requests.packages.urllib3.exceptions.InsecureRequestWarning
)

# To enabled SSL cert checking (recommended for production)
# place the CUCM Tomcat cert .pem file in the root of the project
# and uncomment the two lines below

# CERT = 'changeme.pem'
# session.verify = CERT

session.auth = HTTPBasicAuth(os.getenv("CUCM_USERNAME"), os.getenv("PASSWORD"))

transport = Transport(session=session, timeout=10)

# strict=False is not always necessary, but it allows zeep to parse imperfect XML
settings = Settings(strict=False, xml_huge_tree=True)

plugin = [MyLoggingPlugin()] if DEBUG else []

client = Client(WSDL_FILE, settings=settings, transport=transport, plugins=plugin)

# Create the Zeep service binding to the Perfmon SOAP service at the specified CUCM
service = client.create_service(
    "{http://schemas.cisco.com/ast/soap}RisBinding",
    f'https://{ os.getenv( "CUCM_ADDRESS" ) }:8443/realtimeservice2/services/RISService70',
)

# Build and execute the request object

stateInfo = ""

criteria = {
    "MaxReturnedDevices": "1000",
    "DeviceClass": "Phone",
    "Model": "255",
    "Status": "Any",
    "NodeName": "",
    "SelectBy": "Name",
    "Protocol": "Any",
    "DownloadStatus": "Any",
    "SelectItems": {"item": []},
}

# One or more specific devices can be retrieved by replacing * with
# the device name in multiple items
criteria["SelectItems"]["item"].append({"Item": "*"})

# Execute the request
try:
    resp = service.selectCmDevice(stateInfo, criteria)
except Fault as err:
    print(f"Zeep error: selectCmDevice: { err }")
    sys.exit(1)

print("\nselectCmDevice response:\n")
print(resp, "\n")

for node in resp["SelectCmDeviceResult"]["CmNodes"]["item"]:
    if node["ReturnCode"] != "Ok":
        continue

    print("Node: ", node["Name"])
    print()

    print(
        "{name:16}{ip:16}{dirn:11}{status:13}{desc:16}{ts:17}".format(
            name="Name",
            ip="IP Address",
            dirn="DN",
            status="Status",
            desc="Description",
            ts="Time",
        )
    )

    print(
        "{name:16}{ip:16}{dirn:11}{status:13}{desc:16}{ts:17}".format(
            name="-" * 15,
            ip="-" * 15,
            dirn="-" * 10,
            status="-" * 12,
            desc="-" * 15,
            ts="-" * 16,
        )
    )

    for device in node["CmDevices"]["item"]:
        ipaddresses = device["IPAddress"]
        ipaddress = ipaddresses["item"][0]["IP"] if ipaddresses else ""
        description = device["Description"] if device["Description"] != None else ""
        devicename = device["Name"]
        timestamp = time.strftime("%Y/%m/%d %H:%M", time.localtime(device["TimeStamp"]))

        if device["LinesStatus"] == None:
            print(
                "{name:16}{ip:16}{dirn:11}{status:13}{desc:16}{ts:17}".format(
                    name=devicename,
                    ip=ipaddress,
                    dirn=" ",
                    status=" ",
                    desc=description,
                    ts=timestamp,
                )
            )
        else:
            for x in range(0, len(device["LinesStatus"]["item"])):
                if x == 0:
                    print(
                        "{name:16}{ip:16}{dirn:11}{status:13}{desc:16}{ts:17}".format(
                            name=devicename,
                            ip=ipaddress,
                            dirn=device["LinesStatus"]["item"][x]["DirectoryNumber"],
                            status=device["LinesStatus"]["item"][x]["Status"],
                            desc=description,
                            ts=timestamp,
                        )
                    )
                else:
                    print(
                        "{pad:32}{dirn:11}{status:13}".format(
                            pad=" ",
                            dirn=device["LinesStatus"]["item"][x]["DirectoryNumber"],
                            status=device["LinesStatus"]["item"][x]["Status"],
                        )
                    )
