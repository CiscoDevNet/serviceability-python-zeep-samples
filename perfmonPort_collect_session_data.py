"""Serviceability Perfmon <perfmonCollectSessionData> sample script

Creates a perfmon counter session with <perfmonOpenSession>, adds some example
counters with <perfmonAddCounter>, periodically refreshes/parses/prints counter
data with <perfmonCollectSessionData>, then waits for a keypress before cleaning
up the session with <perfmonCloseSession>

Note: this sample uses the 'curses' module, which is not supported fon Windows

Copyright (c) 2020 Cisco and/or its affiliates.
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

import curses

import time
from time import sleep

import os
import sys

# Edit .env file to specify your Webex site/user details
from dotenv import load_dotenv
load_dotenv()

# The WSDL is a local file in the working directory, see README
WSDL_FILE = 'schema/PerfmonService.wsdl'

# Set DEBUG=True in .env to enable output of request/response headers and XML
DEBUG = os.getenv( 'DEBUG' ) == 'True'

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

# Create the Zeep client with the specified settings
client = Client( WSDL_FILE, settings = settings, transport = transport, plugins = [ MyLoggingPlugin() ] )

# Create the Zeep service binding to the Perfmon SOAP service at the specified CUCM
service = client.create_service(
    '{http://schemas.cisco.com/ast/soap}PerfmonBinding',
    f'https://{ os.getenv( "CUCM_ADDRESS" ) }:8443/perfmonservice2/services/PerfmonService' 
    )

# Open a new Perfmon counter session
try:
	resp = service.perfmonOpenSession( )
except Fault as err:
    print( f'Zeep error: perfmonOpenSession: { err }' )
    sys.exit( 1 )

# Save the returned session handle
sessionHandle = resp

print( "\nperfmonOpenSession response:\n" )
print( resp,"\n" )

input( 'Press Enter to continue...\n' )

# Add a set of performance counters to the session

# Create an array of counter names we want to monitor
# See the Perfmon API Reference for info on how to build the counter path name.
# Here we want to monitor the current CUCM node, for the 'Processor' object, of the '0' (first)
#   instance, watching the '% CPU Time'/'IOWait Percentage'/'Idle Percentage' counters
counters = { 
    "Counter": [
        { 'Name': f'\\\\{ os.getenv( "CUCM_ADDRESS" ) }\\Processor(0)\\% CPU Time' },
        { 'Name': f'\\\\{ os.getenv( "CUCM_ADDRESS" ) }\\Processor(0)\\IOwait Percentage' },
        { 'Name': f'\\\\{ os.getenv( "CUCM_ADDRESS" ) }\\Processor(0)\\Idle Percentage' }
    ]
}

try:
	resp = service.perfmonAddCounter( SessionHandle = sessionHandle, ArrayOfCounter = counters )
except Fault as err:
    print( f'Zeep error: perfmonAddCounter: { err }' )
    sys.exit( 1 )

print( "\nperfmonAddCounter response: SUCCESS\n" )

input( 'Press Enter to continue...\n' )

# Define a function to start monitoring session counters
def monitorCounters( stdscr ):

    # Disable printing debug output to keep the display sane
    global DEBUG
    DEBUG_SAVE = DEBUG
    DEBUG = False

    # Using the provided curses window object, turn on non-blocking mode for key input
    stdscr.nodelay( True )

    # Repeat indefinitely (until a break or return)
    while True:

        # Hide the cursor and clear the window
        curses.curs_set(0)
        stdscr.clear()

        # Create a simple report of the XML response, and 'print' to the curses window
        stdscr.addstr( '\nperfmonCollectSessionData output for "Processor(0)"\n' )
        stdscr.addstr( '=======================================================\n\n')

        # Retrieve the latest counter data for the session
        # No Try/Except wrapper is used, so that exceptions trigger the curses.wrapper
        #   behaviour, and are re-raised from the wrapped function (where they
        #   are then handled)
        resp = service.perfmonCollectSessionData( SessionHandle = sessionHandle )

        # Loop through the response and parse/print the counter names and values
        for item in resp:

            #Extract the final value in the counter path, which sould be the counter name
            counterPath = item.Name._value_1
            last = counterPath.rfind( '\\' ) + 1
            counterName = counterPath[ last: ]

            # Print the name and value, padding/truncating the name to 49 characters
            stdscr.addstr( '{:49.49}'.format( counterName ) + ' : ' + str( item.Value ) + '\n' )

        # Print the current time for Last Updated
        stdscr.addstr( f'Last updated: { time.strftime( "%X" ) }\n\n')

        stdscr.addstr( '\n(Press any key to exit)' )

        # Flush the text output to the window
        stdscr.refresh()

        # Check keyboard input for a key press, repeat up to 50 times, waiting a tenth of a
        #   second between re-checks
        for x in range( 1, 50 ):

            # If an input character is waiting...
            if stdscr.getch() != curses.ERR:
                    # Restore the previous debug setting
                    DEBUG = DEBUG_SAVE
                    # Return from the monitorCounters() function
                    return
            else:
                # Otherwise, sleep for tenth of a second
                sleep( 0.1 )

# Start the continuous monitoring function.
# As the function uses curses to handle display/input, curses.wrapper is
# used to automatically return the console window to a sane state in case
# of any unhandled exceptions
try:
    curses.wrapper( monitorCounters )
except Fault as err:
    print( f'Zeep error: perfmonCollectSessionData: { err }' )
    sys.exit( 1 )

# Cleanup the session objected we created
try:
	resp = service.perfmonCloseSession( SessionHandle = sessionHandle )
except Fault as err:
    print( f'Zeep error: perfmonCloseSession: { err }' )
    sys.exit( 1 )

print( "\nperfmonCloseSession response: SUCCESS\n" )






