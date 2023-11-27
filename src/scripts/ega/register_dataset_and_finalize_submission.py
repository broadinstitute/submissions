"""
    After crams have been submitted and validated, AND the experiments/runs for each sample have been registered, this
    script can be run for a BATCH of samples to register the dataset and finalize the submission
    It will:
    1) Log in and retrieve access token for the EGA
    2) Use the EGA APIs to:
        a) Create a DATASET for a batch of samples
        c) Finalize the submission

   Resources:
    - Schema Map:
        https://ega-archive.org/submission/metadata/ega-schema/
    - Portal API Submission Overview:
        https://ega-archive.org/submission/metadata/submission/sequencing-phenotype/submitter-portal-api/
    - Submission API Documentation:
        https://submission.ega-archive.org/api/spec/#/
"""
import sys
import argparse
import requests
import logging
from datetime import datetime
from typing import Optional


sys.path.append("./")
from src.scripts.ega.utils import (
    LoginAndGetToken,
    SUBMISSION_PROTOCOL_API_URL,
    format_request_header,
    VALID_STATUS_CODES,
)

logging.basicConfig(
    format="%(levelname)s: %(asctime)s : %(message)s", level=logging.INFO
)


class RegisterEgaDatasetAndFinalizeSubmission:

    def __init__(
            self,
            token: str,
            submission_accession_id: str,
            policy_title: str,
            library_strategy: list[str],
            run_accession_ids: list[str],
            dataset_title: Optional[str],
            dataset_description: Optional[str]
    ):
        self.token = token
        self.submission_accession_id = submission_accession_id
        self.policy_title = policy_title
        self.library_strategy = library_strategy
        self.run_accession_ids = run_accession_ids
        self.dataset_title = dataset_title
        self.dataset_description = dataset_description

    def _headers(self) -> dict:
        return format_request_header(self.token)

    def _get_policy_accession_id(self) -> Optional[str]:
        """
        Collects all policy metadata
        Endpoint documentation located here:
        https://submission.ega-archive.org/api/spec/#/paths/policies/get
        """

        response = requests.get(
            url=f"{SUBMISSION_PROTOCOL_API_URL}/policies",
            headers=self._headers(),
        )
        if response.status_code in VALID_STATUS_CODES:
            policy_accession_id = [a["accession_id"] for a in response.json() if a["title"] == self.policy_title]
            if not policy_accession_id:
                raise ValueError(
                    f"Expected to find one DAC, but found zero for policy {self.policy_title}"
                )
            if len(policy_accession_id) > 1:
                raise ValueError(
                    f"Expected to find one DAC, but found {len(policy_accession_id)} for policy {self.policy_title}"
                )
            logging.info("Successfully retrieved policy DAC")
            return policy_accession_id[0]
        else:
            error_message = f"""Received status code {response.status_code} with error: {response.text} 
            while attempting to get policy accession ID"""
            logging.error(error_message)
            raise Exception(error_message)

    def _dataset_exists(self, policy_accession_id: str, dataset_title: str) -> Optional[str]:
        """
        Gets existing datasets in the submission
        Endpoint documentation located here:
        https://submission.ega-archive.org/api/spec/#/paths/submissions-accession_id--datasets/get
        """
        response = requests.get(
            url=f"{SUBMISSION_PROTOCOL_API_URL}/submissions/{self.submission_accession_id}/datasets",
            headers=self._headers(),
        )
        if response.status_code in VALID_STATUS_CODES:
            all_datasets = response.json()
            for dataset in all_datasets:
                if dataset["policy_accession_id"] == policy_accession_id and dataset["title"] == dataset_title:
                    logging.info(
                        f"Dataset with title {dataset_title} associated with policy {policy_accession_id} already "
                        f"exists. Will not attempt to re-create it."
                    )
                    return dataset["accession_id"]
            logging.info(
                f"Dataset with title {dataset_title} associated with policy {policy_accession_id} does not exist. "
                f"Will attempt to create it now."
            )
            return None
        else:
            error_message = f"""Received status code {response.status_code} with error: {response.text} while 
            attempting to query existing datasets"""
            logging.error(error_message)
            raise Exception(error_message)

    def _conditionally_create_dataset(self, policy_accession_id: str) -> Optional[str]:
        """
        Registers the dataset of runs
        Endpoint documentation located here:
        https://submission.ega-archive.org/api/spec/#/paths/submissions-accession_id--datasets/post
        """
        library_strategies = list(set(self.library_strategy))
        if len(library_strategies) > 1:
            raise ValueError(
                f"Expected to find one unique library strategy. Instead found {len(self.library_strategy)}"
            )
        strategy = library_strategies[0]
        if strategy == "WGS":
            dataset_type = "Whole genome sequencing"
        elif strategy == "WXS":
            dataset_type = "Exome sequencing"
        else:
            raise Exception(f"Expected library strategy to be one of 'WGS' or 'WXS', instead received {strategy}")

        dataset_title = (self.dataset_title if self.dataset_title else
                         f"{dataset_type} sequencing of samples for {self.submission_accession_id}")
        dataset_description = self.dataset_description if self.dataset_description else dataset_title

        if dataset_accession_id := self._dataset_exists(policy_accession_id, dataset_title):
            return dataset_accession_id

        logging.info("Attempting to create dataset.")
        response = requests.post(
            url=f"{SUBMISSION_PROTOCOL_API_URL}/submissions/{self.submission_accession_id}/datasets",
            headers=self._headers(),
            json={
                "title": dataset_title,
                "description": dataset_description,
                "dataset_types": [dataset_type],
                "policy_accession_id": policy_accession_id,
                "run_provisional_ids": self.run_accession_ids,
            }
        )
        if response.status_code in VALID_STATUS_CODES:
            dataset_accession_id = [r["accession_id"] for r in response.json()][0]
            logging.info("Successfully registered dataset!")
            return dataset_accession_id
        else:
            error_message = f"""Received status code {response.status_code} with error: {response.text} while 
            attempting to register dataset"""
            logging.error(error_message)
            raise Exception(error_message)

    def _finalize_submission(self) -> None:
        """
        Finalizes the submission
        Endpoint documentation located here:
        https://submission.ega-archive.org/api/spec/#/paths/submissions-accession_id--finalise/post
        """
        timestamp = datetime.now().strftime("%Y-%m-%d")
        logging.info("Attempting to finalize submission")
        response = requests.post(
            url=f"{SUBMISSION_PROTOCOL_API_URL}/submissions/{self.submission_accession_id}/finalise",
            headers=self._headers(),
            json={
                "expected_release_date": timestamp,
            }
        )
        if response.status_code in VALID_STATUS_CODES:
            logging.info(
                f"Successfully finalized submission for submission accession id: {self.submission_accession_id}"
            )
        else:
            error_message = f"""Received status code {response.status_code} with error {response.text} while
            attempting to finalize submission"""
            logging.error(error_message)
            raise Exception(error_message)

    def register_metadata(self):
        # Get the policy accession ID using the policy title provided bu the user
        policy_accession_id = self._get_policy_accession_id()
        # If the policy accession is successfully collected, conditionally register the dataset if it doesn't already
        # exist
        if policy_accession_id:
            dataset_accession_id = self._conditionally_create_dataset(policy_accession_id)
            # If the dataset gets successfully created, finalize the submission
            if dataset_accession_id:
                self._finalize_submission()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="This script will upload dataset metadata and finalize a submissions after all experiment and run "
                    "metadata has been loaded"
    )
    parser.add_argument(
        "-submission_accession_id",
        required=True,
        help="The submission accession ID"
    )
    parser.add_argument(
        "-user_name",
        required=True,
        help="The EGA username"
    )
    parser.add_argument(
        "-password",
        required=True,
        help="The EGA password"
    )
    parser.add_argument(
        "-policy_title",
        required=True,
        help="The name of the policy exactly as it was registered for the associated DAC"
    )
    parser.add_argument(
        "-library_strategy",
        required=True,
        help="A list of the experiment library strategies for each sample",
    )
    parser.add_argument(
        "-run_accession_ids",
        required=True,
        help="An array of all run accession IDs that are to be associated with this dataset"
    )
    parser.add_argument(
        "-dataset_title",
        required=False,
        help="The title to be give to the new dataset. If not provided, a default will be used.",
    )
    parser.add_argument(
        "-dataset_description",
        required=False,
        help="The description for the new dataset. If not provided, a default will be used.",
    )

    args = parser.parse_args()

    access_token = LoginAndGetToken(username=args.user_name, password=args.password).login_and_get_token()
    if access_token:
        logging.info("Successfully generated access token. Will continue with dataset registration now.")
        RegisterEgaDatasetAndFinalizeSubmission(
            token=access_token,
            submission_accession_id=args.submission_accession_id,
            policy_title=args.policy_title,
            library_strategy=args.library_strategy,
            run_accession_ids=args.run_accession_ids,
            dataset_title=args.dataset_title if args.dataset_title else None,
            dataset_description=args.dataset_description if args.dataset_description else None,
        ).register_metadata()
