import requests
import argparse
import json
import sys
from datetime import datetime, timedelta

# This script exports Audit Log entries into a JSON blob. It uses undocumented API calls and was reverse engineered from
# the CB Cloud console. Settings -> Audit Log. PLEASE NOTE! This script requires the Org ID and not the Org Key.
# The Org ID is a numerical figure, not alphanumeric.

# By default, this script returns a "Verbose" Audit Log. It also requests all entries.
# You can modify the post_data JSON blob in main() to tune this. It also will only return 10,000 entries.
# If you have more than 10,000 entries in your audit log, you will likely need to chunk by time frames to return fewer
# than 10,000 entries.

# Usage: python export-audit-log.py --help

# API key permissions required:
# Custom - View All

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

def build_base_url(environment, org_id):
    # Build the base URL
    environment = get_environment(environment)
    return f"{environment}/appservices/v5/orgs/{org_id}/auditlog/find"


def request_data(session, pd, environment, org_id):
    url = build_base_url(environment, org_id)
    r = session.post(url, json=pd)
    if r.status_code < 300:
        results = r.json()
    else:
        results = False
    return results

def get_date_range(days_to_export):
    chunks = 5
    tomorrow = datetime.combine(datetime.now() + timedelta(days=1), datetime.min.time())
    two_years_ago = tomorrow - timedelta(days=days_to_export)
    dates = [tomorrow - timedelta(days=x) for x in range(days_to_export, 0, chunks * -1)] + [tomorrow]
    dates = [int(datetime.timestamp(i) * 1000) for i in dates]
    return dates


def main():
    # Main function to parse arguments and retrieve the results

    parser = argparse.ArgumentParser(prog="export-endpoints.py",
                                     description="Query VMware Carbon Black \
                                         Cloud and export Audit Log data.")
    requiredNamed = parser.add_argument_group('required arguments')
    requiredNamed.add_argument("-e", "--environment", required=True, default="PROD05",
                               choices=["EAP1", "PROD01", "PROD02", "PROD05",
                                        "PROD06", "PRODNRT", "PRODSYD", "PRODUK", "GOVCLOUD"],
                               help="Environment for the Base URL")
    requiredNamed.add_argument("-o", "--org_id", required=True,
                               help="Org ID (found in your product console under \
                              Settings > API Access > API Keys)")
    requiredNamed.add_argument("-i", "--api_id", required=True,
                               help="API ID")
    requiredNamed.add_argument("-s", "--api_secret", required=True,
                               help="API Secret Key")
    requiredNamed.add_argument("-d", "--days_to_export", required=True, help="Days to export")
    args = parser.parse_args()

    dates = get_date_range(int(args.days_to_export))
    session = setup_session(args.api_secret,args.api_id)
    post_data = {
      "fromRow": 1,
      "maxRows": 10000,
      "searchWindow": "ALL",
      "sortDefinition": {
        "fieldName": "TIME",
        "sortOrder": "ASC"
      },
      "criteria": {
        "VERBOSE_ENTRIES": [
          "false"
        ]
      },
      "orgId": 1035,
      "highlight": "false"
    }
    entries = []
    for x, i in enumerate(dates):
        if x + 1 < len(dates):
            post_data["startTime"] = dates[x]
            post_data["endTime"] = dates[x + 1]
            data = request_data(session, post_data, args.environment, args.org_id)
            entries.append(data["entries"])
    with open("audit_log.json", "w") as f:
        json.dump(entries, f)




if __name__ == "__main__":
    sys.exit(main())