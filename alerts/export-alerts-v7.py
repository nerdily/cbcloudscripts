import pandas as pd
import requests
import argparse
import sys
import json
from datetime import datetime, timedelta
import time

# This script exports the queried for alerts into a csv via the alerts v7 API. To change the query, look at the "payload" variable which is the
# json-formatted request made to the CB Cloud back end. The developer documentation has a full list of what can be queried.
# The CB Cloud API will return up to 10,000 items in a single request. If you have more than 10,000 alerts, you would need
# multiple requests to fetch them all.

# Usage: python export-alerts.py --help

# API key permissions required:
# Alerts - General information - org.alerts - read

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

def setup_session(api_secret,api_id):
    s = requests.session()
    headers = {
        "X-Auth-Token": f"{api_secret}/{api_id}",
        "Content-Type": "application/json"
        }
    s.headers.update(headers)
    return s


def build_base_url(environment, org_key):
    # Build the base URL
    # Documentation on this specific API call can be found here:
    # https://developer.carbonblack.com/reference/carbon-black-cloud/platform/latest/alerts-api/#alert-search

    # rtype: string

    environment = get_environment(environment)
    return f"{environment}/api/alerts/v7/orgs/{org_key}/alerts/_search"

def request_data(session, pd, environment, org_id):
    url = build_base_url(environment, org_id)
    r = session.post(url, json=pd)
    if r.status_code < 300:
        results = r.json()
    else:
        results = False
    return results


def get_date_range(days_to_export):
    chunks = 6
    tomorrow = datetime.combine(datetime.now() + timedelta(days=1), datetime.min.time())
    two_years_ago = tomorrow - timedelta(days=days_to_export)
    dates = [tomorrow - timedelta(days=x) for x in range(days_to_export, 0, chunks * -1)] + [tomorrow]
    i = 0
    for date in dates:
        dates[i] = datetime.strftime(date, '%Y-%m-%dT%H:%M:%S.%fZ')
        i += 1
    return dates


def main():
    # Main function to parse arguments and retrieve the endpoint results

    parser = argparse.ArgumentParser(prog="export-alerts-v7.py",
                                     description="Query VMware Carbon Black \
                                         Cloud for alert v7 data.")
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
    requiredNamed.add_argument("-d", "--days_to_export", required=True, help="Days to export")
    args = parser.parse_args()

    dates = get_date_range(int(args.days_to_export))
    session = setup_session(args.api_secret,args.api_id)

    payload = {
        "time_range": {
        },
        "criteria": {
            "minimum_severity": 1,
            "workflow_status":
                [
                    "OPEN",
                    "IN_PROGRESS",
                    "CLOSED"
                ],
        },
        "start": "1",
        "rows": "10000",
        "sort": [
            {
                "field": "backend_timestamp",
                "order": "DESC"
            }
        ]
    }

    alerts_json = []
    for x, i in enumerate(dates):
        if x + 1 < len(dates):
            payload["time_range"]["start"] = dates[x]
            payload["time_range"]["end"] = dates[x + 1]
            print(payload)
            data = request_data(session, payload, args.environment, args.org_key)
            alerts_json.extend(data["results"])
    with open("alerts.json", "w") as f:
        json.dump(alerts_json, f)
    # Now pull the json into a pandas dataframe as it can export to csv very nicely:
    alerts_df = pd.read_json("alerts.json")
    timestamp = time.strftime("%Y%m%d-%H%M%S") # create a timestamp for our filename
    alerts_df.to_csv('alerts-v7-' + timestamp + '.csv' )
    print('Saved to \'alerts-v7-' + timestamp + ' .csv\'') # let the user know



if __name__ == "__main__":
    sys.exit(main())
