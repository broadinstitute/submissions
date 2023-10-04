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

import argparse
import requests
from typing import Optional

from src.scripts.ega_utils import (
    EGA_LIBRARY_STRATEGY_TYPES,
    EGA_LIBRARY_SOURCE_TYPES,
    EGA_LIBRARY_SELECTION_TYPES,
    EGA_LIBRARY_LAYOUT_TYPES
)


IDP_URL = "https://idp.ega-archive.org/realms/EGA/protocol/openid-connect/token"
SUBMISSION_PROTOCOL_URL = "https://submission.ega-archive.org/api"


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
    def __init__(
            self, token: str,
            submission_accession_id: str,
            study_accession_id: str,
            design_description: str,
            instrument_model_id: int,
            library_layout: str,
            library_strategy: str,
            library_source: str,
            library_selection: str,
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

    # TODO: Does this only need to be run once for the experiment, and not once for the sample? Or once per sample?
    def _create_experiment(self) -> Optional[int]:
        """Registers the sample experiment"""
        response = requests.post(
            url=f"{SUBMISSION_PROTOCOL_URL}/submissions/{self.submission_accession_id}/experiments",
            data={
                "design_description": self.design_description,
                "instrument_model_id": self.instrument_model_id,
                "library_layout": self.library_layout,
                "library_strategy": self.library_strategy,
                "library_source": self.library_source,
                "library_selection": self.library_selection,
                "study_accession_id": self.study_accession_id
            }
        )
        if response.status_code == 200:
            experiment_id = response.json()["provisional_id"]
            return experiment_id
        raise Exception(
            f"Received status code {response.status_code} with error: {response.json()} while attempting to "
            f"register experiment"
        )

    # TODO: figure out how to get a sample's accession id
    def _get_sample_accession_id(self):
        """Retrieves the sample accession ID"""
        pass

    def _create_run(self):
        """Registers the run for the sample"""


    def run(self):
        experiment_id = self._create_experiment()
        self._get_sample_accession_id()


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
    # TODO: add a mapping to pull the correct ID based on these pairings: https://github.com/EllenElizabethWinchester/ega-submission/blob/main/Resources/platform_models.json
    parser.add_argument(
        "-instrument_model_id",
        required=True,
        help="The experiment instrument model ID"
    )
    # Source: https://github.com/EllenElizabethWinchester/ega-submission/blob/main/Resources/library_layouts.json
    parser.add_argument(
        "-library_layout",
        required=True,
        help="The experiment library layout",
        choices=EGA_LIBRARY_LAYOUT_TYPES
    )
    # Source: https://github.com/EllenElizabethWinchester/ega-submission/blob/main/Resources/library_strategies.json
    parser.add_argument(
        "-library_strategy",
        required=True,
        help="The experiment library strategy.",
        choices=EGA_LIBRARY_STRATEGY_TYPES
    )
    # Source: https://github.com/EllenElizabethWinchester/ega-submission/blob/main/Resources/library_sources.json
    parser.add_argument(
        "-library_source",
        required=True,
        help="The experiment library source",
        choices=EGA_LIBRARY_SOURCE_TYPES
    )
    # Source: https://github.com/EllenElizabethWinchester/ega-submission/blob/main/Resources/library_selections.json
    parser.add_argument(
        "-library_selection",
        required=True,
        help="The experiment library selection",
        choices=EGA_LIBRARY_SELECTION_TYPES
    )
    # TODO: add a mapping to
    parser.add_argument(
        "-run_file_type",
        required=True,
        help="The run file type.",
        choices=
    )


    args = parser.parse_args()
    access_token = LoginAndGetToken(username=args.username, password=args.password).login_and_get_token()
    CreateExperimentAndRuns(
        token=access_token,
        submission_accession_id=args.submission_accession_id,
        study_accession_id=args.study_accession_id,
        design_description=args.design_description,
        instrument_model_id=args.instrument_model_id,
        library_layout=args.library_layout,
        library_strategy=args.library_strategy,
        library_source=args.library_source,
        library_selection=args.library_selection
    ).run()
