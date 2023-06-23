import pandas as pd
import requests
import argparse
import sys


# This script exports the queried for events into a csv via the process search API. To change the query, look at the "payload" variable which is the
# json-formatted request made to the CB Cloud back end. The developer documentation has a full list of what can be queried.
# The CB Cloud API will return up to 10,000 items in a single request. If you have more than 10,000 alerts, you would need
# multiple requests to fetch them all.

# This is a multistep query. A query is submitted which results in a job ID. That job ID gets polled and when completed the results are returned.
# Then for each result, a second query is made for details via the process guid.

# Usage: python export-alerts.py --help

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

def build_process_detail_url(environment, org_key):
    # Build the URL to return the process details job_id on process_guid
    # Documentation on this specific API call can be found here:
    # https://developer.carbonblack.com/reference/carbon-black-cloud/platform/latest/platform-search-api-processes/#request-details-of-processes-v2

    # rtype: string
    environment = get_environment(environment)
    return f"{environment}/api/investigate/v2/orgs/{org_key}/processes/detail_jobs"

def build_process_detail_job_id_url(environment, org_key, job_id):
    # Buidl the URL to return the process details based on job_id
    # Documentation on this specific API call can be found here:
    # https://developer.carbonblack.com/reference/carbon-black-cloud/platform/latest/platform-search-api-processes/#retrieve-results-for-a-process-detail-search-v2

    # rtype: string
    environment = get_environment(environment)
    return f"{environment}/api/investigate/v2/orgs/{org_key}/processes/detail_jobs/{job_id}/results"


def main():
    # Main function to parse arguments and retrieve the endpoint results

    parser = argparse.ArgumentParser(prog="export-endpoints.py",
                                     description="Query VMware Carbon Black \
                                         Cloud for process data.")
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

    req_url = build_search_url(args.environment, args.org_key)
    api_token = f"{args.api_secret}/{args.api_id}"

    payload = {
      "query": "process_name:powershell.exe",
      "fields": ["*"],
      "sort": [
        {
          "field": "device_timestamp",
          "order": "asc"
        }
      ],
      "start": 0,
      "time_range": {
        "window": "-30d",
      }
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
        #api_token = f"{args.api_secret}/{args.api_id}"

        # Initialize contacted and completed to different values so the while loop kicks off at least once
        contacted = 1
        completed = -1
        while contacted != completed:
            response = requests.request("GET", req_url, headers=headers)
            response = response.json()
            contacted = response['contacted']
            completed = response['completed']
        events = pd.DataFrame.from_dict(response['results'])

        # Trim down the dataframe to just the fields we need
        events = events[['process_guid', 'backend_timestamp', 'device_id', 'device_name', 'device_policy_id', 'process_name', 'process_username']]
        # Add a process_cmdline column
        events['process_cmdline'] = ''

        # Iterate through the events dataframe and do API call for each process_guid. For each process_guid we request a job_id.
        # Then check status of the job_id. If completed = contacted, return the info.
        for i, row in events.iterrows():
            # if pd.isnull(events.loc[i, 'process_guid']) != 1:
            req_url = build_process_detail_url(args.environment, args.org_key)
            process_guid = row.process_guid
            payload = {
              "process_guids": [
                row.process_guid
              ],
              "limited": True
            }
            response = requests.request("POST", req_url, headers=headers, json=payload)
            if response.status_code == 200:
                print(f"Process detail success {response}")
                response = response.json()
                job_id = response['job_id']

                # Now that we have the job_id, check the status of it:
                req_url = build_process_detail_job_id_url(args.environment, args.org_key, job_id)

                # Reset contacted and completed to different values so the while loop kicks off at least once
                contacted = 1
                completed = -1
                while completed != contacted:
                    response = requests.request("GET", req_url, headers=headers)
                    response = response.json()
                    contacted = response['contacted']
                    completed = response['completed']
                details = pd.DataFrame.from_dict(response['results'])
                events.at[i, 'process_cmdline'] = str(details.iloc[0]['process_cmdline'])
                print("Event details successful - round " + str(i) )
        print('Job complete')
        # Cool. Let's export to CSV now
        events.to_csv('events.csv')
        print('Saved to \'events.csv\'')
    else:
        print(response)


if __name__ == "__main__":
    sys.exit(main())
