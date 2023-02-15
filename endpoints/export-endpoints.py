import pandas as pd
import requests
import json
import numpy as np

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

print('Your Parameters')
print('API ID: ' + api_id)
print('Secret: ' + api_secret_key)
print('Org key: ' + org_key)
print('Base URL: ' + base_url)
print('API token: ' + api_token)

# Form our request URL:
req_url = base_url + '/appservices/v6/orgs/' + org_key + '/devices/_search'

# Set our headers
headers = {'X-Auth-Token': api_token,
           'Content-Type': 'application/json'
           }
# Set our data (body) for the request
data = {"criteria":{"deployment_type":["ENDPOINT","WORKLOAD","VDI"]},"sort":[{"field":"last_contact_time","order":"DESC"}],"start":1,"rows":10000,"":""}

# Double check they're ok
print('Request URL: ' + req_url)
print('Headers: ', end="")
print(headers)
print('Data: ', end="")
print(data)

# Make the request
req = requests.post(req_url, headers=headers, json=data)
print('Status code: ' + str(req.status_code))

devices_dict = req.json()
# devices_dict['results']
devices = pd.DataFrame.from_dict(devices_dict['results'])
devices.set_index('device_owner_id', drop=True, inplace=True)

print('Total devices found: ', end="")
print(devices_dict.get('num_found'))
devices.head()

# Cool. Let's export to CSV now
devices.to_csv('devices.csv')
