from oauth2client.client import GoogleCredentials
import requests
import json

class TerraAPIWrapper:
    def __init__(self, base_url="https://rawls.dsde-prod.broadinstitute.org/api/workspaces"):
        self.base_url = base_url

    def get_access_token(self):
        """Get access token."""
        scopes = ["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email"]
        credentials = GoogleCredentials.get_application_default()
        credentials = credentials.create_scoped(scopes)

        return credentials.get_access_token().access_token

    def get_headers(self):
        return {
            "Authorization": "Bearer " + self.get_access_token(),
            "accept": "*/*", 
            "Content-Type": "application/json"
        }

    def call_terra_api(self, sample_id, project, workspace_name, table):
        """
        Call the Terra API to retrieve reads data.

        Args:
            sample_id (str): The sample ID to filter by.
            project (str): The project name.
            workspace_name (str): The workspace name.
            table (str): The table name.

        Returns:
            list: A list of results from the API.
        """
        results = []
        page_number = 1
        headers = self.get_headers()
        workspace_url = f"{self.base_url}/{project}/{workspace_name}/entityQuery/{table}"

        while True:
            parameters = {
                'page': page_number,
                'pageSize': 100,
                'filterTerms': sample_id
            }

            try:
                response = requests.get(workspace_url, headers=headers, params=parameters)
                response.raise_for_status()
                data = response.json()

                if data.get('results'):
                    results.extend(data['results'])
                    page_number += 1
                else:
                    break
            except requests.exceptions.RequestException as e:
                print(f"Error calling Terra API: {e}")
                break

        return results