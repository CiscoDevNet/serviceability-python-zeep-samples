# serviceability-python-zeep-samples

## Overview

Sample scripts demonstrating usage of various Cisco CUCM Serviceability APIs using Python and the Zeep SOAP library.

https://developer.cisco.com/site/sxml/

## Available samples

* `risport70_selectCmDevice.py` - Demonstrates querying for all device registrations using Risport (`<selectCmDevice>`)

* `perfmonPort_collect_counter_data.py` - Demonstrates retrieving and parsing performance counter data via the Perfmon `<perfmonCollectCounterData>` request

* `services_getProductInformationList.py` - Use Control Center Services to retrieve a list of the installed Products and versions (`<getProductInformationList>`)

* `perfmonPort_collectSession_data.py` - (Mac/Linux only) Uses Perfmonport to start a collection session, add example counters, then periodically retrieve/parse the results (`<perfmonOpenSession>`, `<perfmonAddCounter>`,`<perfmonCollectCounterData>`)

* `logCollection_GetOneFile.py` - Performs a listing of log files available for a specific service (Cisco Audit Logs), retrieves the contents of the latest file, then parses/prints a few lines of the results (`<selectLogFiles>`, `<GetOneFile>`)

* `services_soapGetServiceStatus.py` - Performs a `<soapGetServiceStatus>` request using the Zeep SOAP library.

Tested using:

* Ubuntu 20.10 / Python 3.8.6
* Mac OS 11.4 / Python 3.9.6

## Getting started

* Install Python 3

  (On Windows, choose the option to add to PATH environment variable)

* Clone this repository:

    ```bash
    git clone https://www.github.com/CiscoDevNet/serviceability-python-zeep-samples
    cd serviceability-python-zeep-samples
    ```

* (Optional) Create/activate a Python virtual environment named `venv`:

    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

* Install needed dependency packages:

    ```bash
    pip install -r requirements.txt
    ```

* Open the project in Visual Studio Code:

    ```bash
    code .
    ```
  
* Rename the file `.env.example` to `.env` and edit to specify your CUCM address and [Serviceability API user credentials](https://d1nmyq4gcgsfi5.cloudfront.net/site/sxml/help/faq/#sec-1)

* The Serviceability SOAP API WSDL files for CUCM v12.5 are included in this project.  If you'd like to use a different version, replace the files in `schema/` with the versions from your CUCM, which can be retrieved at:

    * CDRonDemand: `https://{cucm}/CDRonDemandService2/services/CDRonDemandService?wsdl`

    * Log Collection: `https://{cucm}:8443/logcollectionservice2/services/LogCollectionPortTypeService?wsdl`

    * PerfMon: `https://{cucm}:8443/perfmonservice2/services/PerfmonService?wsdl`

    * RisPort70: `https://{cucm}:8443/realtimeservice2/services/RISService70?wsdl`

    * Control Center Services: `https://{cucm}:8443/controlcenterservice2/services/ControlCenterServices?wsdl`

    * Control Center Services Extended: `https://{cucm}:8443/controlcenterservice2/services/ControlCenterServicesEx?wsdl`

## Hints

* You can get a 'dump' of an API WSDL to see how Zeep interprets it, for example by running (Mac/Linux):

    ```bash
    python -mzeep schema/PerfmonService.wsdl > PerfmonServiceWsdl.txt
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

    ```python
    {
        'members': {
            'member': [
                {
                    'subElement1': 'value',
                    'subElement2': 'value'
                },
                                {
                    'subElement1': 'value',
                    'subElement2': 'value'
                }
            ]
        }
    }
    ```
