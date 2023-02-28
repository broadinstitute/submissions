import requests
import xml.etree.ElementTree as ET

class Sample:
    def __init__(self, json_object):
        sample_json = json_object[0]["attributes"]
        # Here we are making the assumption that we are only running once per sample. If we need t
        self.project = sample_json["aggregation_project"]
        self.location = sample_json["location"]
        self.index = sample_json["aggregation_index_path"]
        self.version = sample_json["version"]
        self.md5 = sample_json["md5"]
        self.data_file = sample_json["aggregation_path"]
        self.phs = sample_json["phs_id"]
        self.data_type = sample_json["data_type"]

    # study_info will be a dict of all the values from the telemetry report
    def set_study_info(self, study_info):
        self.study_info = study_info

    def get_study_info(self):
        return self.study_info


class ReadGroup:
    def __init__(self, json_object):
        first_read_group = json_object[0]["attributes"]
        # First we will just use the first json object in the list to set the constant values
        self.product_order_id = first_read_group["product_order_id"]
        self.sample_type = first_read_group["sample_type"]
        self.sample_material_type = first_read_group["sample_material_type"]
        self.library_name = first_read_group["library_name"]
        self.library_type = first_read_group["library_type"]
        self.version = first_read_group["version"]
        self.work_request_id = first_read_group["work_request_id"]
        self.sample_id = first_read_group["sample_id"]
        self.research_project_id = first_read_group["research_project_id"]
        self.analysis_type = first_read_group["analysis_type"]
        self.paired_run = first_read_group["paired_run"]
        self.read_structure = first_read_group["read_structure"]
        self.root_sample_id = first_read_group["root_sample_id"]
        self.product_part_number = first_read_group["product_part_number"]
        self.sample_barcode = first_read_group["sample_barcode"]
        self.sample_lsid = first_read_group["sample_lsid"]

        self.set_aggregate_values(json_object)

    def set_aggregate_values(self, json_object):
        def construct_read_group_id(row):
            return f"{row['run_barcode'][:5]}.{row['lane']}"

        def construct_molecular_idx(row):
            return f"{row['molecular_barcode_name']} {row['molecular_barcode_sequence']}"

        def construct_rg_platform(row):
            return f"{row['run_barcode']}.{row['lane']}.{row['molecular_barcode_sequence']}"

        def construct_rg_platform_lib(row):
            return f"{construct_rg_platform(row)}.{row['library_name']}"

        self.read_group_ids = {construct_read_group_id(x["attributes"]) for x in json_object}
        self.molecular_idx_schemes = {construct_molecular_idx(x["attributes"]) for x in json_object}
        self.rg_platform_unit = {construct_rg_platform(x["attributes"]) for x in json_object}
        self.rg_platform_unit_lib = {construct_rg_platform_lib(x["attributes"]) for x in json_object}

        self.run_barcode = {x["attributes"]["run_barcode"] for x in json_object}
        self.run_name = {x["attributes"]["run_name"] for x in json_object}
        self.instrument_names = {x["attributes"]["machine_name"] for x in json_object}
        self.flowcell_barcodes = {x["attributes"]["flowcell_barcode"] for x in json_object}

def call_telemetry_report(phs_id)
    baseUrl = f"https://www.ncbi.nlm.nih.gov/projects/gap/cgi-bin/GetSampleStatus.cgi"
    parameters = {
        'rettype': 'xml',
        'study_id': 'phs001977.v1.p1'
    }
    headers = {"Content-Type": "application/json"}

    return requests.get(baseUrl, headers=headers, params=parameters)

def get_telemetry_report_info(phs_id):
    def is_bioproject_admin(xml_object):
        if xml_object['bp_type'] == 'admin'

    root = ET.fromstring(call_telemetry_report(phs_id).text)

    study = root[0].attrib
    ioProject = [is_bioproject_admin(x) for x in root.iter('BioProject')]
