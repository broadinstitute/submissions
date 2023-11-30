"""
    After crams have been submitted and validated, this script can be used to submit the sample metadata.
    It will:
    1) Log in and retrieve access token for the EGA
    2) Use the EGA APIs to:
        a) Register the sample Experiment
        b) Retrieve the sample's accession ID
        c) Registers the sample Run

   Resources:
    - Schema Map:
        https://ega-archive.org/submission/metadata/ega-schema/
    - Portal API Submission Overview:
        https://ega-archive.org/submission/metadata/submission/sequencing-phenotype/submitter-portal-api/
    - Submission API Documentation:
        https://submission.ega-archive.org/api/spec/#/
"""
import logging
import sys
import argparse
import requests
from typing import Optional
from datetime import datetime

sys.path.append("./")
from src.scripts.ega_utils import (
    LoginAndGetToken,
    SecretManager,
    LibraryLayouts,
    LibraryStrategy,
    LibrarySource,
    LibrarySelection,
    RunFileType,
    INSTRUMENT_MODEL_MAPPING,
)


LOGIN_URL = "https://idp.ega-archive.org/realms/EGA/protocol/openid-connect/token"
SUBMISSION_PROTOCOL_API_URL = "https://submission.ega-archive.org/api"

class RegisterEgaMetadata:
    VALID_STATUS_CODES = [200, 201]

    def __init__(
            self,
            token: str,
            submission_accession_id: str,
            study_accession_id: str,
            instrument_model_id: int,
            library_layout: LibraryLayouts,
            library_strategy: LibraryStrategy,
            library_source: LibrarySource,
            library_selection: LibrarySelection,
            run_file_type: RunFileType,
            technology: str,
            dataset_title: str,
            dataset_description: str,
            policy_name: str,
    ):
        self.token = token
        self.submission_accession_id = submission_accession_id
        self.study_accession_id = study_accession_id
        self.instrument_model_id = instrument_model_id
        self.library_layout = library_layout
        self.library_strategy = library_strategy
        self.library_source = library_source
        self.library_selection = library_selection
        self.run_file_type = run_file_type
        self.technology = technology
        self.dataset_title = dataset_title
        self.dataset_description = dataset_description
        self.policy_name = policy_name


    def _headers(self) -> dict:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}"
        }

    def _create_experiment(self) -> Optional[int]:
        """
        Registers the "experiment"
        Endpoint documentation located here:
        https://submission.ega-archive.org/api/spec/#/paths/submissions-accession_id--experiments/post
        """
        design_description = f"{self.technology} sequencing of Homo sapiens via {self.library_selection}"

        response = requests.post(
            url=f"{SUBMISSION_PROTOCOL_API_URL}/submissions/{self.submission_accession_id}/experiments",
            headers=self._headers(),
            data={
                "design_description": design_description,
                "instrument_model_id": self.instrument_model_id,
                "library_layout": self.library_layout,
                "library_strategy": self.library_strategy,
                "library_source": self.library_source,
                "library_selection": self.library_selection,
                "study_accession_id": self.study_accession_id
            }
        )
        if response.status_code in self.VALID_STATUS_CODES:
            experiment_provisional_id = response.json()["provisional_id"]
            logging.info(f"Successfully created experiment with id: {experiment_provisional_id}")
            return experiment_provisional_id
        else:
            error_message = f"""Received status code {response.status_code} with error: {response.json()} while 
            attempting to register experiment"""
            logging.error(error_message)
            raise Exception(error_message)

    def _get_sample_accession_id(self) -> list[int]:
        """
        Retrieves the sample accession ID(s)
        Endpoint documentation located here:
        https://submission.ega-archive.org/api/spec/#/paths/files/get
        """
        # TODO: we need the file format so we know the correct prefix in order to filter on files that correspond to
        #  the one sample (assuming we can filter by the sample_alias here?)
        # NOTE: This should somehow filter for the files that are part of this "submission" so that this only has to
        # be run once
        response = requests.get(
            url=f"{SUBMISSION_PROTOCOL_API_URL}/files",
            headers=self._headers(),
            params={
                "status": "inbox",
                "prefix": "",
            }
        )
        if response.status_code in self.VALID_STATUS_CODES:
            file_provisional_ids = [a["provisional_id"] for a in response.json()]
            logging.info("Successfully retrieved files")
            return file_provisional_ids
        else:
            error_message = f"""Received status code {response.status_code} with error: {response.json()} while
             attempting to get sample accession ids"""
            raise Exception(error_message)

    def _create_run(self, experiment_provisional_id: int, sample_accession_ids: list[int]) -> Optional[list]:
        """
        Registers the run for the sample
        Endpoint documentation located here:
        https://submission.ega-archive.org/api/spec/#/paths/submissions-accession_id--runs/post
        """
        response = requests.post(
            url=f"{SUBMISSION_PROTOCOL_API_URL}/submissions/{self.submission_accession_id}/runs",
            headers=self._headers(),
            data={
                "run_file_type": self.run_file_type,
                "files": sample_accession_ids,
                "experiment_provisional_id": experiment_provisional_id,
            }
        )
        if response.status_code in self.VALID_STATUS_CODES:
            run_provisional_ids = [a["provisional_id"] for a in response.json()]
            logging.info("Successfully registered runs")
            return run_provisional_ids
        else:
            error_message = f"""Received status code {response.status_code} with error: {response.json()} while 
            attempting to register run"""
            raise Exception(error_message)

    def _get_policy_accession_id(self) -> Optional[str]:
        """
        Gets a policy accession ID
        Endpoint documentation located here:
        https://submission.ega-archive.org/api/spec/#/paths/policies/get
        """

        response = requests.get(
            url=f"{SUBMISSION_PROTOCOL_API_URL}/policies",
            headers=self._headers(),
        )
        if response.status_code in self.VALID_STATUS_CODES:
            policy_accession_id = [a["accession_id"] for a in response.json() if a["title"] == self.policy_name]
            if len(policy_accession_id) > 1:
                raise ValueError(
                    f"Expected to find one associated policy, but found {len(policy_accession_id)}"
                )
            logging.info("Successfully retrieved policy DAC")
            return policy_accession_id[0]
        else:
            error_message = f"""Received status code {response.status_code} with error: {response.json()} 
            while attempting to get policy accession ID"""
            logging.error(error_message)
            raise Exception(error_message)

    def _create_dataset(self, policy_accession_id: str, run_provisional_ids: list[int]) -> Optional[int]:
        """
        Registers the dataset of runs
        Endpoint documentation located here:
        https://submission.ega-archive.org/api/spec/#/paths/submissions-accession_id--datasets/post
        """

        wgs = "Whole genome sequencing"
        exome = "Exome sequencing"
        dataset_type = wgs if self.library_strategy == LibraryStrategy.WGS else exome

        response = requests.post(
            url=f"{SUBMISSION_PROTOCOL_API_URL}/submissions/{self.submission_accession_id}/datasets",
            headers=self._headers(),
            data={
                "title": self.dataset_title,
                "description": self.dataset_description,
                "dataset_types": [dataset_type],
                "policy_accession_id": policy_accession_id,
                "run_provisional_ids": run_provisional_ids,
            }
        )
        if response.status_code in self.VALID_STATUS_CODES:
            dataset_provisional_id = [r["provisional_id"] for r in response.json()][0]
            logging.info("Successfully registered dataset!")
            return dataset_provisional_id
        else:
            error_message = f"""Received status code {response.status_code} with error: {response.json()} while 
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
        response = requests.post(
            url=f"{SUBMISSION_PROTOCOL_API_URL}/submissions/{self.submission_accession_id}/finalise",
            headers=self._headers(),
            data={
                "expected_release_date": timestamp,
            }
        )
        if response.status_code in self.VALID_STATUS_CODES:
            logging.info(
                f"Successfully finalized submission for submission accession id: {self.submission_accession_id}"
            )
        else:
            error_message = f"""Received status code {response.status_code} with error {response.json()} while
            attempting to finalize submission"""
            logging.error(error_message)
            raise Exception(error_message)

    def register_metadata(self):
        # Register the experiment
        experiment_provisional_id = self._create_experiment()
        # Gather sample accession IDs
        sample_accession_id = self._get_sample_accession_id()
        # If both successful, create the runs
        if experiment_provisional_id and sample_accession_id:
            run_provisional_ids = self._create_run(
                experiment_provisional_id=experiment_provisional_id,
                sample_accession_ids=sample_accession_id
            )
            # If creating the runs is successful, gather thea appropriate DAC policy info
            policy_accession_id = self._get_policy_accession_id()
            # If the DAC policy is found, create the dataset
            if policy_accession_id and run_provisional_ids:
                dataset_provisional_id = self._create_dataset(
                    policy_accession_id=policy_accession_id,
                    run_provisional_ids=run_provisional_ids
                )
                # If the dataset is created, finalize the submission
                if dataset_provisional_id:
                    self._finalize_submission()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="This script will upload metadata to the EGA after crams have been uploaded and validated."
    )
    parser.add_argument(
        "-submission_accession_id",
        required=True,
        help="The submission accession ID"
    )
    parser.add_argument(
        "-study_accession_id",
        required=True,
        help="The study accession ID"
    )
    parser.add_argument(
        "-user_name",
        required=True,
        help="User's username"
    )
    parser.add_argument(
        "-instrument_model",
        required=True,
        help="The experiment instrument model",
        choices=INSTRUMENT_MODEL_MAPPING.values()
    )
    """Source: https://submission.ega-archive.org/api/spec/#/paths/enums-library_layouts/get"""
    parser.add_argument(
        "-library_layout",
        required=True,
        help="The experiment library layout",
        choices=list(LibraryLayouts)
    )
    """Source: https://submission.ega-archive.org/api/spec/#/paths/enums-library_strategies/get"""
    parser.add_argument(
        "-library_strategy",
        required=True,
        help="The experiment library strategy.",
        choices=list(LibraryStrategy)
    )
    """Source: https://submission.ega-archive.org/api/spec/#/paths/enums-library_sources/get"""
    parser.add_argument(
        "-library_source",
        required=True,
        help="The experiment library source",
        choices=list(LibrarySource)
    )
    """Source: https://submission.ega-archive.org/api/spec/#/paths/enums-library_selections/get"""
    parser.add_argument(
        "-library_selection",
        required=True,
        help="The experiment library selection",
        choices=list(LibrarySelection)
    )
    """Source: https://submission.ega-archive.org/api/spec/#/paths/enums-run_file_types/get"""
    parser.add_argument(
        "-run_file_type",
        required=True,
        help="The run file type.",
        choices=list(RunFileType)
    )
    parser.add_argument(
        "-technology",
        required=False,
        help="The type of sequencer",
        default="ILLUMINA",
    )
    parser.add_argument(
        "-dataset_title",
        required=True,
        help="The dataset title",
    )
    parser.add_argument(
        "-dataset_description",
        required=True,
        help="The dataset description",
    )
    parser.add_argument(
        "-policy_name",
        required=True,
        help="The name of the policy exactly as it was registered for the DAC"
    )

    args = parser.parse_args()
    # TODO: Add DAC info as required param to script input
    password = SecretManager(project_id="gdc-submissions", secret_id="ega_password", version_id=1).get_ega_password_secret()
    access_token = LoginAndGetToken(username=args.username, password=args.password).login_and_get_token()
    if access_token:
        RegisterEgaMetadata(
            token=access_token,
            submission_accession_id=args.submission_accession_id,
            study_accession_id=args.study_accession_id,
            instrument_model_id=INSTRUMENT_MODEL_MAPPING[args.instrument_model],
            library_layout=args.library_layout,
            library_strategy=args.library_strategy,
            library_source=args.library_source,
            library_selection=args.library_selection,
            run_file_type=args.run_file_type,
            technology=args.technolgy,
            dataset_title=args.dataset_title,
            dataset_description=args.dataset_description,
            policy_name=args.policy_name,
        ).register_metadata()
