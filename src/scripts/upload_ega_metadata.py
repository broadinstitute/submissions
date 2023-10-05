"""
    After crams have been submitted and validated, this script can be used to submit the sample metadata.
    It will:
    1) Log in and retrieve access token for the EGA
    2) Use the EGA APIs to:
        a) Register the sample Experiment
        b) Retrieve the sample's accession ID
        c) Registers the sample Run

   Resources:
    - Schema Map: https://ega-archive.org/submission/metadata/ega-schema/
    - Portal API Submission Overview:
        https://ega-archive.org/submission/metadata/submission/sequencing-phenotype/submitter-portal-api/
    - Submission API Documentation: https://submission.ega-archive.org/api/spec/#/
"""
import sys
import argparse
import requests
from typing import Optional

sys.path.append("./")
from src.scripts.ega_utils import (
    LibraryLayouts,
    LibraryStrategy,
    LibrarySource,
    LibrarySelection,
    RunFileType, INSTRUMENT_MODEL_MAPPING,
)


IDP_URL = "https://idp.ega-archive.org/realms/EGA/protocol/openid-connect/token"
SUBMISSION_PROTOCOL_API_URL = "https://submission.ega-archive.org/api"


class LoginAndGetToken:
    def __init__(self, username: str, password: str) -> None:
        self.username = username
        self.password = password

    def login_and_get_token(self) -> str:
        """Logs in and retrieves access token"""
        response = requests.get(
            url=IDP_URL,
            params={
                "grant_type": "password",
                "client_id": "sp-api",
                "username": self.username,
                "password": self.password,
            }
        )
        if response.status_code == 200:
            token = response.json()["access_token"]
            return token
        raise Exception(
            f"Received status code {response.status_code} with error {response.json()} while attempting to "
            f"get access token"
        )


class CreateExperimentAndRuns:
    # TODO: figure out if the study_provisional_id is required if the study already has an accession id
    # TODO: figure out if the extra_attributes are always required, or if the tag/value only required if passing
    #  extra args
    VALID_STATUS_CODES = [200, 201]

    def __init__(
            self,
            token: str,
            submission_accession_id: str,
            study_accession_id: str,
            design_description: str,
            instrument_model_id: int,
            library_layout: LibraryLayouts,
            library_strategy: LibraryStrategy,
            library_source: LibrarySource,
            library_selection: LibrarySelection,
            run_file_type: RunFileType,
    ):
        self.token = token
        self.submission_accession_id = submission_accession_id
        self.study_accession_id = study_accession_id
        self.design_description = design_description
        self.instrument_model_id = instrument_model_id
        self.library_layout = library_layout
        self.library_strategy = library_strategy
        self.library_source = library_source
        self.library_selection = library_selection
        self.run_file_type = run_file_type

    def _headers(self) -> dict:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}"
        }

    def _create_experiment(self) -> Optional[int]:
        """
        Registers the sample experiment
        Endpoint documentation located here:
        https://submission.ega-archive.org/api/spec/#/paths/submissions-accession_id--experiments/post
        """
        response = requests.post(
            url=f"{SUBMISSION_PROTOCOL_API_URL}/submissions/{self.submission_accession_id}/experiments",
            headers=self._headers(),
            json={
                "design_description": self.design_description,
                "instrument_model_id": self.instrument_model_id,
                "library_layout": self.library_layout,
                "library_strategy": self.library_strategy,
                "library_source": self.library_source,
                "library_selection": self.library_selection,
                "study_accession_id": self.study_accession_id
            }
        )
        if response.status_code in self.VALID_STATUS_CODES:
            experiment_id = response.json()["provisional_id"]
            return experiment_id
        raise Exception(
            f"Received status code {response.status_code} with error: {response.json()} while attempting to "
            f"register experiment"
        )

    def _get_sample_accession_id(self) -> list[int]:
        """
        Retrieves the sample accession ID(s)
        Endpoint documentation located here:
        https://submission.ega-archive.org/api/spec/#/paths/files/get
        """
        response = requests.get(
            url=f"{SUBMISSION_PROTOCOL_API_URL}/files",
            headers=self._headers(),

        )

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
            run_accession_ids = [a["provisional_id"] for a in response.json()]
            return run_accession_ids
        raise Exception(
            f"Received status code {response.status_code} with error: {response.json()} while attempting to "
            f"register experiment"
        )

    def run(self):
        experiment_provisional_id = self._create_experiment()
        sample_accession_id = self._get_sample_accession_id()
        run_accesion_ids = self._create_run(
            experiment_provisional_id=experiment_provisional_id,
            sample_accession_ids=sample_accession_id
        )
        print(run_accesion_ids)


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
        "-password",
        required=True,
        help="The EGA password"
    )
    parser.add_argument(
        "-design_description",
        required=True,
        help="The design description"
    )
    parser.add_argument(
        "-instrument_model_id",
        required=True,
        help="The experiment instrument model ID",
        choices=INSTRUMENT_MODEL_MAPPING.keys()
    )
    # Source: https://github.com/EllenElizabethWinchester/ega-submission/blob/main/Resources/library_layouts.json
    parser.add_argument(
        "-library_layout",
        required=True,
        help="The experiment library layout",
        choices=list(LibraryLayouts)
    )
    # Source: https://github.com/EllenElizabethWinchester/ega-submission/blob/main/Resources/library_strategies.json
    parser.add_argument(
        "-library_strategy",
        required=True,
        help="The experiment library strategy.",
        choices=list(LibraryStrategy)
    )
    # Source: https://github.com/EllenElizabethWinchester/ega-submission/blob/main/Resources/library_sources.json
    parser.add_argument(
        "-library_source",
        required=True,
        help="The experiment library source",
        choices=list(LibrarySource)
    )
    # Source: https://github.com/EllenElizabethWinchester/ega-submission/blob/main/Resources/library_selections.json
    parser.add_argument(
        "-library_selection",
        required=True,
        help="The experiment library selection",
        choices=list(LibrarySelection)
    )
    # Source: https://github.com/EllenElizabethWinchester/ega-submission/blob/main/Resources/run_file_types.json
    parser.add_argument(
        "-run_file_type",
        required=True,
        help="The run file type.",
        choices=list(RunFileType)
    )

    args = parser.parse_args()

    access_token = LoginAndGetToken(username=args.username, password=args.password).login_and_get_token()
    CreateExperimentAndRuns(
        token=access_token,
        submission_accession_id=args.submission_accession_id,
        study_accession_id=args.study_accession_id,
        design_description=args.design_description,
        instrument_model_id=INSTRUMENT_MODEL_MAPPING[args.instrument_model_id],
        library_layout=args.library_layout,
        library_strategy=args.library_strategy,
        library_source=args.library_source,
        library_selection=args.library_selection,
        run_file_type=args.run_file_type,
    ).run()
