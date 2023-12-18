import requests
import logging
from typing import Optional

LOGIN_URL = "https://idp.ega-archive.org/realms/EGA/protocol/openid-connect/token"
SUBMISSION_PROTOCOL_API_URL = "https://submission.ega-archive.org/api"
VALID_STATUS_CODES = [200, 201]

logging.basicConfig(
    format="%(levelname)s: %(asctime)s : %(message)s", level=logging.INFO
)


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
        if response.status_code in VALID_STATUS_CODES:
            token = response.json()["access_token"]
            print("Successfully created access token!")
            return token
        else:
            error_message = f"""Received status code {response.status_code} with error {response.json()} while 
            attempting to get access token"""
            print(error_message)
            raise Exception(error_message)


def format_request_header(token: str) -> dict:
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }


def get_file_metadata_for_all_files_in_inbox(headers: dict) -> Optional[list[dict]]:
    """
    Retrieves file metadata for all files in the inbox
    Endpoint documentation located here:
    https://submission.ega-archive.org/api/spec/#/paths/files/get
    """

    response = requests.get(
        url=f"{SUBMISSION_PROTOCOL_API_URL}/files",
        headers=headers,
    )
    if response.status_code in VALID_STATUS_CODES:
        file_metadata = response.json()

        if file_metadata:
            return file_metadata
        else:
            raise Exception("Expected to find at least 1 file in the inbox. Instead found none.")

    else:
        error_message = f"""Received status code {response.status_code} with error: {response.text} while
                 attempting to query for file metadata"""
        logging.error(error_message)
        raise Exception(error_message)
