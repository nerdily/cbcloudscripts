import requests
import argparse
import sys
import json
import time

# This script establishes a LiveResponse session to a device.

# Usage: python LR-establish-session.py --help

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

def build_start_session_url(environment, org_key):
    # Build the base URL
    # Documentation on this specific API call can be found here:
    # https://developer.carbonblack.com/reference/carbon-black-cloud/platform/latest/devices-api/#search-devices
    # rtype: string

    environment = get_environment(environment)
    return f"{environment}/appservices/v6/orgs/{org_key}/liveresponse/sessions"


def build_session_command_url(environment, org_key, session_id):
    # Build the URL to issue LR commands
    # Documentation on this specific API call can be found here:
    # https://developer.carbonblack.com/reference/carbon-black-cloud/platform/latest/live-response-api/#issue-command
    # rtype: string

    environment = get_environment(environment)
    return f"{environment}/appservices/v6/orgs/{org_key}/liveresponse/sessions/{session_id}/commands"


def build_command_id_url(environment, org_key, session_id, command_id):
    # Build the URL to retrieve the LR command results
    # Documentation on this specific API call can be found here:
    # https://developer.carbonblack.com/reference/carbon-black-cloud/platform/latest/live-response-api/#retrieve-command-status
    # rtype: string
    environment = get_environment(environment)
    return f"{environment}/appservices/v6/orgs/{org_key}/liveresponse/sessions/{session_id}/commands/{command_id}"


def build_get_file_contents_url(environment, org_key, session_id, file_id):
    # Build the URL to retreive the contents of a file via LR
    # Documentation on this specific API call can be found here:
    # https://developer.carbonblack.com/reference/carbon-black-cloud/platform/latest/live-response-api/#get-file-content
    # rtype: string
    environment = get_environment(environment)
    return f"{environment}/appservices/v6/orgs/{org_key}/liveresponse/sessions/{session_id}/files/{file_id}/content"


def build_close_session_url(environment, org_key, session_id):
    # Build the base URL
    # Documentation on this specific API call can be found here:
    # https://developer.carbonblack.com/reference/carbon-black-cloud/platform/latest/devices-api/#search-devices
    # rtype: string

    environment = get_environment(environment)
    return f"{environment}/appservices/v6/orgs/{org_key}/liveresponse/sessions/{session_id}"


def main():
    # Main function to parse arguments and retrieve the endpoint results

    parser = argparse.ArgumentParser(prog="LR-establish-session.py",
                                     description="Begin a Live Response session with CB Cloud.")
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
    requiredNamed.add_argument("-d", "--deviceid", required=True, help="Device ID of target system")
    args = parser.parse_args()

    req_url = build_start_session_url(args.environment, args.org_key)
    api_token = f"{args.api_secret}/{args.api_id}"

    payload = {
        "device_id": f"{args.deviceid}"
    }

    headers = {
        "Content-Type": "application/json",
        "X-Auth-Token": api_token
    }

    # Setting status to PENDING initially so that it will execute the while loop at least once which will actually try and establish the LR session
    status="PENDING"
    print('Connecting to device ID: ' + f"{args.deviceid}")
    print('Status: ' + status)
    while status == "PENDING":
        response = requests.request("POST", req_url, headers=headers, json=payload)
        status=json.loads(response.text)['status']
        session_id=json.loads(response.text)['id']
        status=status
        print('Trying again in 10 seconds...')
        time.sleep(10)
    if status == "ACTIVE":
        print()
        print("LIVE RESPONSE SESSION ESTABLISHED!")
        print('Session id: ' + session_id)
        print('Current working directory: ' + json.loads(response.text)['current_working_directory'])
        print('Supported commands: ' + str(json.loads(response.text)['supported_commands']))
        print()


    # With the LR session established, we now run the command we want. In this case, repcli.exe status
    req_url = build_session_command_url(args.environment, args.org_key,session_id)
    payload = {
      "name": "create process",
      "path": "c:\\program files\\confer\\repcli.exe status",
      "output_file": "c:\\windows\\temp\\repcli-" + f"{args.deviceid}" + ".txt",
      "wait": False
    }
    print("Running 'repcli status'...")
    response = requests.request("POST", req_url, headers=headers, json=payload) # issue the repcli command
    command_id = json.loads(response.text)['id'] # set the command id so we can check its status


    # With the command fired off, check its status. Keep checking until it comes back as 'COMPLETE'
    print('Checking command status...')
    req_url = build_command_id_url(args.environment, args.org_key, session_id, command_id)
    status="PENDING"
    print('status: ' + status)
    while status == "PENDING":
        response = requests.request("GET", req_url, headers=headers)
        status = json.loads(response.text)['status']
        # command_id = json.loads(response.text)['id']
        status = status
        print('Trying again in 10 seconds...')
        time.sleep(10)
    if status == "COMPLETE":
        print('status: ' + status)
        output_file = json.loads(response.text)['input']['output_file']
        print('command output file: ' + output_file)
    else:
        print(status)

    # Get the file ID of the output file and then we can retrieve the contents of it
    req_url = build_session_command_url(args.environment, args.org_key, session_id)
    payload = {
      "name": "get file",
      "path": f"{output_file}"
    }
    print("Getting output file ID")
    response = requests.request("POST", req_url, headers=headers, json=payload)  # issue the get file command
    file_id = json.loads(response.text)['file_details']['file_id']
    print("File ID: " + file_id)

    # Get the file contents and write it to a file locally
    req_url = build_get_file_contents_url(args.environment, args.org_key, session_id, file_id)
    response = requests.request("GET", req_url, headers=headers)  # issue the get contents of the file
    file_content = response.text
    f=open('repcli-' + f"{args.deviceid}" + '-.txt', 'w')
    f.write(file_content)
    f.close()

    # Close the LR session
    req_url = build_close_session_url(args.environment, args.org_key, session_id)
    response = requests.request("DELETE", req_url, headers=headers)
    if response.status_code == 204:
        print()
        print(f"Success {response}")
        print("Live Response session closed")
    else:
        print(response)


if __name__ == "__main__":
    sys.exit(main())