import requests
import json
import edn_format

# Need to figure out a better way to handle the env variables
endpoint = 'https://api.gdc.cancer.gov/v0/submission'

def submit(input):
    file = open('src/resources/metadata.json')
    fileToken = open('tokens/gdc-token.txt')
    data = json.load(file)
    token = fileToken.read()
    url = f"{endpoint}/{input['program']}/{input['project']}/_dry_run"

    print("Submit METADATA to GDC dry_run endpoint for PROGRAM PROJECT.")

    print("url", url)
    try:
        response = requests.post(url,
            data = json.dumps(data),
            headers = {
                "Content-Type": "application/json",
                "X-Auth-Token": token
            }
        )
    except Exception as e:
        print("Error", e)

    print("response", response.text)

# Run this function if you would like to see all entity schemas in GDC
def getGdcShemas():
    response = requests.get(f'{endpoint}/_dictionary/_all', params = {})
    f = open('src/resources/reads_output.json', 'w')
    f.write(response.text)
    f.close()
