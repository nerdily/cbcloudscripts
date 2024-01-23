import requests
import argparse
import sys
import json
import time

# This script establishes a LiveResponse session to a device.

# Usage: python LR-establish-session.py --help

# API key permissions required:
# TBD


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

def build_start_session_url(environment, org_key):
    # Build the base URL
    # Documentation on this specific API call can be found here:
    # https://developer.carbonblack.com/reference/carbon-black-cloud/platform/latest/devices-api/#search-devices
    # rtype: string

    environment = get_environment(environment)
    return f"{environment}/appservices/v6/orgs/{org_key}/liveresponse/sessions"


def main():
    # Main function to parse arguments and retrieve the endpoint results

    parser = argparse.ArgumentParser(prog="LR-establish-session.py",
                                     description="Begin a Live Response session with CB Cloud.")
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
    requiredNamed.add_argument("-d", "--deviceid", required=True, help="Device ID of target system")
    args = parser.parse_args()

    req_url = build_start_session_url(args.environment, args.org_key)
    api_token = f"{args.api_secret}/{args.api_id}"

    payload = {
        "device_id": f"{args.deviceid}"
    }

    headers = {
        "Content-Type": "application/json",
        "X-Auth-Token": api_token
    }

    # Setting status to PENDING initially so that it will execute the while loop at least once which will actually try and establish the LR session
    status="PENDING"
    print('status: ' + status)
    while status == "PENDING":
        response = requests.request("POST", req_url, headers=headers, json=payload)
        status=json.loads(response.text)['status']
        id=json.loads(response.text)['id']
        status=status
        print('Trying again in 10 seconds...')
        time.sleep(10)
    if status == "ACTIVE":
        print('session id: ' + id)
        print('status: ' + status)
        cwd=json.loads(response.text)['current_working_directory']
        print('current working directory: ' + cwd)



if __name__ == "__main__":
    sys.exit(main())