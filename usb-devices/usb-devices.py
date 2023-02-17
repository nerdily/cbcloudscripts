import requests
import pandas as pd

# API key permissions required:
# Device Control - Manage External Devices - external-device.manage - read

api_id = 'QW1A2MFITH'
api_secret_key = '2ZIR4U3A67BCWGK82GLFCI9K'
org_key = '7PESY63N'
org_id = '1035'
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

# Looks like a 2-step process, similar to looking up users.
# POST {cbc-hostname}/device_control/v3/orgs/{org_key}/devices/_search

# Form our request URL:
req_url = base_url + '/device_control/v3/orgs/' + org_key + '/devices/_search'

# Set our headers
headers = {'X-Auth-Token': api_token,
           'Content-Type': 'application/json'
           }
# Set our data (body) for the request
data = {"query":"","criteria":{},"sort":[{"field":"last_seen","order":"DESC"}],"start":0,"rows":10000}

# Double check they're ok
print('Request URL: ' + req_url)
print('Headers: ', end="")
print(headers)
print('Data: ', end="")
print(data)

# Make the request
req = requests.post(req_url, headers=headers, json=data)
print('Status code: ' + str(req.status_code))

usb_devices_dict = req.json()
usb_devices = pd.DataFrame.from_dict(usb_devices_dict['results'])
usb_devices.set_index('id', drop=True, inplace=True)

# Cool. Let's export to CSV now
usb_devices.to_csv('usb-devices.csv')
print('Exported to \'usb-devices.csv\'')
