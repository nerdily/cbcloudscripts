import requests
import argparse
import sys
import pandas as pd
import time


# This script simply queries your backend and lists your asset groups

# Usage: python getAssetGroups.py --help

# API key permissions required:
# group-management - READ


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
    # https://developer.carbonblack.com/reference/carbon-black-cloud/platform/latest/asset-groups-api/#get-all-asset-groups
    # rtype: string

    environment = get_environment(environment)
    return f"{environment}/asset_groups/v1/orgs/{org_key}/groups"


def main():
    # Main function to parse arguments and retrieve the endpoint results

    parser = argparse.ArgumentParser(prog="getAssetGroups.py",
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
    parser.add_argument("-c", "--csv", action='store_true', help="Export the data to a csv file")
    args = parser.parse_args()

    req_url = build_base_url(args.environment, args.org_key)
    api_token = f"{args.api_secret}/{args.api_id}"

    headers = {
        "Content-Type": "application/json",
        "X-Auth-Token": api_token
    }

    response = requests.request("GET", req_url, headers=headers)

    if response.status_code == 200:
        print(f"Success {response}")
        assetGroups_dict = response.json()
        assetGroups_df = pd.DataFrame.from_dict(assetGroups_dict['results'])

        print('Total asset groups found: ', end="")
        print(assetGroups_dict.get('num_found'))
        print(response.json())
        if args.csv == True:
            timestamp = time.strftime("%Y%m%d-%H%M%S")  # create a timestamp for our filename
            assetGroups_df.to_csv('assetGroups-' + timestamp + '.csv')

    else:
        print(response)


if __name__ == "__main__":
    sys.exit(main())