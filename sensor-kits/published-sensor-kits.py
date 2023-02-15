import requests

# API key permissions required:
# Device - Sensor kits - org.kits - execute

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

# GET /appservices/v5/orgs/1/kits/published

# Form our request URL:
req_url = base_url + '/appservices/v5/orgs/' + org_id + '/kits/published?deploymentType=ENDPOINT'
# Set our headers
headers = {'X-Auth-Token': api_token,
           'X-Org': org_key,
           'Content-Type': 'application/json'
           }

# Double check they're ok
print('Request URL: ' + req_url)
print('Headers: ', end="")
print(headers)

# Make the request
req = requests.get(req_url, headers=headers)
print('Status code: ' + str(req.status_code))

req.json()
