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
    LIBRARY_LAYOUT,
    LIBRARY_STRATEGY,
    LIBRARY_SOURCE,
    LIBRARY_SELECTION,
    RUN_FILE_TYPE,
    INSTRUMENT_MODEL,
)
INSTRUMENT_MODEL_MAPPING = {
    "HiSeq X Five": 8,
    "HiSeq X Ten": 9,
    "Illumina Genome Analyzer": 10,
    "Illumina Genome Analyzer II": 11,
    "Illumina Genome Analyzer IIx": 12,
    "Illumina HiScanSQ": 13,
    "Illumina HiSeq 1000": 14,
    "Illumina HiSeq 1500": 15,
    "Illumina HiSeq 2000": 16,
    "Illumina HiSeq 2500": 17,
    "Illumina HiSeq 3000": 18,
    "Illumina HiSeq 4000": 19,
    "Illumina HiSeq X": 20,
    "Illumina iSeq 100": 21,
    "Illumina MiSeq": 22,
    "Illumina MiniSeq": 23,
    "Illumina NovaSeq X": 24,
    "Illumina NovaSeq 6000": 25,
    "NextSeq 500": 26,
    "NextSeq 550": 27,
    "NextSeq 1000": 28,
    "NextSeq 2000": 29,
    "unspecified": 30
}



LOGIN_URL = "https://idp.ega-archive.org/realms/EGA/protocol/openid-connect/token"
SUBMISSION_PROTOCOL_API_URL = "https://submission.ega-archive.org/api"


class LoginAndGetToken:
    def __init__(self, username: str, password: str) -> None:
        self.username = username
        self.password = password

    def login_and_get_token(self) -> Optional[str]:
        """Logs in and retrieves access token"""
        response = requests.post(
            url=LOGIN_URL,
            data={
                "grant_type": "password",
                "client_id": "sp-api",
                "username": self.username,
                "password": self.password,
            }
        )
        if response.status_code == 200:
            token = response.json()["access_token"]
            logging.info("Successfully created access token!")
            return token
        else:
            error_message = f"""Received status code {response.status_code} with error {response.json()} while 
            attempting to get access token"""
            logging.error(error_message)
            raise Exception(error_message)


class RegisterEgaMetadata:
    VALID_STATUS_CODES = [200, 201]

    def __init__(
            self,
            token: str,
            submission_accession_id: str,
            study_accession_id: str,
            instrument_model_id: int,
            library_layout: str,
            library_strategy: str,
            library_source: str,
            library_selection: str,
            run_file_type: str,
            policy_title: str,
            dataset_title: Optional[str],
            dataset_description: Optional[str],
            technology: Optional[str],
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
        self.technology = technology if technology else "ILLUMINA"
        self.dataset_title = (
            dataset_title if dataset_title
            else f"New dataset for Submission {self.submission_accession_id}"
        )
        self.dataset_description = (
            dataset_description if dataset_description
            else f"Please fill out a new description here for submission {self.submission_accession_id}"
        )
        self.policy_title = policy_title

    def _headers(self) -> dict:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}"
        }

    def _get_study_provisional_id(self) -> Optional[int]:
        """
        Gets the study's provisional ID using the study accession ID
        Endpoint documentation located here:
        https://submission.ega-archive.org/api/spec/#/paths/studies-accession_id/get
        """
        response = requests.get(
            url=f"{SUBMISSION_PROTOCOL_API_URL}/studies/{self.study_accession_id}",
            headers=self._headers(),
        )

        if response.status_code in self.VALID_STATUS_CODES:
            study_provisional_id = response.json()["provisional_id"]
            logging.info("Successfully gathered the study provisional ID")
            return study_provisional_id
        else:
            error_message = f"""Received status code {response.status_code} with error: {response.text} while 
            attempting to get study provisional ID"""
            logging.error(error_message)
            raise Exception(error_message)

    def _create_experiment(self, study_provisional_id: int) -> Optional[int]:
        """
        Registers the "experiment"
        Endpoint documentation located here:
        https://submission.ega-archive.org/api/spec/#/paths/submissions-accession_id--experiments/post
        """
        design_description = f"{self.technology} sequencing of Homo sapiens via {self.library_selection}"

        response = requests.post(
            url=f"{SUBMISSION_PROTOCOL_API_URL}/submissions/{self.submission_accession_id}/experiments",
            headers=self._headers(),
            json={
                "design_description": design_description,
                "instrument_model_id": self.instrument_model_id,
                "library_layout": self.library_layout,
                "library_strategy": self.library_strategy,
                "library_source": self.library_source,
                "library_selection": self.library_selection,
                "study_accession_id": self.study_accession_id,
            }
        )
        if response.status_code in self.VALID_STATUS_CODES:
            experiment_provisional_id = response.json()["provisional_id"]
            logging.info(f"Successfully created experiment with id: {experiment_provisional_id}")
            return experiment_provisional_id
        else:
            error_message = f"""Received status code {response.status_code} with error: {response.text} while 
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
            error_message = f"""Received status code {response.status_code} with error: {response.text} while
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
            json={
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
            error_message = f"""Received status code {response.status_code} with error: {response.text} while 
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

    def _create_dataset(self, policy_accession_id: str, run_provisional_ids: list[int]) -> Optional[int]:
        """
        Registers the dataset of runs
        Endpoint documentation located here:
        https://submission.ega-archive.org/api/spec/#/paths/submissions-accession_id--datasets/post
        """

        dataset_type = "Whole genome sequencing" if self.library_strategy == "WGS" else "Exome sequencing"

        response = requests.post(
            url=f"{SUBMISSION_PROTOCOL_API_URL}/submissions/{self.submission_accession_id}/datasets",
            headers=self._headers(),
            json={
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
        response = requests.post(
            url=f"{SUBMISSION_PROTOCOL_API_URL}/submissions/{self.submission_accession_id}/finalise",
            headers=self._headers(),
            json={
                "expected_release_date": timestamp,
            }
        )
        if response.status_code in self.VALID_STATUS_CODES:
            logging.info(
                f"Successfully finalized submission for submission accession id: {self.submission_accession_id}"
            )
        else:
            error_message = f"""Received status code {response.status_code} with error {response.text} while
            attempting to finalize submission"""
            logging.error(error_message)
            raise Exception(error_message)

    def register_metadata(self):
        # Get the study provisional ID
        study_provisional_id = self._get_study_provisional_id()

        if study_provisional_id:
            # Register the experiment
            experiment_provisional_id = self._create_experiment(study_provisional_id)
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
        help="The EGA username"
    )
    parser.add_argument(
        "-password",
        required=True,
        help="The EGA password"
    )
    parser.add_argument(
        "-instrument_model",
        required=True,
        help="The experiment instrument model",
        choices=INSTRUMENT_MODEL
    )
    """Source: https://submission.ega-archive.org/api/spec/#/paths/enums-library_layouts/get"""
    parser.add_argument(
        "-library_layout",
        required=True,
        help="The experiment library layout",
        choices=LIBRARY_LAYOUT
    )
    """Source: https://submission.ega-archive.org/api/spec/#/paths/enums-library_strategies/get"""
    parser.add_argument(
        "-library_strategy",
        required=True,
        help="The experiment library strategy.",
        choices=LIBRARY_STRATEGY
    )
    """Source: https://submission.ega-archive.org/api/spec/#/paths/enums-library_sources/get"""
    parser.add_argument(
        "-library_source",
        required=True,
        help="The experiment library source",
        choices=LIBRARY_SOURCE
    )
    """Source: https://submission.ega-archive.org/api/spec/#/paths/enums-library_selections/get"""
    parser.add_argument(
        "-library_selection",
        required=True,
        help="The experiment library selection",
        choices=LIBRARY_SELECTION
    )
    """Source: https://submission.ega-archive.org/api/spec/#/paths/enums-run_file_types/get"""
    parser.add_argument(
        "-run_file_type",
        required=True,
        help="The run file type.",
        choices=RUN_FILE_TYPE
    )
    parser.add_argument(
        "-technology",
        required=False,
        help="The type of sequencer",
    )
    parser.add_argument(
        "-dataset_title",
        required=False,
        help="The dataset title",
        default="Illumina"
    )
    parser.add_argument(
        "-dataset_description",
        required=False,
        help="The dataset description",
    )
    parser.add_argument(
        "-policy_title",
        required=True,
        help="The title of the policy exactly as it was registered for the DAC"
    )

    args = parser.parse_args()
    access_token = LoginAndGetToken(username=args.user_name, password=args.password).login_and_get_token()
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
            technology=args.technology,
            dataset_title=args.dataset_title,
            dataset_description=args.dataset_description,
            policy_title=args.policy_title,
        ).register_metadata()

