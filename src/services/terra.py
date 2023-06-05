from oauth2client.client import GoogleCredentials

base_url = "https://rawls.dsde-prod.broadinstitute.org/api/workspaces"

# function to get authorization bearer token for requests
def get_access_token():
    """Get access token."""

    scopes = ["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email"]
    credentials = GoogleCredentials.get_application_default()
    credentials = credentials.create_scoped(scopes)

    return credentials.get_access_token().access_token

def get_headers():
    return {
        "Authorization": "Bearer " + get_access_token(),
        "accept": "*/*", 
        "Content-Type": "application/json"
    }

def callTerraApi(sample_id, project, workspace_name, table):
    """Call the Terra api to retrieve reads data"""
    results = []
    page_number = 1
    more_results = True
    headers = get_headers()
    baseUrl = f"{base_url}/{project}/{workspace_name}/entityQuery/{table}"

    while more_results:
        parameters = {
            'page': page_number,
            'pageSize': 100,
            'filterTerms': sample_id
        }

        print(f"Calling terra api on page {page_number}")

        response = requests.get(baseUrl, headers=headers, params=parameters)
        status_code = response.status_code
        data = json.loads(response.text)

        if data and data.results and len(data.results) > 0:
            results += data.results
            page_number += 1
        else:
            more_results = False

    return results