# serviceability-python-zeep-samples

## Overview

Sample scripts demonstrating usage of various Cisco CUCM Serviceability APIs using Python and the Zeep SOAP library.

https://developer.cisco.com/site/sxml/

## Available samples

* `risport70_selectCmDevice.py` - Demonstrates querying for all device registrations using Risport (`<selectCmDevice>`)

* `perfmonPort_collect_counter_data.py` - Demonstrates retrieving and parsing performance counter data via the Perfmon `<perfmonCollectCounterData>` request

* `services_getProductInformationList.py` - Use Control Center Services to retrieve a list of the installed Products and versions (`<getProductInformationList>`)

## Getting started

* Install 3.7

  (On Windows, choose the option to add to PATH environment variable)

* Dependency Installation:

  ```bash
  pip install -r requirements.txt
  ```
  
* Edit `creds.py` to specify your CUCM address and [Serviceability API user credentials](https://d1nmyq4gcgsfi5.cloudfront.net/site/sxml/help/faq/#sec-1)

* The Serviceability SOAP API WSDL files for CUCM v12.5 are included in this project.  If you'd like to use a different version, replace the files in `schema/` with the versions from your CUCM, which can be retrieved at:

    * CDRonDemand: `https://{cucm}/CDRonDemandService2/services/CDRonDemandService?wsdl`

    * Log Collection: `https://{cucm}:8443/logcollectionservice2/services/LogCollectionPortTypeService?wsdl`

    * PerfMon: `https://{cucm}:8443/perfmonservice2/services/PerfmonService?wsdl`

    * RisPort70: `https://{cucm}:8443/realtimeservice2/services/RISService70?wsdl`

    * Control Center Services: `https://ServerName:8443/controlcenterservice2/services/ControlCenterServices?wsdl`

    * Control Center Services Extended: `https://ServerName:8443/controlcenterservice2/services/ControlCenterServicesEx?wsdl`

## Hints

* You can get a 'dump' of an API WSDL to see how Zeep interprets it, for example by running (Mac/Linux):

    ```bash
    python3 -mzeep schema/PerfmonService.wsdl > PerfmonServiceWsdl.txt
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
