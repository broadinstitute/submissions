import requests
import json
import uuid
import os
import xml.etree.ElementTree as ET
from datetime import datetime
from ftplib import FTP

BROAD_ABBREVIATION = "BI"
NONAMESPACESCHEMALOCATION = "http://www.ncbi.nlm.nih.gov/viewvc/v1/trunk/sra/doc/SRA_1-5/SRA.submission.xsd?view=co"
XSI = "http://www.w3.org/2001/XMLSchema-instance"

class Sample:
    def __init__(self, json_object):
        # Here we are making the assumption that we are only running once per sample. If we need t
        sample_json = json_object[0]["attributes"]
        self.project = sample_json["aggregation_project"]
        self.location = sample_json["location"]
        self.index = sample_json["aggregation_index_path"]
        self.version = sample_json["version"]
        self.md5 = sample_json["md5"]
        self.data_file = sample_json["aggregation_path"]
        self.phs = str(sample_json["phs_id"])
        self.data_type = sample_json["data_type"]
        self.alias = sample_json["alias"]
        self.set_telemetry_report_info()

    # study_info will be a dict of all the values from the telemetry report
    def set_study_info(self, study_info):
        self.study_info = study_info

    def get_study_info(self):
        return self.study_info

    def set_telemetry_report_info(self):
        def is_bioproject_admin(xml_object):
            return xml_object.attrib['bp_type'] == 'admin'
        
        def is_sample(xml_object):
            return xml_object.attrib['submitted_sample_id'] == self.alias

        root = ET.fromstring(call_telemetry_report(self.phs))
        sample = [x.attrib for x in root.iter('Sample') if is_sample(x)]
        self.study = root[0].attrib
        self.bio_project = [x.attrib['bp_id'] for x in root.iter('BioProject') if is_bioproject_admin(x)][0]

        if not self.study:
            raise Exception('Study not registered with Dbgap')
        if len(sample) == 0:
            raise Exception('Sample not registered with Dbgap')
        if len(sample) > 1:
            raise Exception('Could not find specific sample in report')
        
        self.dbgap_sample_info = sample[0]
        self.center_project_name = root[0].attrib['study_name']
        self.center_name = self.get_center_name()

    def get_center_name(self):
        file_path = "/cromwell_root/temp.xml"
        is_correct_xml_obj = False
        download_bioproject_xml()

        def is_correct_project(elem):
            if elem.attrib["accession"] == self.bio_project:
                return True
            else:
                return False

        def format_name(orgs):
            if "owner" in orgs:
                return orgs["owner"]
            elif "participant" in orgs:
                return orgs["participant"]
            else:
                print("Housten we have a problem. We couldnt find an organization for this bioproject")

                return ""

        for event, elem in ET.iterparse(file_path, events=("start",)):
            if elem.tag == "ArchiveID":
                is_correct_xml_obj = is_correct_project(elem)

            if is_correct_xml_obj and elem.tag == "Submission":
                orgs = {}
                description_elements = elem[0]

                for child in description_elements:
                    if child.tag == "Organization":
                        role = child.attrib["role"]
                        name = child[0]

                        if name.text:
                            orgs[role] = name.text
                        else:
                            orgs[role] = name.attrib["attr"]

                return format_name(orgs)

    def formatted_data_type(self):
        DATA_TYPE_MAPPING = {
            "WGS": {
                "constant": "Whole Genome",
                "name": "Whole Genome Sequencing"
            },
            "RNA": {
                "constant": "RNA Seq",
                "name": "RNA Sequencing",
            },
            "Exome": {
                "constant": "Whole Exome",
                "name": "Whole Exome Sequencing"
            },
            "Custom_Selection": {
                "constant": "Custom_Selection",
                "name": "Genomic Sequencing for Select Targets of Interest"
            },
            "N/A": {
                "constant": "Unknown",
                "name": "Unknown"
            }
        }

        return DATA_TYPE_MAPPING[self.data_type]

    def subject_string(self):
        subject_id = self.dbgap_sample_info["submitted_subject_id"]

        if subject_id:
            return f"from subject '{subject_id}'"
        else:
            return ""

    def get_biospecimen_repo(self):
        return self.dbgap_sample_info["repository"]

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
        self.sample_barcode = first_read_group.get("sample_barcode")
        self.sample_lsid = first_read_group["sample_lsid"]
        self.primary_disease = first_read_group.get("primary_disease")
        self.reference_sequence = first_read_group["reference_sequence"]
        self.bait_set = first_read_group["bait_set"]
        self.model = first_read_group["model"]
        self.nominal_length = str(first_read_group["mean_insert_size"])
        self.nominal_sdex = str(first_read_group["standard_deviation"])
        self.submission_metadata = self.sub_data_to_dict(first_read_group["submission_metadata"]["items"])
        self.set_aggregate_values(json_object)

    def sub_data_to_dict(self, submissionMetadata):
        if submissionMetadata and len(submissionMetadata):
            library_construction = {}
            target_capture = {}
            for read in submission_metadata:
                if "library" in read["key"]:
                    library_construction[read["key"]] = read["value"] if read["value"] else ""
                else:
                    target_capture[read["key"]] = read["value"] if read["value"] else ""

            return {
                "library_construction": library_construction,
                "target_capture": target_capture
            }
        else:
            return None


    def set_aggregate_values(self, json_object):
        def construct_read_group_id(row):
            return f"{row['run_barcode'][:5]}.{row['lane']}"

        def construct_molecular_idx(row):
            return f"{row['molecular_barcode_name']} [{row['molecular_barcode_sequence']}]"

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

    def pairing_code(self):
        if self.paired_run:
            return "P"
        else:
            return "S"

    def is_paired_end(self):
        if self.paired_run:
            return "paired-end"
        else:
            return "single-end"

    def get_pdo_or_wr(self):
        if self.product_order_id:
            return self.product_order_id
        elif work_request_id:
            return self.work_request_id
        else:
            return ""

    def get_library_descriptor(self):
        library_descriptor = {
            "strategy": {},
            "source": {}
        }

        if self.library_type == "WholeGenomeShotgun":
            library_descriptor["strategy"] = {
                "ncbi_string": "WGS",
                "humanized_string": "whole genome shotgun"
            }
            library_descriptor["source"] = {
                "ncbi_string": "GENOMIC",
                "humanized_string": "genomic DNA"
            }
            library_descriptor["selection"] = "random"
        elif (self.library_type == "cDNAShotgunReadTwoSense" or self.library_type == "cDNAShotgunStrandAgnostic" or
              self.analysis_type == "cDNA") and self.analysis_type != "AssemblyWithoutReference":
            library_descriptor["strategy"] = {
                "ncbi_string": "RNA_SEQ",
                "humanized_string": "RNA"
            }
            library_descriptor["source"] = {
                "ncbi_string": "TRANSCRIPTOMIC",
                "humanized_string": "transcriptome"
            }
            library_descriptor["selection"] = "cDNA"
        elif self.library_type == "HybridSelection":
            library_descriptor["strategy"] = {
                "ncbi_string": "WXS",
                "humanized_string": "random exon"
            }
            library_descriptor["source"] = {
                "ncbi_string": "GENOMIC",
                "humanized_string": "genomic DNA"
            }
            library_descriptor["selection"] = "Hybrid Selection"

        return library_descriptor

    def get_read_length(self):
        if self.read_structure:
            return int(self.read_structure.split("T")[0])
        else:
            raise Exception(f'read structure not populated for read {self.root_sample_id}')


class Experiment:
    def __init__(self, sample, read_group):
        self.sample = sample
        self.read_group = read_group
        self.uuid = create_random_uuid()

    def get_submitter_id(self):
        pairing_code = self.read_group.pairing_code()
        pdo_or_wr = self.read_group.get_pdo_or_wr()
        formatted_data_type = self.sample.formatted_data_type()["constant"].replace(" ", "_")

        return f"{self.sample.phs}.{pdo_or_wr}.{self.read_group.library_name}.{pairing_code}.{self.sample.alias}.{self.sample.project}.{formatted_data_type}.{self.sample.version}"

    def get_title(self):
        repo = self.sample.get_biospecimen_repo()
        library_strategy_string = self.read_group.get_library_descriptor()["strategy"]["humanized_string"]
        library_source_string = self.read_group.get_library_descriptor()["source"]["humanized_string"]
        paired_end = self.read_group.is_paired_end()

        return f"{repo} Illumina {library_strategy_string} sequencing of '{library_source_string}' {paired_end} library '{self.read_group.library_name}' containing sample '{self.sample.alias}' {self.sample.subject_string()}"

    def get_read_spec_forward(self):
        return {
            "read_label": "forward",
            "read_type": "Forward",
            "read_index": "0",
            "base_coord": "1",
            "read_class": "Application Read"
        }

    def get_read_spec_reverse(self):
        return {
            "read_label": "reverse",
            "read_type": "Reverse",
            "read_index": "1",
            "base_coord": str(self.read_group.get_read_length() + 1),
            "read_class": "Application Read"
        }

    def get_spot_length(self):
        if self.read_group.paired_run:
            return str(self.read_group.get_read_length() * 2)
        else:
            return str(self.read_group.get_read_length())

    # could consolidate some of the next two functions
    def generate_experiment_attributes(self):
        attributes_dict = {
            "aggregation_project": self.sample.project,
            "analysis_type": self.read_group.analysis_type,
            "library": self.read_group.library_name,
            "library_type": self.read_group.library_type,
            "lsid": self.read_group.sample_lsid,
            "material_type": self.read_group.sample_material_type,
            "project": self.sample.project,
            "research_project": self.read_group.research_project_id,
            "target_set": self.read_group.bait_set,
            "work_request_or_pdo": self.read_group.get_pdo_or_wr()
        }
        if self.read_group.sample_barcode and str(self.read_group.sample_barcode) != "":
            attributes_dict["gssr_id"] = str(self.read_group.sample_barcode)

        return attributes_dict

    def kit_construction(self, dict_value):
        kit_str = ""
        sub_metadata = self.read_group.submission_metadata

        if sub_metadata:
            if dict_value == "library_construction":
                kit_str += " Library Preparation Kit: "
            else:
                kit_str += " Target Capture Kit: "

            for key, value in sub_metadata[dict_value].items():
                kit_str += f"{key}={value}"

            kit_str += "."

        return kit_str

    def get_design_description(self):
        selection = self.read_group.get_library_descriptor()["selection"]
        library_description = f"Illumina sequencing of Homo sapiens via {selection}"
        library_construction = self.kit_construction('library_construction')
        target_construction = self.kit_construction('target_capture')

        return f"{library_description}{library_construction}{target_construction}"

    def set_identifiers(self, experiment):
        identifier = ET.SubElement(experiment, "IDENTIFIERS")
        ET.SubElement(
            identifier, 
            "SUBMITTER_ID",
            namespace=BROAD_ABBREVIATION
        ).text = self.get_submitter_id()
        print("submitterid", self.get_submitter_id())
        print("uuid", self.uuid)
        ET.SubElement(identifier, "UUID").text = self.uuid

    def set_study_ref(self, experiment):
        study_ref = ET.SubElement(experiment, "STUDY_REF")
        identifiers = ET.SubElement(study_ref, "IDENTIFIERS")

        ET.SubElement(
            identifiers, 
            "EXTERNAL_ID",
            namespace="bioproject"
        ).text = self.sample.bio_project
        
        ET.SubElement(
            identifiers, 
            "EXTERNAL_ID",
            namespace="gap"
        ).text = self.sample.phs

        ET.SubElement(
            identifiers, 
            "EXTERNAL_ID",
            namespace=self.sample.center_name,
            label=self.sample.center_project_name
        ).text = self.sample.phs

    def set_design(self, experiment):
        ET.SubElement(
            experiment, 
            "DESIGN_DESCRIPTION" 
        ).text = self.get_design_description()

        sample_descriptor = ET.SubElement(experiment, "SAMPLE_DESCRIPTOR")
        identifiers = ET.SubElement(sample_descriptor, "IDENTIFIERS")
        ET.SubElement(
            identifiers, 
            "EXTERNAL_ID",
            namespace="biosample"
        ).text = self.sample.dbgap_sample_info["sra_sample_id"]

        ET.SubElement(
            identifiers, 
            "EXTERNAL_ID",
            namespace=self.sample.phs,
            label=self.sample.dbgap_sample_info["repository"]
        ).text = self.sample.dbgap_sample_info["submitted_sample_id"]

    def set_library_descriptor(self, experiment):
        library_descriptor = ET.SubElement(experiment, "LIBRARY_DESCRIPTOR")

        ET.SubElement(library_descriptor, "LIBRARY_NAME").text = self.read_group.library_name
        ET.SubElement(library_descriptor, "LIBRARY_STRATEGY").text = self.read_group.get_library_descriptor()["strategy"]["ncbi_string"]
        ET.SubElement(library_descriptor, "LIBRARY_SOURCE").text = self.read_group.get_library_descriptor()["source"]["ncbi_string"]
        ET.SubElement(library_descriptor, "LIBRARY_SELECTION").text = self.read_group.get_library_descriptor()["selection"]
        layout = ET.SubElement(library_descriptor, "LIBRARY_LAYOUT")
        ET.SubElement(layout, "PAIRED", NOMINAL_LENGTH=self.read_group.nominal_length, NOMINAL_SDEV=self.read_group.nominal_sdex)

    def set_spec_values(self, dict, decode_spec):
        read_spec = ET.SubElement(decode_spec, "READ_SPEC")

        ET.SubElement(read_spec, "READ_INDEX").text = dict["read_index"]
        ET.SubElement(read_spec, "READ_LABEL").text = dict["read_label"]
        ET.SubElement(read_spec, "READ_CLASS").text = dict["read_class"]
        ET.SubElement(read_spec, "READ_TYPE").text = dict["read_type"]
        ET.SubElement(read_spec, "READ_COORD").text = dict["base_coord"]

    def set_spot_descriptor(self, experiment):
         spot_descriptor = ET.SubElement(experiment, "SPOT_DESCRIPTOR")
         decode_spec = ET.SubElement(spot_descriptor, "SPOT_DECODE_SPEC")

         ET.SubElement(decode_spec, "SPOT_LENGTH").text = self.get_spot_length()
         read_spec = ET.SubElement(decode_spec, "READ_SPEC")

         self.set_spec_values(self.get_read_spec_forward(), read_spec)
         self.set_spec_values(self.get_read_spec_reverse(), read_spec)

    def set_platform(self, experiment):
        illumina = ET.SubElement(experiment, "ILLUMINA")

        ET.SubElement(illumina, "INSTRUMENT_MODEL").text = self.read_group.model

    def set_experiment_attributes(self, experiment):
        experiment_attrs = ET.SubElement(experiment, "EXPERIMENT_ATTRIBUTES")

        for key, value in self.generate_experiment_attributes().items():
            experiment_attr = ET.SubElement(experiment_attrs, "EXPERIMENT_ATTRIBUTE")

            ET.SubElement(experiment_attr, "TAG").text = key
            ET.SubElement(experiment_attr, "VALUE").text = value

    def create_file(self):
        print("creating experiment xml files")

        root = ET.Element(
            "EXPERIMENT_SET",
            noNamespaceSchemaLocation=NONAMESPACESCHEMALOCATION,
            xsi=XSI
        )
        experiment = ET.SubElement(root, "EXPERIMENT")

        self.set_identifiers(experiment)
        ET.SubElement(experiment, "TITLE").text = self.get_title()
        self.set_study_ref(experiment)
        self.set_design(experiment)
        self.set_library_descriptor(experiment)
        self.set_spot_descriptor(experiment)
        self.set_platform(experiment)
        self.set_experiment_attributes(experiment)

        write_xml_file("experiment", root)


class Run:
    def __init__(self, sample, read_group, experiment):
        self.sample = sample
        self.read_group = read_group
        self.experiment = experiment
        self.uuid = create_random_uuid()

    def file_type(self):
        return self.sample.data_file.split(".")[-1]

    def get_submitter_id(self):
        flowcell_barcodes = ".".join(self.read_group.flowcell_barcodes)
        sample_id = self.sample.alias

        return f"{flowcell_barcodes}.{sample_id}.{self.sample.project}.{self.sample.version}.{self.file_type()}"

    
    def generate_run_attributes(self):
        attributes_dict = {
            "aggregation_project": self.sample.project,
            "analysis_type": self.read_group.analysis_type,
            "assembly": self.read_group.reference_sequence[16:39],
            "bait_set": self.read_group.bait_set,
            "data_type": self.sample.data_type,
            "flowcell_barcode": ", ".join(self.read_group.flowcell_barcodes),
            "instrument_name": ", ".join(self.read_group.instrument_names),
            "library": self.read_group.library_name,
            "library_type": self.read_group.library_type,
            "lsid": self.read_group.sample_lsid,
            "molecular_idx_scheme": ", ".join(self.read_group.molecular_idx_schemes),
            "read_group_id": ", ".join(self.read_group.read_group_ids),
            "research_project": self.read_group.research_project_id,
            "rg_platform_unit": ", ".join(self.read_group.rg_platform_unit),
            "rg_platform_unit_lib": ", ".join(self.read_group.rg_platform_unit_lib),
            "run_barcode": ", ".join(self.read_group.run_barcode),
            "run_name": ", ".join(self.read_group.run_name),
            "work_request_or_pdo": self.read_group.get_pdo_or_wr()
        }

        return attributes_dict

    def create_identifiers(self, parent, submitter_id, uuid):
        identifier = ET.SubElement(parent, "IDENTIFIERS")

        ET.SubElement(identifier, "SUBMITTER_ID").text = submitter_id
        ET.SubElement(identifier, "UUID").text = uuid

    def create_experiment_ref(self, run):
        experiment_ref = ET.SubElement(run, "EXPERIMENT_REF")

        self.create_identifiers(experiment_ref, self.experiment.get_submitter_id(), self.experiment.uuid)

    def create_data_blocks(self, run):
        data_block = ET.SubElement(run, "DATA_BLOCK")
        files = ET.SubElement(data_block, "FILES")

        ET.SubElement(
            data_block, 
            "FILE",
            file_name=self.sample.data_file,
            file_type=self.file_type(),
            checksum_method="MD5",
            checksum=self.sample.md5,
        )

    def create_run_attrs(self, run):
        run_attrs = ET.SubElement(run, "RUN_ATTRIBUTES")

        for key, value in self.generate_run_attributes().items():
            run_attr = ET.SubElement(run_attrs, "RUN_ATTRIBUTE")

            ET.SubElement(run_attr, "TAG").text = key
            ET.SubElement(run_attr, "VALUE").text = value

    def create_file(self):
        print("creating run xml files")

        root = ET.Element(
            "RUN_SET",
            noNamespaceSchemaLocation=NONAMESPACESCHEMALOCATION,
            xsi=XSI
        )
        run = ET.SubElement(
            root, 
            "RUN",
            run_date=get_date(),
            run_center=BROAD_ABBREVIATION
        )

        self.create_identifiers(run, self.get_submitter_id(), self.uuid)
        self.create_experiment_ref(run)
        self.create_data_blocks(run)
        self.create_run_attrs(run)

        write_xml_file("run", root)

class Submission:
    def __init__(self, experiment, run, phs):
        self.phs = str(phs)
        self.experiment = experiment
        self.run = run
        self.name = "sra_submissions"
        self.lab_name = "Genome Sequencing"
        self.ncbi_protected = "NCBI_PROTECTED"
        self.submission_site = "Submission Site"

    def get_alias(self):
        return f"{BROAD_ABBREVIATION}.{self.phs}.{get_run_date().year}"

    def get_submission_comment(self):
        return f"Produced by user picard on {get_submission_comment_formatted_date()} EST {get_run_date().year}"

    def create_actions(self, submission):
        actions = ET.SubElement(submission, "ACTIONS")
        action_protect = ET.SubElement(
            actions,
            "ACTION"
        )
        ET.SubElement(
            action_protect,
            "PROTECT"
        )
        action_release = ET.SubElement(
            actions,
            "ACTION"
        )
        ET.SubElement(
            action_release,
            "RELEASE"
        )
        action_experiment = ET.SubElement(
            actions,
            "ACTION"
        )
        ET.SubElement(
            action_experiment,
            "ADD",
            source=f"{self.experiment.get_submitter_id()}.add.experiment.xml",
            schema="experiment"
        )
        action_run = ET.SubElement(
            actions,
            "ACTION"
        )
        ET.SubElement(
            action_run,
            "ADD",
            source=f"{self.run.get_submitter_id()}.add.run.xml",
            schema="run"
        )

    def create_submission_attributes(self, submission):
        submission_attributes = ET.SubElement(submission, "SUBMISSION_ATTRIBUTES")
        submission_attribute = ET.SubElement(submission_attributes, "SUBMISSION_ATTRIBUTE")
        ET.SubElement(submission_attribute, "TAG").text = "Submission Site"
        ET.SubElement(submission_attribute, "VALUE").text = "NCBI_PROTECTED"

    def create_file(self):
        print("Creating submission xml file")

        root = ET.Element(
            "SUBMISSION_SET",
            noNamespaceSchemaLocation=NONAMESPACESCHEMALOCATION,
            xsi=XSI
        )
        submission = ET.SubElement(
            root, 
            "SUBMISSION", 
            submission_date=get_date(),
            submission_comment=self.get_submission_comment(),
            lab_name="Genome Sequencing",
            alias=self.get_alias(),
            center_name=BROAD_ABBREVIATION
        )

        contacts = ET.SubElement(submission, "CONTACTS")
        contact = ET.SubElement(
            contacts,
            "CONTACT",
            name="sra_sumissions",
            inform_on_status="mailto:dsde-ops@broadinstitute.org",
            inform_on_error="mailto:dsde-ops@broadinstitute.org"
        )

        self.create_actions(submission)
        self.create_submission_attributes(submission)

        write_xml_file("submission", root)

################### Helper Function ####################

def download_bioproject_xml():
    ftp = FTP('ftp.ncbi.nlm.nih.gov')
    ftp.login("anonymous", None)
    ftp.cwd('bioproject')

    with open('./cromwell_root/bioproject.xml', 'wb') as fp:
        ftp.retrbinary('RETR bioproject.xml', fp.write)

def write_xml_file(file_name, root):
    with open(f"./cromwell_root/xml/{file_name}.xml", 'wb') as xfile:
        xfile.write(ET.tostring(root, encoding="ASCII"))

def get_submission_comment_formatted_date():
    return datetime.strftime(datetime.now(), "%A %B %d %H:%M:%S")

def get_date():
    return f"{str(datetime.now().date())}T{datetime.strftime(datetime.now(), '%H:%M:%S')}-5:00"

def get_run_date():
    return datetime.now()

def create_random_uuid():
    return str(uuid.uuid1())

def call_telemetry_report(phs_id):
    baseUrl = f"https://www.ncbi.nlm.nih.gov/projects/gap/cgi-bin/GetSampleStatus.cgi?rettype=xml&study_id={phs_id}.v1.p1"
    headers = {"Content-Type": "application/json"}
    response = requests.get(baseUrl, headers=headers)
    status_code = response.status_code

    return response.text

