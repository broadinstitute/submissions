import requests
import json

class GdcApiWrapper:
    def __init__(self, endpoint='https://api.gdc.cancer.gov/v0/submission', program=None, project=None, token=None):
        self.endpoint = endpoint
        self.program = program
        self.project = project
        self.token = token

    def get_entity(self, query_type, submitter_id):
        """Constructs GraphQL query to hit the GDC API"""

        query = self.construct_query(query_type, submitter_id)
        print(f"Query to GDC: {query}")

        return requests.post(
            f"{self.endpoint}/graphql",
            json=query,
            headers={
                "Content-Type": "application/json",
                "X-Auth-Token": self.token
            }
        )

    def get_gdc_schemas(self):
        """Queries GDC to get a specific schema. Replace submitted_aligned_reads with any GDC entity"""

        response = requests.get(f'{self.endpoint}/template/submitted_aligned_reads?format=json')
        with open('src/resources/sample_template.json', 'w') as f:
            f.write(response.text)

    def submit_metadata(self, input_data, metadata):
        """Submits the formatted metadata to GDC API"""

        url = f"{self.endpoint}/{self.program}/{self.project}"

        print("Submit METADATA to GDC dry_run endpoint for PROGRAM PROJECT.")
        try:
            dry_run_response = requests.put(f'{url}/_dry_run',
                data=json.dumps(metadata),
                headers=self.get_headers()
            )
            print("response for the dry commit", dry_run_response.text)
            dry_run_response = json.loads(dry_run_response.text)

            print("response", dry_run_response)
            transaction_id = dry_run_response['transaction_id']

            if dry_run_response['success']:
                print("Successfully submitted metadata for transaction", transaction_id)
                operation = "commit"
            else:
                print("Could not submit metadata for transaction", transaction_id)
                operation = "close"

            commit_response = requests.put(f'{url}/transactions/{transaction_id}/{operation}',
                headers=self.get_headers()
            )
        except Exception as e:
            print("Error", e)

    def construct_query(self, query_type, submitter_id):
        base_query = """
        {{
            {entity} (project_id: "{self.program}-{self.project}", submitter_id: "{submitter_id}") {{
                id
                {additional_fields}
            }}
        }}
        """

        if query_type == "sar":
            entity = "submitted_aligned_reads"
            additional_fields = ""
        elif query_type == "verify":
            entity = "aliquot"
            additional_fields = ""
        else:
            entity = "submitted_aligned_reads"
            additional_fields = """
                submitter_id
                state
                file_state
                error_type
            """

        return {
            "query": base_query.format(entity=entity, program=self.program, project=self.project, submitter_id=submitter_id, additional_fields=additional_fields)
        }

    def get_headers(self):
        return {
            "Content-Type": "application/json",
            "X-Auth-Token": self.token
        }