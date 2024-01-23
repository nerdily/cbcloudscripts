import requests
import argparse
import sys
import json
import time

# This script establishes a liveresponse session to a device.

# Usage: python LR-close-session.py --help

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

def build_close_session_url(environment, org_key, session_id):
    # Build the base URL
    # Documentation on this specific API call can be found here:
    # https://developer.carbonblack.com/reference/carbon-black-cloud/platform/latest/devices-api/#search-devices
    # rtype: string

    environment = get_environment(environment)
    return f"{environment}/appservices/v6/orgs/{org_key}/liveresponse/sessions/{session_id}"


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
    requiredNamed.add_argument("-sid", "--session_id", required=True, help="Session ID to close")
    args = parser.parse_args()

    req_url = build_close_session_url(args.environment, args.org_key, args.session_id)
    api_token = f"{args.api_secret}/{args.api_id}"

    headers = {
        "Content-Type": "application/json",
        "X-Auth-Token": api_token
    }

    response = requests.request("DELETE", req_url, headers=headers)
    if response.status_code == 204:
        print(f"Success {response}")
        print("Live Response session closed")
    else:
        print(response)


if __name__ == "__main__":
    sys.exit(main())