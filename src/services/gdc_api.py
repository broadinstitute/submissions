import requests
import json
import logging

logging.basicConfig(
    format="%(levelname)s: %(asctime)s : %(message)s", level=logging.INFO
)


class GdcApiWrapper:
    def __init__(self, program=None, project=None, token=None):
        self.endpoint = 'https://api.gdc.cancer.gov/v0/submission'
        self.program = program
        self.project = project
        self.token = token

    def get_entity(self, query_type, submitter_id):
        """Constructs GraphQL query to hit the GDC API"""

        query = self.construct_query(query_type, submitter_id)

        return requests.post(
            f"{self.endpoint}/graphql",
            json=query,
            headers=self.get_headers()
        )

    def get_gdc_schemas(self):
        """Queries GDC to get a specific schema. Replace submitted_aligned_reads with any GDC entity"""

        response = requests.get(f'{self.endpoint}/template/submitted_aligned_reads?format=json')
        with open('src/resources/sample_template.json', 'w') as f:
            f.write(response.text)

    def submit_metadata(self, metadata):
        """Submits the formatted metadata to GDC API"""

        url = f"{self.endpoint}/{self.program}/{self.project}"

        logging.info(
            f"Submitting metadata to GDC dry_run endpoint for program {self.program} in project {self.project}"
        )
        try:
            dry_run_response = requests.put(
                f"{url}/_dry_run",
                data=json.dumps(metadata),
                headers=self.get_headers()
            ).json()

            logging.info(f"Response for the dry commit: {dry_run_response}")
            transaction_id = dry_run_response.get("transaction_id")

            if dry_run_response.get("success"):
                logging.info(f"Successfully submitted metadata for transaction {transaction_id}")
                operation = "commit"
                commit_response = requests.put(
                    url=f"{url}/transactions/{transaction_id}/{operation}",
                    headers=self.get_headers()
                )
                logging.info(f"Response for the '{operation}' operation: {commit_response.status_code}")

            else:
                logging.error(f"Could not submit metadata for transaction {transaction_id}")
                operation = "close"
                commit_response = requests.put(
                    f"{url}/transactions/{transaction_id}/{operation}",
                    headers=self.get_headers()
                )
                logging.warning(f"Response for the '{operation}' operation: {commit_response.status_code}")
                raise Exception(f"Could not submit metadata for transaction {transaction_id}")

            return operation

        except Exception as e:
            raise Exception(f"Error: {e}")

    def construct_query(self, query_type, submitter_id):
        base_query = """
        {{
            {entity} (project_id: "{program}-{project}", submitter_id: "{submitter_id}") {{
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