import pandas as pd
import requests

# This script exports the queried for alerts into a csv. To change the query, look at the "data" variable which is the
# json-formatted request made to the CB Cloud back end. The developer documentation has a full list of what can be queried.
# The CB Cloud API will return up to 10,000 items in a single request. If you have more than 10,000 endpoints, you would need
# multiple requests to fetch them all.

# API key permissions required:
# Alerts - General information - org.alerts - read
# Alerts - Dismiss - org.alerts.dismiss - execute
# Alerts - Notes - org.alerts.notes - create, read, delete
# Alerts - ThreatMetadata - org.xdr.metadata - read (optional)

api_id = 'api_id'
api_secret_key = 'api_secret'
org_key = 'org_key'
org_id = 'org_id'
base_url = 'https://defense.conferdeploy.net'

# Alternatively you can prompt each time for information:
# api_id = input('Enter the CBC API ID: ')
# api_secret_key = input('Enter the CBC API Key: ')
# org_key = input('Enter the CBC Org Key: ')
# base_url = input('Enter the URL of your Carbon Black Cloud instance: ')

api_token = '/'.join([api_secret_key, api_id])

print('Your Parameters:')
print('API ID: ' + api_id)
print('Secret: ' + api_secret_key)
print('Org key: ' + org_key)
print('Base URL: ' + base_url)
print('API token: ' + api_token)

# Documentation on this specific API call can be found here:
# https://developer.carbonblack.com/reference/carbon-black-cloud/platform/latest/alerts-api/

# Form our request URL:
req_url = base_url + '/appservices/v6/orgs/' + org_key + '/alerts/_search'

# Set our headers
headers = {'X-Auth-Token': api_token,
           'Content-Type': 'application/json'
           }
# Set our data (body) for the request
data = {"criteria":{"group_results":"false","minimum_severity":"1","category":["THREAT"],"workflow":["DISMISSED","OPEN"],"alert_type":["CB_ANALYTICS"],"create_time":{"range":"all"}},"query":"","sort":[{"field":"create_time","order":"DESC"}],"start":0,"rows":10000}

# Double check they're ok
print('Request URL: ' + req_url)
print('Headers: ', end="")
print(headers)
print('Data: ', end="")
print(data)

# Make the request
req = requests.post(req_url, headers=headers, json=data)
print('Status code: ' + str(req.status_code))

# Let's see what we've got
alerts_dict = req.json()

print('Total alerts found: ', end="")
print(alerts_dict.get('num_found'))
print('Total alerts available: ', end="")
print(alerts_dict.get('num_available'))

alerts = pd.DataFrame.from_dict(alerts_dict['results'])

# Cool. Let's export to CSV now
alerts.to_csv('alerts.csv')
