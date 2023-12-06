import requests
import argparse
import sys
import pandas as pd
import time


# This script will create an asset group containing hostnames provided via a text file.
# The file should contain one hostname per line. To keep the command line parameters simple, the created
# Asset Group name will also be used as the group's description. The description can be updated later within the CB Cloud UI.

# Usage: python createAssetGroupByHostnames.py --help

# API key permissions required:
# group-management - CREATE


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
    # https://developer.carbonblack.com/reference/carbon-black-cloud/platform/latest/asset-groups-api/#create-asset-group
    # rtype: string

    environment = get_environment(environment)
    return f"{environment}/asset_groups/v1/orgs/{org_key}/groups"


def main():
    # Main function to parse arguments and retrieve the endpoint results

    parser = argparse.ArgumentParser(prog="createAssetGroupByHostnames.py",
                                     description="Query VMware Carbon Black \
                                         Cloud for asset groups.")
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
    requiredNamed.add_argument("-g", "--group_name", required=True,
                               help="Name of the Asset Group to be added"),
    requiredNamed.add_argument("-f", "--file", required=True,
                               help="Filename containing hostnames to add to the Asset Group")
    args = parser.parse_args()

    req_url = build_base_url(args.environment, args.org_key)
    api_token = f"{args.api_secret}/{args.api_id}"

    payload = {
        "description": f"{args.group_name}",
        "member_type": "DEVICE",
        "name": f"{args.group_name}",
        "query": ""
    }

    headers = {
        "Content-Type": "application/json",
        "X-Auth-Token": api_token
    }

    # loop through supplied file and assemble the payload:query value
    hostnames = open(f'{args.file}', 'r').read().split('\n')
    last_hostname = hostnames[-1]
    query = 'name.equals: "'
    for host in hostnames:
        if host != last_hostname:
            query += host + '" OR name.equals: "'
        if host == last_hostname:
            query += host + '"'
    payload['query'] = query

    response = requests.request("POST", req_url, headers=headers, json=payload)

    if response.status_code == 200:
        print(f"Success {response}")

    else:
        print(response)
        print('pause here')

if __name__ == "__main__":
    sys.exit(main())