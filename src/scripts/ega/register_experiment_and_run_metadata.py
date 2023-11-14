"""
    After crams have been submitted and validated, this script can be used to register the EXPERIMENT and RUN for
    ONE sample
    It will:
    1) Log in and retrieve access token for the EGA
    2) Use the EGA APIs to:
        a) Register the sample's EXPERIMENT
        c) Register the sample's RUN

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
from pathlib import Path
from typing import Optional

sys.path.append("../")
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
            sample_alias: str,
            library_name: str,
            insert_size: float,
            standard_deviation: float,
            sample_material_type: str,
            library_construction_protocol: str,
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
        self.sample_alias = sample_alias
        self.library_name = library_name
        self.insert_size = insert_size
        self.standard_deviation = standard_deviation
        self.sample_material_type = sample_material_type
        self.library_construction_protocol = library_construction_protocol

    def _headers(self) -> dict:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}"
        }

    def _experiment_exists(self, design_description: str) -> Optional[str]:
        """
        Gets existing experiments in the submission
        Endpoint documentation located here:
        https://submission.ega-archive.org/api/spec/#/paths/submissions-accession_id--datasets/get
        """

        response = requests.get(
            url=f"{SUBMISSION_PROTOCOL_API_URL}/submissions/{self.submission_accession_id}/experiments",
            headers=self._headers(),
        )
        if response.status_code in self.VALID_STATUS_CODES:
            all_experiments = response.json()
            for experiment in all_experiments:
                if (self.study_accession_id == experiment["study_accession_id"]
                        and design_description == experiment["design_description"]):
                    logging.info(f"Found experiment with description {design_description} already. Won't re-create it!")
                    return experiment["accession_id"]
                return None
        else:
            error_message = f"""Received status code {response.status_code} with error: {response.text} while 
                        attempting to query existing experiments"""
            logging.error(error_message)
            raise Exception(error_message)

    def _conditionally_create_experiment(self) -> Optional[str]:
        """
        Registers the "experiment"
        Endpoint documentation located here:
        https://submission.ega-archive.org/api/spec/#/paths/submissions-accession_id--experiments/post
        """
        paired_end_string = "paired-end" if self.library_layout == "PAIRED" else ""
        design_description = (f"{self.technology} {self.library_strategy} sequencing of {self.sample_material_type} "
                              f"{paired_end_string} library via {self.library_selection} containing sample "
                              f"{self.sample_alias}")
        nominal_length = int(self.insert_size) if 0 < self.insert_size < 1000 else 0

        # Query for existing experiments. If the one we're trying to register already exists, skip re-creating it
        if experiment_accession_id := self._experiment_exists(design_description):
            return experiment_accession_id

        response = requests.post(
            url=f"{SUBMISSION_PROTOCOL_API_URL}/submissions/{self.submission_accession_id}/experiments",
            headers=self._headers(),
            json={
                "design_description": design_description,
                "library_name": self.library_name,
                "library_construction_protocol": self.library_construction_protocol,
                "paired_nominal_length": nominal_length,
                "paired_nominal_sdev": self.standard_deviation,
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

    def _get_file_metadata_for_files_in_submission(self) -> Optional[list[dict]]:
        """
        Retrieves the sample accession ID
        Endpoint documentation located here:
        https://submission.ega-archive.org/api/spec/#/paths/files/get
        """
        response = requests.get(
            url=f"{SUBMISSION_PROTOCOL_API_URL}/files",
            headers=self._headers(),
        )
        if response.status_code in self.VALID_STATUS_CODES:
            file_metadata = response.json()
            files_of_interest = [
                f for f in file_metadata if f["submission_accession_id"] == self.submission_accession_id
            ]
            return files_of_interest
        else:
            error_message = f"""Received status code {response.status_code} with error: {response.text} while
             attempting to query for file metadata"""
            raise Exception(error_message)

    def _get_metadata_for_registered_sample(self) -> Optional[dict]:
        """
        Gets all samples associated with the submission
        Endpoint documentation located here:
        https://submission.ega-archive.org/api/spec/#/paths/submissions-accession_id--samples/get
        """

        response = requests.get(
            url=f"{SUBMISSION_PROTOCOL_API_URL}/submissions/{self.submission_accession_id}/samples",
            headers=self._headers(),
        )
        if response.status_code in self.VALID_STATUS_CODES:
            registered_samples = response.json()

            for a in registered_samples:
                if a["alias"] == self.sample_alias:
                    logging.info(f"Found sample {self.sample_alias} in registered samples metadata")
                    return {
                            "sample_alias": a["alias"],
                            "sample_accession_id": a["accession_id"]
                        }
            logging.error(f"Could not find {self.sample_alias} in registered sample metadata")
            return None

        else:
            error_message = f"""Received status code {response.status_code} with error: {response.text} while
                         attempting to query sample accession IDs"""
            raise Exception(error_message)

    def _run_exists(self, experiment_accession_id: str, sample_metadata: dict) -> Optional[str]:
        """
        Collects information on all runs in submission
        Endpoint documentation located here:
        https://submission.ega-archive.org/api/spec/#/paths/submissions-accession_id--runs/get
        """
        response = requests.get(
            url=f"{SUBMISSION_PROTOCOL_API_URL}/{self.submission_accession_id}/runs",
            headers=self._headers(),
        )
        if response.status_code in self.VALID_STATUS_CODES:
            registered_runs = response.json()

            sample_alias = sample_metadata["sample_alias"]
            sample_accession_id = sample_metadata["sample_accession_id"]

            for run in registered_runs:
                run_experiment_accession_id = run["experiment"]["accession_id"]
                run_sample_accession_id = run["sample"]["accession_id"]
                run_sample_alias = run["sample"]["alias"]
                run_accession_id = run["accession_id"]

                if (run_experiment_accession_id == experiment_accession_id
                        and run_sample_accession_id == sample_accession_id
                        and run_sample_alias == sample_alias):
                    logging.info(f"Found a registered run with accession ID {run_accession_id} for {self.sample_alias}")
                    return run_accession_id
            logging.info(f"Did not find a registered run for sample {self.sample_alias}. Will register one now!")
            return None

        else:
            error_message = f"""Received status code {response.status_code} with error: {response.text} while
                         attempting to query runs"""
            raise Exception(error_message)

    @staticmethod
    def _link_files_to_samples(file_metadata: list[dict], sample_metadata: dict) -> dict:
        files = []

        for file in file_metadata:
            relative_file_path = file["relative_path"]
            file_name = Path(relative_file_path).name
            sample_alias_from_path = Path(file_name).stem

            # There could be multiple files associated with a given sample, so we loop through ALL files and append
            # all the file provisional IDs to a list
            if sample_alias_from_path == sample_metadata["sample_alias"]:
                files.append(file["provisional_id"])

        sample_metadata["files"] = files
        return sample_metadata

    def _conditionally_register_run(self, experiment_accession_id: str, sample_metadata: dict) -> Optional[str]:
        """
        Registers the run for the sample
        Endpoint documentation located here:
        https://submission.ega-archive.org/api/spec/#/paths/submissions-accession_id--runs/post
        """
        if run_accession_id := self._run_exists(experiment_accession_id, sample_metadata):
            return run_accession_id

        # If the run for the sample doesn't already exist, gather the metadat for all files in the submission and
        # link the files to the sample of interest in order to register the run
        file_metadata = self._get_file_metadata_for_files_in_submission()
        if file_metadata:
            sample_and_file_metadata = self._link_files_to_samples(file_metadata, sample_metadata)

            response = requests.post(
                url=f"{SUBMISSION_PROTOCOL_API_URL}/submissions/{self.submission_accession_id}/runs",
                headers=self._headers(),
                json={
                    "run_file_type": self.run_file_type,
                    "files": sample_and_file_metadata["files"],
                    "experiment_accession_id": experiment_accession_id,
                    "sample_accession_id": sample_and_file_metadata["sample_accession_id"],
                }
            )
            if response.status_code in self.VALID_STATUS_CODES:
                run_accession_id = [a["accession_id"] for a in response.json()][0]
                logging.info(f"Successfully registered run for sample {self.sample_alias}")
                return run_accession_id
            else:
                error_message = f"""Received status code {response.status_code} with error: {response.text} while 
                attempting to register run"""
                raise Exception(error_message)

    def register_metadata(self):
        """
        Registers experiment and run metadata. Logic is built into the following methods so that any metadata that
        already exists is not attempted to be re-registered, and this script can be run multiple times in case there
        are any transient failures.
        """

        # Register the experiment if it doesn't already exist
        experiment_accession_id = self._conditionally_create_experiment()

        # Gather the sample accession ID that corresponds to the sample we're trying to register a run for
        sample_metadata = self._get_metadata_for_registered_sample()

        if experiment_accession_id and sample_metadata:
            # Register the run if it doesn't already exist
            run_accession_id = self._conditionally_register_run(experiment_accession_id, sample_metadata)


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
        "-sample_alias",
        required=True,
        help="The sample alias to register metadata for"
    )
    parser.add_argument(
        "-library_name",
        required=True,
        help="The library name for the sample of interest",
    )
    parser.add_argument(
        "-mean_insert_size",
        required=True,
        help="The mean insert size for the sample of interest"
    )
    parser.add_argument(
        "-standard_deviation",
        required=True,
        help="The standard deviation for the sample of interest"
    )
    parser.add_argument(
        "-sample_material_type",
        required=True,
        help="The sample material type for the sample of interest"
    )
    parser.add_argument(
        "-construction_protocol",
        required=True,
        help="The library construction protocol",
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
            sample_alias=args.sample_alias,
            library_name=args.library_name,
            insert_size=args.mean_insert_size,
            standard_deviation=args.standard_deviation,
            sample_material_type=args.sample_material_type,
            library_construction_protocol=args.library_construction_protocol,
        ).register_metadata()
