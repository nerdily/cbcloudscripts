import requests
import argparse
import sys
import pandas as pd
import time


# This script exports API keys and last time they were used into a CSV. Be aware that this uses an undocumented API and it
# could break at any time.

# Usage: python API-keys.py --help

# API key permissions required:
# Requires an API key with Super Admin rights.


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


def build_base_url(environment, org_id):
    # Build the base URL
    # Documentation on this specific API call can be found here:
    # https://developer.carbonblack.com/reference/carbon-black-cloud/platform/latest/devices-api/#search-devices
    # rtype: string

    environment = get_environment(environment)
    return f"{environment}/appservices/v5/orgs/{org_id}/connectors/find"


def main():
    # Main function to parse arguments and retrieve the API keys
    parser = argparse.ArgumentParser(prog="api-keys.py",
                                     description="Query VMware Carbon Black \
                                         Cloud for API keys.")
    requiredNamed = parser.add_argument_group('required arguments')
    requiredNamed.add_argument("-e", "--environment", required=True, default="PROD05",
                               choices=["EAP1", "PROD01", "PROD02", "PROD05",
                                        "PROD06", "PRODNRT", "PRODSYD", "PRODUK", "GOVCLOUD"],
                               help="Environment for the Base URL")
    requiredNamed.add_argument("-id", "--org_id", required=True,
                               help="Org ID (found in your product console under \
                              Settings > API Access > API Keys)")
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
      "sortDefinition": {
        "fieldName": "TIME",
        "sortOrder": "ASC"
      },
      "searchWindow": "ALL",
      "fromRow": 0,
      "maxRows": 50,
      "orgId": f"{args.org_id}"
    }

    headers = {
        "Content-Type": "application/json",
        "X-Auth-Token": api_token
    }

    response = requests.request("POST", req_url, headers=headers, json=payload)
    if response.status_code == 200:
        print(f"Success {response}")
        # Take the response and put the 'entries' section into a dataframe for manipulation
        apikeys_dict = response.json()
        apikeys_pd = pd.DataFrame.from_dict(apikeys_dict['entries'])

        # flatten the 'stats' field and append to the dataframe
        apikeys_pd = apikeys_pd.join(pd.json_normalize(apikeys_pd['stats']))

        # drop unneeded rows:
        apikeys_pd = apikeys_pd.drop(columns=['serviceConnector', 'stats', 'sessionId', 'apiKey', 'orgId'])

        # convert date columns from epoch (milliseconds) to datetime
        apikeys_pd['createTime'] = pd.to_datetime(apikeys_pd['createTime'], unit='ms')
        apikeys_pd['lastUpdatedTime'] = pd.to_datetime(apikeys_pd['lastUpdatedTime'], unit='ms')
        apikeys_pd['lastReportedTime'] = pd.to_datetime(apikeys_pd['lastReportedTime'], unit='ms')
        apikeys_pd['sessionStartTime'] = pd.to_datetime(apikeys_pd['sessionStartTime'], unit='ms')

        # Cool. Let's export to CSV now
        timestamp = time.strftime("%Y%m%d-%H%M%S")  # create a timestamp for our filename
        apikeys_pd.to_csv('apikeys-' + timestamp + '.csv')
        print('Saved to \'apikeys-' + timestamp + '.csv')


if __name__ == "__main__":
    sys.exit(main())
