import requests
import argparse
import sys
import json

# This script exports the queried for available sensor kits into a json blob.

# Usage: python published-sensor-kits.py --help


# API key permissions required:
# Device - Sensor kits - org.kits - execute
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


def build_base_url(environment, org_id):
    # Build the base URL

    # rtype: string

    environment = get_environment(environment)
    return f"{environment}/appservices/v5/orgs/{org_id}/kits/published?deploymentType=ENDPOINT"


def main():
    # Main function to parse arguments and retrieve the endpoint results

    parser = argparse.ArgumentParser(prog="export-endpoints.py",
                                     description="Query VMware Carbon Black \
                                         Cloud for endpoint data.")
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

    req_url = build_base_url(args.environment, args.org_id)
    api_token = f"{args.api_secret}/{args.api_id}"

    headers = {
        "Content-Type": "application/json",
        "X-Org": args.org_key,
        "X-Auth-Token": api_token
    }

    response = requests.request('GET', req_url, headers=headers)

    if response.status_code == 200:
        print(f"Success {response}")
        filename = f"sensor-kits.json"
        print("Writing results to" f" {filename}")
        with open(filename, "w", encoding="utf-8") as outfile:
            json.dump(response.json(), outfile, indent=4)
    else:
        print(response)



if __name__ == "__main__":
    sys.exit(main())

# Original script below:
# api_id = 'api_id'
# api_secret_key = 'api_secret'
# org_key = 'org_key'
# org_id = 'org_id'
# base_url = 'https://defense.conferdeploy.net'
#
# # Alternatively you can prompt each time for information:
# # api_id = input('Enter the CBC API ID: ')
# # api_secret_key = input('Enter the CBC API Key: ')
# # org_key = input('Enter the CBC Org Key: ')
# # base_url = input('Enter the URL of your Carbon Black Cloud instance: ')
#
# api_token = '/'.join([api_secret_key, api_id])
#
# print('Your Parameters:')
# print('API ID: ' + api_id)
# print('Secret: ' + api_secret_key)
# print('Org key: ' + org_key)
# print('Base URL: ' + base_url)
# print('API token: ' + api_token)
#
# # GET /appservices/v5/orgs/1/kits/published
#
# # Form our request URL:
# req_url = base_url + '/appservices/v5/orgs/' + org_id + '/kits/published?deploymentType=ENDPOINT'
# # Set our headers
# headers = {'X-Auth-Token': api_token,
#            'X-Org': org_key,
#            'Content-Type': 'application/json'
#            }
#
# # Double check they're ok
# print('Request URL: ' + req_url)
# print('Headers: ', end="")
# print(headers)
#
# # Make the request
# req = requests.get(req_url, headers=headers)
# print('Status code: ' + str(req.status_code))
#
# req.json()
