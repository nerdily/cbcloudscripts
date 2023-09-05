import pandas as pd
import requests
import argparse
import sys


# This script exports the queried for events into a csv via the process search API. To change the query, look at the "payload" variable which is the
# json-formatted request made to the CB Cloud back end. The developer documentation has a full list of what can be queried.
# The CB Cloud API will return up to 10,000 items in a single request. If you have more than 10,000 alerts, you would need
# multiple requests to fetch them all.

# This is an example of requesting additional fields that normally might need a second query to retrieve after the summary request.  Fields marked with "Process***" here:
# https://developer.carbonblack.com/reference/carbon-black-cloud/platform/latest/platform-search-fields/
# can simply be added to in the initial request making the follow-up request unnecessary.

# Usage: python export-alerts.py --help

# API key permissions required:
# Search - Events - org.search.events - CREATE
# Search - Events - org.search.events - READ

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


def build_search_url(environment, org_key):
    # Build the initial search URL
    # Documentation on this specific API call can be found here:
    # https://developer.carbonblack.com/reference/carbon-black-cloud/platform/latest/platform-search-api-processes/#start-a-process-search-v2

    # rtype: string

    environment = get_environment(environment)
    return f"{environment}/api/investigate/v2/orgs/{org_key}/processes/search_jobs"

def build_search_job_id_url(environment, org_key, job_id):
    # Build the URL to return the results of the search based on job_id
    # Documentation on this specific API call can be found here:
    # https://developer.carbonblack.com/reference/carbon-black-cloud/platform/latest/platform-search-api-processes/#retrieve-results-for-a-process-detail-search-v2

    # rtype: string
    environment = get_environment(environment)
    return f"{environment}/api/investigate/v2/orgs/{org_key}/processes/detail_jobs/{job_id}/results"


def main():
    # Main function to parse arguments and retrieve the endpoint results

    parser = argparse.ArgumentParser(prog="events.py",
                                     description="Query VMware Carbon Black Cloud for process data.")
    requiredNamed = parser.add_argument_group('required arguments')
    requiredNamed.add_argument("-e", "--environment", required=True, default="PROD05",
                               choices=["EAP1", "PROD01", "PROD02", "PROD05", "PROD06", "PRODNRT", "PRODSYD", "PRODUK", "GOVCLOUD"],
                               help="Environment for the Base URL")
    requiredNamed.add_argument("-o", "--org_key", required=True,
                               help="Org key (found in your product console under Settings > API Access > API Keys)")
    requiredNamed.add_argument("-i", "--api_id", required=True,
                               help="API ID")
    requiredNamed.add_argument("-s", "--api_secret", required=True,
                               help="API Secret Key")
    args = parser.parse_args()

    req_url = build_search_url(args.environment, args.org_key)
    api_token = f"{args.api_secret}/{args.api_id}"

    payload = {
      "criteria": {},
      "exclusions": {},
      "query": "process_name:powershell.exe",
      "time_range": {
        "window": "-1h"
      },
      "rows": 10000,
      "fields": [
        "*"
      ],
      "sort": [
        {
          "field": "device_timestamp",
          "order": "DESC"
        }
      ]
    }

    headers = {
        "Content-Type": "application/json",
        "X-Auth-Token": api_token
    }

    response = requests.request("POST", req_url, headers=headers, json=payload)

    if response.status_code == 200:
        print(f"Process search success {response}")
        response = response.json()
        job_id = response['job_id']

        # Now that we have a job_id, check the status of it.
        req_url = build_search_job_id_url(args.environment, args.org_key, job_id)

        # Initialize contacted and completed to different values so the while loop kicks off at least once
        contacted = 1
        completed = -1
        while contacted != completed:
            response = requests.request("GET", req_url, headers=headers)
            response = response.json()
            contacted = response['contacted']
            completed = response['completed']
        events = pd.DataFrame.from_dict(response['results'])

        # Cool. Let's export to CSV now
        events.to_csv('events.csv')
        print('Saved to \'events.csv\'')
    else:
        print(response)


if __name__ == "__main__":
    sys.exit(main())