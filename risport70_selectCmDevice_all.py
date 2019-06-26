"""Risport70 <selectCmDevice> sample script, using the Zeep SOAP library

Install Python 2.7 or 3.7
On Windows, choose the option to add to PATH environment variable

If this is a fresh installation, update pip (you may need to use `pip3` on Linux or Mac)

    $ python -m pip install --upgrade pip

Script Dependencies:
    lxml
    requests
    zeep

Dependency Installation:

    $ pip install zeep

This will install automatically all of zeep dependencies, including lxml, requests

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
from requests import Session
from requests.auth import HTTPBasicAuth

from zeep import Client, Settings, Plugin
from zeep.transports import Transport
from zeep.exceptions import Fault

# Configure CUCM location and user credentials in creds.py
import creds

# Change to true to enable output of request/response headers and XML
DEBUG = False

# The WSDL is a local file in the root directory, see README
WSDL_FILE = 'RISService70.wsdl'

# This class lets you view the incoming and outgoing http headers and XML

class MyLoggingPlugin(Plugin):

    def egress(self, envelope, http_headers, operation, binding_options):
        print(
'''Request
-------
Headers:
{headers}

Body:
{xml}

'''.format( headers = http_headers, 
            xml = etree.tostring( envelope, pretty_print = True, encoding = 'unicode') )
        )

    def ingress( self, envelope, http_headers, operation ):
        print('\n')
        print(
'''Response
-------
Headers:
{headers}

Body:
{xml}

'''.format( headers = http_headers, 
            xml = etree.tostring( envelope, pretty_print = True, encoding = 'unicode') )
        )

# The first step is to create a SOAP client session

session = Session()

# We avoid certificate verification by default

session.verify = False

# To enabled SSL cert checking (recommended for production)
# place the CUCM Tomcat cert .pem file in the root of the project
# and uncomment the two lines below

# CERT = 'changeme.pem'
# session.verify = CERT

session.auth = HTTPBasicAuth(creds.USERNAME, creds.PASSWORD)

transport = Transport( session = session, timeout = 10 )

# strict=False is not always necessary, but it allows zeep to parse imperfect XML
settings = Settings( strict = False, xml_huge_tree = True )

plugin = [ MyLoggingPlugin() ] if DEBUG else [ ]

client = Client( WSDL_FILE, settings = settings, transport = transport, plugins = plugin )

service = client.create_service( '{http://schemas.cisco.com/ast/soap}RisBinding',
    'https://{cucm}:8443/realtimeservice2/services/RISService70'.format( cucm = creds.CUCM_ADDRESS ))

# Build and execute the request

stateInfo = ''  

criteria = {  
    'MaxReturnedDevices': '1000',  
    'DeviceClass': 'Phone',  
    'Model': '255',  
    'Status': 'Registered',  
    'NodeName': '',  
    'SelectBy': 'Name',  
    'Protocol': 'Any',  
    'DownloadStatus': 'Any', 
    'SelectItems': {
        'Item': [ ]
    } 
}

criteria['SelectItems']['Item'].append(
    { 'item': '*'}
)

try:
    resp = service.selectCmDevice( stateInfo, criteria )
except Fault as err:
    print('Zeep error: selectCmDevice: {err}'.format( err = err))
else:
    print('selectCmDevice response:')
    print()
    print(resp)
    print()

for node in resp['SelectCmDeviceResult']['CmNodes']['item']:

    if node['ReturnCode'] != 'Ok':
        continue

    print( 'Node: ', node['Name'] )
    print()

    print( '{name:19}{ip:19}{dirn:29}{desc:19}'.format(
    name = 'Name',
    ip = 'IP Address',
    dirn = 'Directory Numbers',
    desc = 'Description' ) )

    print( '{name:19}{ip:19}{dirn:29}{desc:19}'.format(
        name = '-'*17,
        ip = '-'*17,
        dirn = '-'*27,
        desc = '-'*25 ) )

    for device in node['CmDevices']['item']:

        ipaddresses = device['IPAddress']

        ipaddress = ipaddresses['item'][0]['IP'] if ipaddresses else ''

        print ( '{name:19}{ip:19}{dirn:29}{desc:19}'.format(
            name = device['Name'], 
            ip = ipaddress, 
            dirn = device['DirNumber'], 
            desc = device['Description'] ) )

    print()



