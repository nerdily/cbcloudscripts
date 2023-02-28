import requests
import argparse
import sys
import pandas as pd

# This script exports the queried for USB devices and saves them as an Excel file. To change the query, look at the "payload" variable which is the
# json-formatted request made to the CB Cloud back end. The developer documentation has a full list of what can be queried.
# The CB Cloud API will return up to 10,000 items in a single request. If you have more than 10,000 endpoints, you would need
# multiple requests to fetch them all.

# Explanation on the resultant Excel file:
# A "Summary" tab will be created that has an overview of the devices. Column A has a "Device no." entry. This corresponds to the
# relevant "device0" "device1" etc. tab(s) also created which contains USB device details such as which endpoints it has been plugged into,
# not just the *last* endpoint it was plugged into

# Usage: python usb-devices.py --help

# API key permissions required:
# Device Control - Manage External Devices - external-device.manage - read


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


def build_summary_url(environment, org_key):
    # Build the summary URL
    # Documentation on this specific API call can be found here:
    # https://developer.carbonblack.com/reference/carbon-black-cloud/cb-defense/latest/device-control-api/#search-usb-devices
    # rtype: string

    environment = get_environment(environment)
    return f"{environment}/device_control/v3/orgs/{org_key}/devices/_search"




def flatten_json(obj):
    global ret
    ret = {}

    def flatten(x, flattened_key=""):
        if type(x) is dict:
            for current_key in x:
                flatten(x[current_key], flattened_key + current_key + '_')
        elif type(x) is list:
            i = 0
            for elem in x:
                flatten(elem, flattened_key + str(i) + '_')
                i += 1
        else:
            # x === string, integer, bool, etc
            ret[flattened_key[:-1]] = x
    flatten(obj)
    return ret


def main():
    def build_details_url(environment, org_key):
        # Build the summary URL
        # Documentation on this specific API call can be found here:
        # https://developer.carbonblack.com/reference/carbon-black-cloud/cb-defense/latest/device-control-api/#get-usb-device-by-id
        # rtype: string

        environment = get_environment(environment)
        return f"{environment}/device_control/v3/orgs/{org_key}/devices/{j.usb_id}/endpoints"

    # Main function to parse arguments and retrieve the endpoint results

    parser = argparse.ArgumentParser(prog="export-endpoints.py",
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

    req_url = build_summary_url(args.environment, args.org_key)
    api_token = f"{args.api_secret}/{args.api_id}"

    payload = {
          "query": "",
          "criteria": {},
          "sort": [
            {
              "field": "last_seen",
              "order": "DESC"
            }
          ],
          "start": 0,
          "rows": 10000
        }

    headers = {
        "Content-Type": "application/json",
        "X-Auth-Token": api_token
    }

    response = requests.request('POST', req_url, headers=headers, json=payload)

    if response.status_code == 200:
        print(f"Success {response}")
        usb_devices_dict = response.json()
        usb_devices = pd.DataFrame.from_dict(usb_devices_dict['results'])
        usb_devices.rename(columns={"id": "usb_id"}, inplace=True)
        usb_devices.index.name = "Device no."

        # Cool. Let's write to Excel file now
        xlwriter = pd.ExcelWriter('usb-devices.xlsx')
        usb_devices.to_excel(xlwriter, sheet_name='Summary')

    else:
        print(response)

    # Loop through each usb_id from the usb_devices dataframe and pull back the info
    for i, j in usb_devices.iterrows():
        req_url = build_details_url(args.environment, args.org_key)

        # headers = {
        #     "Content-Type": "application/json",
        #     "X-Auth-Token": api_token
        # }

        # Make the request
        response = requests.get(req_url, headers=headers)

        # Let's see what we've got
        usb_device_endpoints_dict = response.json()
        flattened_usb_devices = flatten_json(usb_device_endpoints_dict)
        usb_devices_df = pd.DataFrame.from_dict(flattened_usb_devices, orient='index', columns=['value'])

        usb_devices_df.to_excel(xlwriter, sheet_name='device' + str(i))

    xlwriter.close()
    print('Data exported to usb-devices.xls')




if __name__ == "__main__":
    sys.exit(main())