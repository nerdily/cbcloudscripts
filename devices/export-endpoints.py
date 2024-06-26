import requests
import argparse
import sys
import pandas as pd
import time


# This script exports the queried for devices into a csv. To change the query, look at the "payload" variable which is the
# json-formatted request made to the CB Cloud back end. The developer documentation has a full list of what can be queried.
# The CB Cloud API will return up to 10,000 items in a single request. If you have more than 10,000 devices, you would need
# multiple requests to fetch them all.

# Usage: python export-devices.py --help

# API key permissions required:
# Device - General Information - device - read


def get_environment(environment):
    # Function to get the required environment to build a Base URL. More info about building a Base URL can be found at
    # https://developer.carbonblack.com/reference/carbon-black-cloud/authentication/#building-your-base-urls

    # rtype: string

    if environment == "EAP1":
        return "https://defense-eap01.confer.deploy.net"
    elif environment == "PROD01":
        return "https://dashboard.confer.net"
    elif environment == "PROD02":
        return "https://defense.conferdeploy.net"
    elif environment == "PROD05":
        return "https://defense-prod05.conferdeploy.net"
    elif environment == "PROD06":
        return "https://defense-eu.conferdeploy.net"
    elif environment == "PRODNRT":
        return "https://defense-prodnrt.conferdeploy.net"
    elif environment == "PRODSYD":
        return "https://defense-prodsyd.conferdeploy.net"
    elif environment == "PRODUK":
        return "https://ew2.carbonblack.vmware.com"
    elif environment == "GOVCLOUD":
        return "https://gprd1usgw1.carbonblack-us-gov.vmware.com"


def build_base_url(environment, org_key):
    # Build the base URL
    # Documentation on this specific API call can be found here:
    # https://developer.carbonblack.com/reference/carbon-black-cloud/platform/latest/devices-api/#search-devices
    # rtype: string

    environment = get_environment(environment)
    return f"{environment}/appservices/v6/orgs/{org_key}/devices/_search"


def main():
    # Main function to parse arguments and retrieve the endpoint results

    parser = argparse.ArgumentParser(prog="export-devices.py",
                                     description="Query VMware Carbon Black \
                                         Cloud for endpoint data.")
    requiredNamed = parser.add_argument_group('required arguments')
    requiredNamed.add_argument("-e", "--environment", required=True, default="PROD05",
                               choices=["EAP1", "PROD01", "PROD02", "PROD05",
                                        "PROD06", "PRODNRT", "PRODSYD", "PRODUK", "GOVCLOUD"],
                               help="Environment for the Base URL")
    requiredNamed.add_argument("-o", "--org_key", required=True,
                               help="Org key (found in your product console under \
                              Settings > API Access > API Keys)")
    requiredNamed.add_argument("-i", "--api_id", required=True,
                               help="API ID")
    requiredNamed.add_argument("-s", "--api_secret", required=True,
                               help="API Secret Key")
    args = parser.parse_args()

    req_url = build_base_url(args.environment, args.org_key)
    api_token = f"{args.api_secret}/{args.api_id}"

    payload = {
        "criteria": {
            "deployment_type": [
                "ENDPOINT",
                "WORKLOAD",
                "VDI"
            ]
        },
        "sort": [
            {
                "field": "last_contact_time",
                "order": "DESC"
            }
        ],
        "start": 1,
        "rows": 10000,
        "": ""
    }

    headers = {
        "Content-Type": "application/json",
        "X-Auth-Token": api_token
    }

    response = requests.request("POST", req_url, headers=headers, json=payload)

    if response.status_code == 200:
        print(f"Success {response}")
        devices_dict = response.json()
        devices = pd.DataFrame.from_dict(devices_dict['results'])
        devices.set_index('device_owner_id', drop=True, inplace=True)

        print('Total devices found: ', end="")
        print(devices_dict.get('num_found'))

        # Cool. Let's export to CSV now
        timestamp = time.strftime("%Y%m%d-%H%M%S")  # create a timestamp for our filename
        devices.to_csv('devices-' + timestamp + '-.csv')
        print('Saved to \'devices-'+ timestamp +'-.csv')

    else:
        print(response)


if __name__ == "__main__":
    sys.exit(main())
