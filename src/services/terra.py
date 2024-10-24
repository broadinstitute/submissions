import requests
import json
from oauth2client.client import GoogleCredentials

class TerraAPIWrapper:
    def __init__(self, billing_project=None, workspace_name=None):
        self.base_url = "https://api.firecloud.org/api/workspaces"
        self.billing_project = billing_project
        self.workspace_name = workspace_name

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

 
    def call_terra_api(self, sample_id, table):
        """
        Call the Terra API to retrieve reads data.

        Args:
            sample_id (str): The sample ID to filter by.
            table (str): The table name.

        Returns:
            list: A list of results from the API.
        """
        results = []
        page_number = 1
        headers = self.get_headers()
        workspace_url = f"{self.base_url}/{self.billing_project}/{self.workspace_name}/entityQuery/{table}"

        while True:
            parameters = {
                'page': page_number,
                'pageSize': 100,
                'filterTerms': sample_id
            }

            response = requests.get(workspace_url, headers=headers, params=parameters)
            response.raise_for_status()
            data = response.json()

            if data.get('results'):
                results.extend(data['results'])
                page_number += 1

                # Check if the next page exists based on metadata
                metadata = data.get('resultMetadata', {})
                filtered_page_count = metadata.get('filteredPageCount', 0)

                if page_number >= filtered_page_count:
                    break

        return results