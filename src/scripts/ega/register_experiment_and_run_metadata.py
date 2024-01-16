"""
    After crams have been submitted and validated, this script can be used to register the EXPERIMENT and RUN for
    ONE sample
    It will:
    1) Log in and retrieve access token for the EGA
    2) Use the EGA APIs to:
        a) Register the sample's EXPERIMENT
        b) Register the sample's RUN

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
from pathlib import Path
from typing import Optional
from csv import DictWriter

sys.path.append("./")
from src.scripts.ega.utils import (
    LoginAndGetToken,
    SecretManager,
    SUBMISSION_PROTOCOL_API_URL,
    format_request_header,
    VALID_STATUS_CODES,
    get_file_metadata_for_all_files_in_inbox,
)
from src.scripts.ega import (
    LIBRARY_LAYOUT,
    LIBRARY_STRATEGY,
    LIBRARY_SOURCE,
    LIBRARY_SELECTION,
    RUN_FILE_TYPE,
    INSTRUMENT_MODEL_MAPPING,
)

logging.basicConfig(
    format="%(levelname)s: %(asctime)s : %(message)s", level=logging.INFO
)


class RegisterEgaExperimentsAndRuns:

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
            sample_id: str,
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
        self.insert_size = float(insert_size)
        self.standard_deviation = standard_deviation
        self.sample_material_type = sample_material_type
        self.sample_id = sample_id
        self.library_construction_protocol = library_construction_protocol

    def _headers(self) -> dict:
        return format_request_header(self.token)

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
        if response.status_code in VALID_STATUS_CODES:
            all_experiments = response.json()
            for experiment in all_experiments:
                if (self.study_accession_id == experiment["study_accession_id"]
                        and design_description == experiment["design_description"]):
                    logging.info(f"Found experiment with description {design_description} already. Won't re-create it!")
                    return experiment["provisional_id"]
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
        logging.info(f"Checking to see if experiment {design_description} already exists...")
        if provisional_id := self._experiment_exists(design_description=design_description):
            return provisional_id

        logging.info("Experiment did not already exist. Attempting to create it now!")
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
        if response.status_code in VALID_STATUS_CODES:
            logging.info(f"Response from creating the experiment {response.json()}")
            provisional_id = [
                experiment["provisional_id"] for experiment in response.json()
                if experiment["design_description"] == design_description
            ][0]
            logging.info(f"Successfully created experiment with provisional id: {provisional_id}")
            return provisional_id
        else:
            error_message = f"""Received status code {response.status_code} with error: {response.text} while 
            attempting to register experiment"""
            logging.error(error_message)
            raise Exception(error_message)

    def _get_file_metadata_for_files_in_inbox(self) -> Optional[list[dict]]:
        logging.info(
            f"Attempting to collect metadata for all files registered under submissions {self.submission_accession_id}"
        )
        return get_file_metadata_for_all_files_in_inbox(headers=self._headers())

    def _get_metadata_for_registered_sample(self) -> Optional[dict]:
        """
        Gets all samples associated with the submission
        Endpoint documentation located here:
        https://submission.ega-archive.org/api/spec/#/paths/submissions-accession_id--samples/get
        """
        logging.info(
            f"Collecting metadata for all registered samples in submission with accession "
            f"id {self.submission_accession_id}"
        )

        response = requests.get(
            url=f"{SUBMISSION_PROTOCOL_API_URL}/submissions/{self.submission_accession_id}/samples",
            headers=self._headers(),
        )
        if response.status_code in VALID_STATUS_CODES:
            registered_samples = response.json()

            for a in registered_samples:
                if a["alias"] == self.sample_alias:
                    logging.info(f"Found sample {self.sample_alias} in registered samples metadata! Continuing.")
                    return {
                            "sample_alias": a["alias"],
                            "sample_provisional_id": a["provisional_id"]
                        }
            logging.error(
                f"Could not find {self.sample_alias} in registered sample metadata. It could be that the sample "
                f"wasn't registered ahead of time, or it was registered with a different alias. We won't be able to "
                f"register a run for sample {self.sample_alias}"
            )
            raise Exception("Expected to find 1 sample registered. Instead found none.")

        else:
            error_message = f"""Received status code {response.status_code} with error: {response.text} while
                         attempting to query sample accession IDs"""
            raise Exception(error_message)

    def _run_exists(self, experiment_provisional_id: str, sample_metadata: dict) -> Optional[int]:
        """
        Collects information on all runs in submission
        Endpoint documentation located here:
        https://submission.ega-archive.org/api/spec/#/paths/submissions-accession_id--runs/get
        """
        logging.info("Collecting information about existing runs in submission...")

        response = requests.get(
            url=f"{SUBMISSION_PROTOCOL_API_URL}/submissions/{self.submission_accession_id}/runs",
            headers=self._headers(),
        )
        if response.status_code in VALID_STATUS_CODES:
            registered_runs = response.json()

            sample_alias = sample_metadata["sample_alias"]
            sample_provisional_id = sample_metadata["sample_provisional_id"]

            for run in registered_runs:
                run_experiment_provisional_id = run["experiment"]["provisional_id"]
                run_sample_provisional_id = run["sample"]["provisional_id"]
                run_sample_alias = run["sample"]["alias"]
                run_provisional_id = run["provisional_id"]

                if (run_experiment_provisional_id == experiment_provisional_id
                        and run_sample_provisional_id == sample_provisional_id
                        and run_sample_alias == sample_alias):
                    logging.info(
                        f"Found a registered run with accession ID {run_provisional_id} for {self.sample_alias}. "
                        f"The run will not be re-created!"
                    )
                    return run_provisional_id
            logging.error(f"Did not find an existing registered run for sample {self.sample_alias}")
            return None

        else:
            error_message = f"""Received status code {response.status_code} with error: {response.text} while
                         attempting to query runs"""
            raise Exception(error_message)

    def _link_files_to_samples(self, file_metadata: list[dict], sample_metadata: dict) -> dict:
        logging.info(f"Found file metadata. Now attempting to link all files associated with {self.sample_alias}")

        files = []

        for file in file_metadata:
            relative_file_path = file["relative_path"]
            file_name = Path(relative_file_path).name
            sample_alias_from_path = Path(file_name).stem

            # There could be multiple files associated with a given sample, so we loop through ALL files and append
            # all the file provisional IDs to a list
            if sample_alias_from_path == self.sample_alias:
                files.append(file["provisional_id"])

        if files:
            logging.info(f"Found {len(files)} associated with sample {self.sample_alias}!")
            sample_metadata["files"] = files
            return sample_metadata
        else:
            raise Exception(
                f"Expected to find at least 1 file associated with sample {self.sample_alias}. Instead found none."
            )

    def _conditionally_register_run(self, experiment_provisional_id: str, sample_metadata: dict) -> Optional[int]:
        """
        Registers the run for the sample
        Endpoint documentation located here:
        https://submission.ega-archive.org/api/spec/#/paths/submissions-accession_id--runs/post
        """
        if run_provisional_id := self._run_exists(
                experiment_provisional_id=experiment_provisional_id, sample_metadata=sample_metadata
        ):
            return run_provisional_id

        # If the run for the sample doesn't already exist, gather the metadat for all files in the submission and
        # link the files to the sample of interest in order to register the run
        file_metadata = self._get_file_metadata_for_files_in_inbox()
        if file_metadata:
            sample_and_file_metadata = self._link_files_to_samples(file_metadata, sample_metadata)

            logging.info(f"Attempting to register run for sample {self.sample_alias} now...")
            response = requests.post(
                url=f"{SUBMISSION_PROTOCOL_API_URL}/submissions/{self.submission_accession_id}/runs",
                headers=self._headers(),
                json={
                    "run_file_type": self.run_file_type,
                    "files": sample_and_file_metadata["files"],
                    "experiment_provisional_id": experiment_provisional_id,
                    "sample_provisional_id": sample_and_file_metadata["sample_provisional_id"],
                }
            )
            if response.status_code in VALID_STATUS_CODES:
                print("json response", response.json())
                run_provisional_id = [a["provisional_id"] for a in response.json()][0]
                logging.info(f"Successfully registered run for sample {self.sample_alias}")
                return run_provisional_id
            else:
                error_message = f"""Received status code {response.status_code} with error: {response.text} while 
                attempting to register run"""
                logging.error(error_message)
                raise Exception(error_message)

    def _write_tsv(self, run_provisional_id: int) -> None:
        logging.info("Writing sample metadata and run provisional id to output file")
        with open("/cromwell_root/sample_id_and_run_provisional_id.tsv", "w") as tsv_file:
            writer = DictWriter(tsv_file, fieldnames=["entity:sample_id", "ega_run_provisional_id"], delimiter='\t')
            writer.writeheader()
            writer.writerow({"entity:sample_id": self.sample_id, "ega_run_provisional_id": run_provisional_id})

    def register_metadata(self):
        """
        Registers experiment and run metadata. Logic is built into the following methods so that any metadata that
        already exists is not attempted to be re-registered, and this script can be run multiple times in case there
        are any transient failures.
        """

        # Register the experiment if it doesn't already exist
        experiment_provisional_id = self._conditionally_create_experiment()

        # Gather the sample accession ID that corresponds to the sample we're trying to register a run for
        sample_metadata = self._get_metadata_for_registered_sample()

        print(f"provisional_id - {experiment_provisional_id}, sample metadata {sample_metadata}")

        if experiment_provisional_id and sample_metadata:
            # Register the run if it doesn't already exist
            run_provisional_id = self._conditionally_register_run(
                experiment_provisional_id=experiment_provisional_id, sample_metadata=sample_metadata
            )

            print("provisional id", run_provisional_id)
            # Write info to a tsv so that it can be written to the Terra data tables
            if run_provisional_id:
                self._write_tsv(run_provisional_id=run_provisional_id)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="This script will upload experiment and run metadata to the EGA after crams have been uploaded "
                    "and validated."
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
        "-instrument_model",
        required=True,
        help="The experiment instrument model",
        choices=[a for a in INSTRUMENT_MODEL_MAPPING.keys()]
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
        "-sample_id",
        required=True,
        help="The sample_id identifier from the terra data table"
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

    password = SecretManager(
        project_id="gdc-submissions",
        secret_id="ega_password",
        version_id=1
    ).get_ega_password_secret()
    access_token = LoginAndGetToken(username=args.user_name, password=password).login_and_get_token()

    if access_token:
        logging.info("Successfully generated access token. Will continue with metadata registration now.")
        RegisterEgaExperimentsAndRuns(
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
            library_construction_protocol=args.construction_protocol,
            sample_id=args.sample_id,
        ).register_metadata()
