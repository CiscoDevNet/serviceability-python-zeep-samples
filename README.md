# serviceability-python-zeep-samples

## Overview

Sample scripts demonstrating usage of various Cisco CUCM Serviceability APIs using Python and the Zeep SOAP library.

https://developer.cisco.com/site/sxml/

## Getting started

* Install Python 2.7 or 3.7
  On Windows, choose the option to add to PATH environment variable

* If this is a fresh installation, update pip (you may need to use `pip3` on Linux or Mac)

  ```
  $ python -m pip install --upgrade pip
  ```
  
* Dependency Installation:

  ```
  $ pip install zeep
  ```
  
* Edit creds.py to specify your CUCM location and Serviceability API user credentials

* Add the Serviceability API WSDL files for your CUCM version:

  * **Risport70** - Download from the CUCM host at: [https://{cucm}:8443/realtimeservice2/services/RISService70?wsdl](https://{cucm}:8443/realtimeservice2/services/RISService70?wsdl)

## Hints

* You can get a 'dump' of the API WSDL to see how Zeep interprets it by copying the WSDL files to the project root (see above) and running (Mac/Linux):

    ```
    python3 -mzeep RISService70.wsdl > wsdl.txt
    ```

    This can help with identifying the proper object structure to send to Zeep

* Elements which contain a list, such as:

    ```xml
    <members>
        <member>
            <subElement1/>
            <subElement2/>
        </member>
        <member>
            <subElement1/>
            <subElement2/>
        </member>        
    </members>
    ```

    are represented a little differently than expected by Zeep.  Note that `<member>` becomes an array, not `<members>`:

    ```json
    { 
        members: {
            member: [
                {
                    "subElement1": None,
                    "subElement2": None
                },
                                {
                    "subElement1": None,
                    "subElement2": None
                }
            ]
        }
    }
    ```

## Available samples

* `risport70_selectCmDevice_all.py` - Demonstrates querying for all device registrations using Risport (`<selectCmDevice>`)

