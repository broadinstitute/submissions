import requests
import xmltodict
import xml.etree.ElementTree as ET

class SampleNotFoundError(Exception):
    """Exception raised when a sample is not found."""
    def __init__(self, alias):
        self.alias = alias
        super().__init__(f"Sample with alias '{alias}' not found")

class DbgapTelemetryWrapper:
    def __init__(self, phs_id=None):
        self.endpoint = f"https://www.ncbi.nlm.nih.gov/projects/gap/cgi-bin/GetSampleStatus.cgi?rettype=xml&study_id={phs_id}"
        self.phs_id = phs_id

    def call_telemetry_report(self):
        """Example xml - https://www.ncbi.nlm.nih.gov/projects/gap/cgi-bin/GetSampleStatus.cgi?rettype=xml&study_id=phs000452"""
        response = requests.get(
            self.endpoint, 
            headers={"Content-Type": "application/json"}
        )
        status_code = response.status_code

        return xmltodict.parse(response.text)

    def get_sample_status(self, alias, data_type):
        try:
            telemetry_data = self.call_telemetry_report()

            study_data = telemetry_data["DbGap"]["Study"]
            sample_list = study_data["SampleList"]["Sample"]

            for sample in sample_list:
                if sample.get("@submitted_sample_id") == alias:
                    sra_data = sample["SRAData"]
                    sra_sample_stats = sra_data["Stats"]

                    if isinstance(sra_sample_stats, list):
                        for stat in sra_sample_stats:
                            if stat.get("@experiment_type") == data_type:
                                return stat["@status"]
                    elif isinstance(sra_sample_stats, dict):
                        return sra_sample_stats["@status"]
            
            raise SampleNotFoundError(alias)
 
        except KeyError as e:
            print(f"Error: {e}")
            # Re-raise the exception so we force the wdl to fail
            raise e