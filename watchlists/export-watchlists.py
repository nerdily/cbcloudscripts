import requests
import argparse
import sys
import pandas as pd
import json

# This script exports Watchlists into an Excel file

# Explanation on the resultant Excel file:
# This script will create an Excel file ('watchlists.xlsx') where each watchlist is written out to a tab. Each tab will
# also contain each report associated with that watchlist and the IOCs of each report

# Usage: python export-watchlists.py --help

# API key permissions required:
# Custom Detections - Watchlists - org.watchlists - READ

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
    # Build the base URL
    environment = get_environment(environment)
    return f"{environment}/threathunter/watchlistmgr/v3/orgs/{org_key}/watchlists"

def build_report_url(environment, org_key):
    # Build the report URL
    environment = get_environment(environment)
    return f"{environment}/threathunter/watchlistmgr/v3/orgs/{org_key}/reports/"

def flatten_json(obj):
    # Function to flatten our JSON objects.
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

    req_url = build_base_url(args.environment, args.org_key)
    api_token = f"{args.api_secret}/{args.api_id}"

    headers = {
        "Content-Type": "application/json",
        "X-Org": args.org_key,
        "X-Auth-Token": api_token
    }

    response = requests.request('GET', req_url, headers=headers)
    if response.status_code == 200:
        print(f"Success {response}")
        wldata = response.json()
    else:
        print(response)

    #Flatten the returned JSON blob:
    flattened_wldata=flatten_json(wldata)
    #Create the watchlist dataframe:
    watchlistdf = pd.DataFrame.from_dict(flattened_wldata, orient='index', columns=['report-id'])
    watchlistdf = watchlistdf.reset_index(drop=False)
    watchlistdf.rename(columns={'index': 'name'}, inplace=True)

    #Create the (watchlist) reports dataframe
    for each in flattened_wldata.items():
      reports = {k:v for (k,v) in flattened_wldata.items() if k.__contains__('report_ids')}
      reportsdf = pd.DataFrame(data=reports, index=['report-id']).transpose()
      #add report data column
      reportsdf['report-data'] = ''

    # Iterate through the reportsdf dataframe and do API call for each report ID. Send the results through the
    # flatten_json function and drop the flattened json into the dataframe's 'report-data' field.
    # Depending upon how many reports there are, this may take a few minutes to run.
    for i, row in reportsdf.iterrows():
      if pd.isnull(reportsdf.loc[i, 'report-id']) != 1:
        #report_req_url = args.environment + '/threathunter/watchlistmgr/v3/orgs/' + args.org_key + '/reports/' + row['report-id']
        report_req_url = build_report_url(args.environment, args.org_key) + row['report-id']
        #Make the request
        report_response = requests.get(report_req_url, headers=headers)
        #Report if we get a status code not 200
        if report_response.status_code != 200:
          print('status code: ' + str(report_response.status_code))
        report_data = report_response.json()
        flattened_report = json.dumps(flatten_json(report_data))
        row['report-data'] = flattened_report
    print("Done with report API calls")
    # merge the dataframes and de-dupe based on the 'name' field.
    mergeddf = pd.merge(watchlistdf, reportsdf, on='report-id', how='left').drop_duplicates(subset=['name'])

    #Filter DataFrame by results_(counter) (ex: 'results_0_', 'results_1_') and dump each to an Excel sheet in a workbook.
    xlwriter = pd.ExcelWriter('watchlists.xlsx')
    i = 0
    while i < mergeddf.shape[0]:
      #Create a mask
      mask = mergeddf['name'].str.startswith('results_' + str(i) + '_')
      if len(mergeddf[mask]) == 0:
        break
      #Apply the mask and write to Excel sheet
      mergeddf[mask].to_excel(xlwriter,sheet_name='watchlist'+str(i))
      i += 1

    xlwriter.close()
    print("watchlists.xlsx written")


if __name__ == "__main__":
    sys.exit(main())