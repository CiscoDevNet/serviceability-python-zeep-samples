"""Serviceability Control Center Services <getServiceStatus> sample script

Performs a <soapGetServiceStatus> request using the Zeep SOAP library, and 
parses/prints the results in a simple table output.

Copyright (c) 2021 Cisco and/or its affiliates.
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

import os
import sys

# Edit .env file to specify your Webex site/user details
from dotenv import load_dotenv
load_dotenv()

# Set DEBUG=True in .env to enable output of request/response headers and XML
DEBUG = os.getenv( 'DEBUG' ) == 'True'


# The WSDL is a local file in the working directory, see README
WSDL_FILE = 'schema/ControlCenterServices.wsdl'

# This class lets you view the incoming and outgoing HTTP headers and XML

# This class lets you view the incoming and outgoing HTTP headers and XML
class MyLoggingPlugin( Plugin ):

    def egress( self, envelope, http_headers, operation, binding_options ):

        if not DEBUG: return

        # Format the request body as pretty printed XML
        xml = etree.tostring( envelope, pretty_print = True, encoding = 'unicode')

        print( f'\nRequest\n-------\nHeaders:\n{http_headers}\n\nBody:\n{xml}' )

    def ingress( self, envelope, http_headers, operation ):

        if not DEBUG: return

        # Format the response body as pretty printed XML
        xml = etree.tostring( envelope, pretty_print = True, encoding = 'unicode')

        print( f'\nResponse\n-------\nHeaders:\n{http_headers}\n\nBody:\n{xml}' )

# The first step is to create a SOAP client session

session = Session()

# We disable certificate verification by default
session.verify = False
# Suppress the console warning about the resulting insecure requests
requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

# To enabled SSL cert checking (recommended for production)
# place the CUCM Tomcat cert .pem file in the root of the project
# and uncomment the two lines below

# CERT = 'changeme.pem'
# session.verify = CERT

session.auth = HTTPBasicAuth( os.getenv( 'USERNAME' ), os.getenv( 'PASSWORD' ) )

transport = Transport( session = session, timeout = 10 )

# strict=False is not always necessary, but it allows zeep to parse imperfect XML
settings = Settings( strict = False, xml_huge_tree = True )

# If debug output is requested, add the MyLoggingPlugin class
plugin = [ MyLoggingPlugin() ] if DEBUG else [ ]

# Create the Zeep client with the specified settings
client = Client( WSDL_FILE, settings = settings, transport = transport, plugins = plugin )

# Create the Zeep service binding to the Perfmon SOAP service at the specified CUCM
service = client.create_service(
    '{http://schemas.cisco.com/ast/soap}ControlCenterServicesBinding',
    f'https://{ os.getenv( "CUCM_ADDRESS" ) }:8443/controlcenterservice2/services/ControlCenterServices' 
    )

# Execute the request
try:
	resp = service.soapGetServiceStatus( '' )
except Fault as err:
    print( f'Zeep error: soapGetServiceStatus: { err }' )
    sys.exit( 1 )

print( "\nsoapGetServiceStatus response:\n" )
print( resp,"\n" )

input( 'Press Enter to continue...' )

# Create a simple report of the XML response
print( '\nService Status' )
print( ( '=' * 57 ) + '\n' )

# Loop through the top-level of the response object
for item in resp.ServiceInfoList.item:

    # Print the name and version, padding/truncating the name to 49 characters
    print( '{:50.50}'.format( item.ServiceName ) + item.ServiceStatus )



