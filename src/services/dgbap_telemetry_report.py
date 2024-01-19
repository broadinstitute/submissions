import requests
import json
import logging
import xml.etree.ElementTree as ET

logging.basicConfig(
    format="%(levelname)s: %(asctime)s : %(message)s", level=logging.INFO
)

class DbgapTelemetryWrapper:
    def __init__(self, phs_id=None):
        self.endpoint = f"https://www.ncbi.nlm.nih.gov/projects/gap/cgi-bin/GetSampleStatus.cgi?rettype=xml&study_id={phs_id}"
        self.phs_id = phs_id

    def call_telemetry_report():
        response = requests.get(
            self.endpoint, 
            headers={"Content-Type": "application/json"}
        )
        status_code = response.status_code

        return response.text

    def _is_bioproject_admin(xml_object):
        return xml_object.attrib['bp_type'] == 'admin'
        
    def _is_sample(xml_object):
        return xml_object.attrib['submitted_sample_id'] == self.alias

    def extract_sample_level_info(alias):
        root = ET.fromstring(call_telemetry_report())
        samples = [x.attrib for x in root.iter('Sample') if self._is_sample(x)]
        bio_projects = [x.attrib['bp_id'] for x in root.iter('BioProject') if self._is_bioproject_admin(x)]

        if not samples:
            raise SampleNotRegisteredException('Sample not registered with Dbgap')
        if not bio_projects:
            raise StudyNotRegisteredException('Study not registered with Dbgap')
        if len(samples) > 1:
            raise Exception('Could not find specific sample in report')
        
        return {
            "study": root[0].attrib,
            "bio_project": bio_projects[0],
            "dbgap_sample_info": samples[0]
        }