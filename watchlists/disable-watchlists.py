import requests
import argparse
import sys
import json
import datefinder
import datetime
import time


# This script will churn through watchlists and disables those where a specified "disable on" date is in the
# description field of the watchlist.

# Usage: python disable-watchlists.py --help

# API key permissions required:
# Custom Detections - Watchlists - org.watchlists - READ
# Custom Detections - Watchlists - org.watchlists - UPDATE

def get_environment(environment) -> str:
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


def build_get_watchlists_url(environment, org_key) -> str:
    # Build the base URL
    environment = get_environment(environment)
    return f"{environment}/threathunter/watchlistmgr/v3/orgs/{org_key}/watchlists"


def build_update_watchlist_url(environment, org_key, watchlist_id) -> str:
    # Build the URL to update a watchlist
    environment = get_environment(environment)
    return f"{environment}/threathunter/watchlistmgr/v3/orgs/{org_key}/watchlists/{watchlist_id}"


def main():
    # Main function to parse arguments and retrieve the results

    parser = argparse.ArgumentParser(prog="disable-watchlists.py",
                                     description="Query VMware Carbon Black Cloud and disable watchlists if there's a \
                                     'Disable after YYYY-MM-DD' string in the watchlist's description.")
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

    req_url = build_get_watchlists_url(args.environment, args.org_key)
    api_token = f"{args.api_secret}/{args.api_id}"

    headers = {
        "Content-Type": "application/json",
        "X-Org": args.org_key,
        "X-Auth-Token": api_token
    }

    today = datetime.date.fromtimestamp(time.time())

    response = requests.request('GET', req_url, headers=headers)
    if response.status_code == 200:
        print(f"Success {response}")
        wldata_json = json.loads(response.text)

        # print the keys and values
        for key in wldata_json['results']:
            print("Watchlist: " + key['name'])
            wl_id = key['id']
            wl_description = key['description']
            print("Description: " + wl_description)
            date_matches = list(datefinder.find_dates(wl_description,strict=True))
            if len(date_matches) > 0:
                date = date_matches[0].date()
                print("Today's date is " + str(today) + " and the watchlist's expiration date is " + str(date) + ". ", end='')
                if today > date:
                    if key['tags_enabled'] == True:
                        print("We should disable this watchlist")
                        req_url = build_update_watchlist_url(args.environment, args.org_key, wl_id)
                        payload = {
                            "name": f"{key['name']}",
                            "description": f"{key['description']}",
                            "tags_enabled": False,
                            "report_ids": key['report_ids']
                        }
                        response = requests.request('PUT', req_url, headers=headers, json=payload)
                        if response.status_code == 200:
                            print("Watchlist disabled.")
                        else:
                            print("Status code/error: " + response.text)
                        print()
                    if key['tags_enabled'] == False:
                        print("Watchlist already disabled.")
                        print()
                else:
                    print("Leave the watchlist alone for now.")
                    print()

            else:
                print("No expiration date found")
                print()
    else:
        print(response)


if __name__ == "__main__":
    sys.exit(main())
