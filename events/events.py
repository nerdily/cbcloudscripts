import pandas as pd
import requests
import argparse
import sys
import time


# This script exports the queried for events into a csv via the process search and events search API. It will first
# do a process search and then pivot from there using the process_guid to return full event details.

# Usage: python events.py --help

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


def build_process_search_url(environment, org_key):
    # Build the initial search URL
    # Documentation on this specific API call can be found here:
    # https://developer.carbonblack.com/reference/carbon-black-cloud/platform/latest/platform-search-api-processes/#start-a-process-search-v2

    # rtype: string

    environment = get_environment(environment)
    return f"{environment}/api/investigate/v2/orgs/{org_key}/processes/search_jobs"

def build_process_search_job_id_url(environment, org_key, job_id):
    # Build the URL to return the results of the search based on job_id
    # Documentation on this specific API call can be found here:
    # https://developer.carbonblack.com/reference/carbon-black-cloud/platform/latest/platform-search-api-processes/#retrieve-results-for-a-process-detail-search-v2

    # rtype: string
    environment = get_environment(environment)
    return f"{environment}/api/investigate/v2/orgs/{org_key}/processes/detail_jobs/{job_id}/results"


def build_event_search_url(environment, org_key, process_guid):
    # Build the URL to perform an event search with a given process_guid
    # Documentation on this specific API call can be found here:
    # https://developer.carbonblack.com/reference/carbon-black-cloud/platform/latest/platform-search-api-processes/#get-events-associated-with-a-given-process-v2
    environment = get_environment(environment)
    return f"{environment}/api/investigate/v2/orgs/{org_key}/events/{process_guid}/_search"


def main():
    # Main function to parse arguments and retrieve the endpoint results

    # global event_data_df
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

    req_url = build_process_search_url(args.environment, args.org_key)
    api_token = f"{args.api_secret}/{args.api_id}"

    payload = {
    "criteria":
    {},
    "exclusions":
    {},
    "query": "scriptload_name:*.js",
    "time_range":
    {
        "window":"-5m"
    },
    "rows": 10000,
    "fields":
    [
       "*"
    ],
    "sort":
    [
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
        req_url = build_process_search_job_id_url(args.environment, args.org_key, job_id)

        # Initialize contacted and completed to different values so the while loop kicks off at least once
        contacted = 1
        completed = -1
        while contacted != completed:
            response = requests.request("GET", req_url, headers=headers)
            response = response.json()
            contacted = response['contacted']
            completed = response['completed']
        print("Number of processes found: " + str(response['num_found']))
        processes_df = pd.DataFrame.from_dict(response['results'])
        print("Done with Process pull")

        # Now that we have process_guids we can do an event search:
        events_df = pd.DataFrame() # Instantiate our events dataframe
        for i, row in processes_df.iterrows():
            print("Process dataframe row " + str(processes_df.index[i]))
            req_url = build_event_search_url(args.environment, args.org_key, row['process_guid'])
            payload = {
              "query": "scriptload_name:*.js",
              "fields": ["*"],
              "time_range": {
                "window":"-5m"
              }
            }
            # Initialize total_segments and processed_segments to different values so the while loop kicks off at least once
            total_segments = 1
            processed_segments = -1
            while total_segments != processed_segments:
                response = requests.request("POST", req_url, headers=headers, json=payload)
                events_dict = response.json()
                event_data_df = pd.DataFrame.from_dict(events_dict['results'])
                total_segments = events_dict['total_segments']
                processed_segments = events_dict['processed_segments']
            print(f"Event search success {response}")
            events_df = pd.concat([events_df, event_data_df], ignore_index=True)

        merged_df = pd.merge(processes_df, events_df, on='process_guid', how='left')

        # Cool. Let's export to CSV now
        print("Done with Events pull")
        timestamp = time.strftime("%Y%m%d-%H%M%S")  # create a timestamp for our filename
        merged_df.to_csv('events-' + timestamp + '.csv')
        print('Saved to \'events-' + timestamp + '.csv\'')
    else:
        print(response)


if __name__ == "__main__":
    sys.exit(main())