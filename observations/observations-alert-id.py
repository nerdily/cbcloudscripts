import requests
import argparse
import sys
import pandas as pd
import json
import time

# This script will retrieve observations based off of an alert ID

# Usage: python observations-alert-id.py --help

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


def build_base_url(environment, org_key):
    # Build the observations search job base URL.
    environment = get_environment(environment)
    return f"{environment}/api/investigate/v2/orgs/{org_key}/observations/search_jobs"

def build_observations_search_job_id_url(environment, org_key, job_id):
    # Build the URL to return the results of the search based on job_id
    # Documentation on this specific API call can be found here:
    # https://developer.carbonblack.com/reference/carbon-black-cloud/platform/latest/observations-api/#get-results

    # rtype: string
    environment = get_environment(environment)
    return f"{environment}/api/investigate/v2/orgs/{org_key}/processes/detail_jobs/{job_id}/results"

def main():
    # Main function to parse arguments and retrieve the endpoint results

    parser = argparse.ArgumentParser(prog="observations-alert-id.py",
                                     description="Query VMware Carbon Black \
                                         Cloud for observation based on alert_id.")
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
    requiredNamed.add_argument("-a", "--alert-id", required=True,
                               help="Alert ID to query")
    args = parser.parse_args()

    req_url = build_base_url(args.environment, args.org_key)
    api_token = f"{args.api_secret}/{args.api_id}"

    payload = {
          "query": "",
          "time_range": {
            "window": "-180d"
          },
          "rows": 10000,
          "sort": [
            {
              "field": "device_timestamp",
              "order": "DESC"
            }
          ]
        }

    headers = {
        "Content-Type": "application/json",
        "X-Org": args.org_key,
        "X-Auth-Token": api_token
    }
    payload["query"] = "alert_id:"f"{args.alert_id}"
    response = requests.request('POST', req_url, headers=headers, json=payload)
    if response.status_code == 200:
        print(f"Success {response}")
        response = response.json()
        job_id = response['job_id']
        # Now that we have a job_id, check the status of it.
        req_url = build_observations_search_job_id_url(args.environment, args.org_key, job_id)

        # Initialize contacted and completed to different values so the while loop kicks off at least once
        contacted = 1
        completed = -1
        while contacted != completed:
            response = requests.request("GET", req_url, headers=headers)
            response = response.json()
            contacted = response['contacted']
            completed = response['completed']
        observations_df = pd.DataFrame.from_dict(response['results'])
        print("Done with Observation pull")
        timestamp = time.strftime("%Y%m%d-%H%M%S")  # create a timestamp for our filename
        with open('alerts-' + timestamp + '.json', "w") as f:
            json.dump(response, f)
        observations_df.to_csv('observations-' + timestamp + '.csv')

    else:
        print(response)

if __name__ == "__main__":
    sys.exit(main())