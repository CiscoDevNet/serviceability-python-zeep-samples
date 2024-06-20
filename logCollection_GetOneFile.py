"""Serviceability Log Collection Service sample script

Performs a <selectLogFiles> to get a listing of log files available for a
specific service (Cisco Audit Logs), retrieves the contents of the latest file
using <GetOneFile>, then parses/prints a few lines of the results.

Dependency Installation:

    $ pip3 install -r requirements.txt

Copyright (c) 2024 Cisco and/or its affiliates.
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

import copy
from lxml import etree
import requests
from requests import Session
from requests.auth import HTTPBasicAuth

from zeep import Client, Settings, Plugin
from zeep.transports import Transport
from zeep.exceptions import Fault

import os
import sys

# Edit .env file to specify your Webex site/user details
from dotenv import load_dotenv

load_dotenv()

# Set DEBUG=True in .env to enable output of request/response headers and XML
DEBUG = os.getenv("DEBUG") == "True"

# The WSDL is a local file in the working directory, see README
WSDL_FILE = "schema/LogCollectionPortTypeService.wsdl"

# This class lets you view the incoming and outgoing HTTP headers and XML


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

        # Modify the plugin to selectively remove large binary file content
        # from GetOneFile response
        if envelope.find("./{*}Body/{*}GetOneFileReturn") is not None:
            display_xml = copy.deepcopy(envelope)
            display_xml.find(
                "./{*}Body/{*}GetOneFileReturn"
            ).text = "REMOVED_FOR_BREVITY"
            # Format the response body as pretty printed XML
            xml_string = etree.tostring(
                display_xml, pretty_print=True, encoding="unicode"
            )
        else:
            # Format the response body as pretty printed XML
            xml_string = etree.tostring(envelope, pretty_print=True, encoding="unicode")

        print(f"\nResponse\n-------\nHeaders:\n{http_headers}\n\nBody:\n{xml_string}")


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
print(os.getenv("CUCM_USERNAME"), os.getenv("PASSWORD"))
transport = Transport(session=session, timeout=10)

# strict=False is not always necessary, but it allows zeep to parse imperfect XML
settings = Settings(strict=False, xml_huge_tree=True)

# If debug output is requested, add the MyLoggingPlugin class
plugin = [MyLoggingPlugin()] if DEBUG else []

# Create the Zeep client with the specified settings
client = Client(WSDL_FILE, settings=settings, transport=transport, plugins=plugin)

# Create the Zeep service binding to the Log Collection SOAP service at the specified CUCM
service = client.create_service(
    "{http://schemas.cisco.com/ast/soap}LogCollectionPortSoapBinding",
    f'https://{ os.getenv( "CUCM_ADDRESS" ) }:8443/logcollectionservice2/services/LogCollectionPortTypeService',
)

# Get a listing of all available log files for the 'Cisco Audit Logs' service
# Note: All the below fields must appear, but onsome some require data, depending on
#     the desired functionality
try:
    resp = service.selectLogFiles(
        FileSelectionCriteria={
            "ServiceLogs": ["Cisco Audit Logs"],
            "SystemLogs": [],
            "SearchStr": "",
            "Frequency": "OnDemand",
            "JobType": "DownloadtoClient",
            "ToDate": "",
            "FromDate": "",
            "TimeZone": "",
            "RelText": "None",
            "RelTime": 0,
            "Port": "",
            "IPAddress": "",
            "UserName": "",
            "Password": "",
            "ZipInfo": False,
            "RemoteFolder": "",
        }
    )
except Fault as err:
    print(f"Zeep error: selectLogFiles: { err }")
    sys.exit(1)

print("\nselectLogFiles response:\n")
print(resp, "\n")

input("Press Enter to continue...")

# Create a simple report of the XML response
print("\nAvailable log files:\n")

# Print the name/size/date, padding/truncating the name to 20 characters
print(f'Filename{ 31 * " " } Size{ 6 * " " } Date{ 24 * " " }')
print(f'{ 39 * "-" } { 10 * "-" } { 28 * "-" }')

if len(resp.Node.ServiceList.ServiceLogs[0].SetOfFiles.File) == 0:
    print("\nNo matching files found...")
    sys.exit(0)

lastFileName = None
lastFilePath = None

# Loop through and print the returned files list
for logFile in resp.Node.ServiceList.ServiceLogs[0].SetOfFiles.File:
    print(
        f'{ logFile.name.ljust( 39, " ") } {logFile.filesize.ljust( 10, " " ) } {logFile.modifiedDate.ljust( 28, " ") }'
    )

    lastFileName = logFile.name
    lastFilePath = logFile.absolutepath

input("\nPress Enter to continue...")

# Retrieve the latest (or, at least the last) log file via DIME
try:
    resp = service.GetOneFile(lastFilePath)
except Fault as err:
    print(f"Zeep error: GetOneFile: { err }")
    sys.exit(1)

print("\nGetOneFile: success\n")

# The output will be bytes - convert to UTF-8 string
fileOutput = resp.decode("utf-8")
# Null out the resp variable in case it was taking up a large amount of memory
resp = None

print(f"File contents (first 10 lines...) of [ { lastFileName } ]:\n")

# Split contents into an array of separate strings for printing out
for line in fileOutput.splitlines()[:10]:
    print(line)
