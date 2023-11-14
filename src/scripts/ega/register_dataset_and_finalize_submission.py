
class Foo():

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

    def _create_dataset(self, policy_accession_id: str, run_accession_ids: list[str]) -> Optional[str]:
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
                "run_provisional_ids": run_accession_ids,
            }
        )
        if response.status_code in self.VALID_STATUS_CODES:
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
