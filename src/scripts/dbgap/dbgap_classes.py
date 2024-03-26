import requests
import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime

BROAD_ABBREVIATION = "BI"
NONAMESPACESCHEMALOCATION = "http://www.ncbi.nlm.nih.gov/viewvc/v1/trunk/sra/doc/SRA_1-5/SRA.submission.xsd?view=co"
XSI = "http://www.w3.org/2001/XMLSchema-instance"


class StudyNotRegisteredException(Exception):
    pass


class SampleNotRegisteredException(Exception):
    pass


class Sample:
    DATA_TYPE_MAPPING = {
        "WGS": {
            "constant": "Whole Genome",
            "name": "Whole Genome Sequencing"
        },
        "RNA": {
            "constant": "RNA Seq",
            "name": "RNA Sequencing",
        },
        "WXS": {
            "constant": "Whole Exome",
            "name": "Whole Exome Sequencing"
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

    def __init__(self, json_object, md5):
        sample_json = json_object[0]["attributes"]
        sample_id = json_object[0]['name']
        self._set_sample_attributes(sample_json, sample_id, md5)
        self.set_telemetry_report_info()

    def _set_sample_attributes(self, sample_json, sample_id, md5):
        self.project = sample_json["aggregation_project"]
        self.location = sample_json["location"]
        self.version = sample_json["version"]
        self.md5 = md5
        self.phs = str(sample_json["phs_id"])
        self.data_type = sample_json["data_type"]
        self.alias = sample_json["alias"]
        self.file_type = self._get_file_extension(sample_json["aggregation_path"])
        self.data_file = f"{sample_id}.{self.file_type}"
        self.set_telemetry_report_info()

    @staticmethod
    def _get_file_extension(aggregation_path):
        return aggregation_path.split(".")[-1]

    def set_telemetry_report_info(self):
        def is_bioproject_admin(xml_object):
            return xml_object.attrib['bp_type'] == 'admin'
        
        def is_sample(xml_object):
            return xml_object.attrib['submitted_sample_id'] == self.alias

        root = ET.fromstring(call_telemetry_report(self.phs))
        samples = [x.attrib for x in root.iter('Sample') if is_sample(x)]
        bio_projects = [x.attrib['bp_id'] for x in root.iter('BioProject') if is_bioproject_admin(x)]

        if not samples:
            raise SampleNotRegisteredException('Sample not registered with Dbgap')
        if not bio_projects:
            raise StudyNotRegisteredException('Study not registered with Dbgap')
        if len(samples) > 1:
            raise Exception('Could not find specific sample in report')
        
        self.study = root[0].attrib
        self.bio_project = bio_projects[0]
        self.dbgap_sample_info = samples[0]

    def formatted_data_type(self):
        return self.DATA_TYPE_MAPPING.get(self.data_type, {"constant": "Unknown", "name": "Unknown"})

    def subject_string(self):
        subject_id = self.dbgap_sample_info.get("submitted_subject_id", "")
        return f"from subject '{subject_id}'" if subject_id else ""

    def get_biospecimen_repo(self):
        return self.dbgap_sample_info.get("repository", "")


class ReadGroup:
    def __init__(self, json_objects):
        first_read_group = json_objects[0]["attributes"]
        self._set_constant_values(first_read_group)
        self._set_aggregate_values(json_objects)
        self._set_submission_metadata(first_read_group)

    def _set_submission_metadata(self, first_read_group):
        # submission_metadata can have three different structures. 
        # 1. It will not exist if no samples have the column
        # 2. It can have a dict with keys itemsType , and items. This happens when the metadata is empty, but not for other samples
        # 3. Just has the metadata
        if "submission_metadata" in first_read_group and "items" not in first_read_group["submission_metadata"]:
            # Replace single quotes with double quotes to make it valid JSON
            submission_metadata_str = first_read_group["submission_metadata"].replace("'", "\"")

            # Convert the string to a Python list of dictionaries
            submission_metadata = json.loads(submission_metadata_str)
            self.submission_metadata = self.sub_data_to_dict(submission_metadata)
        else:
            self.submission_metadata = []

    def _set_constant_values(self, first_read_group):
        try:
            self.library_name = first_read_group["library_name"]
            self.library_type = first_read_group["library_type"]
            self.work_request_id = first_read_group["work_request_id"]
            self.analysis_type = first_read_group["analysis_type"]
            self.paired_run = first_read_group["paired_run"]
            self.read_structure = first_read_group["read_structure"]
            self.sample_lsid = first_read_group["sample_lsid"]
            self.reference_sequence = first_read_group["reference_sequence"]
            self.model = first_read_group["model"]
        except KeyError as e:
            raise KeyError(f"Missing required key in read group {e}")

        self.research_project_id = first_read_group.get("research_project_id", "")
        self.bait_set = first_read_group.get("bait_set", "")
        self.sample_barcode = first_read_group.get("sample_barcode")
        self.product_order_id = first_read_group.get("product_order_id", "")
        self.sample_material_type = first_read_group.get("sample_material_type", "")

    @staticmethod
    def sub_data_to_dict(submission_metadata):
        if submission_metadata and len(submission_metadata):
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

    def _set_aggregate_values(self, json_objects):
        # Extract relevant attributes using list comprehension
        attributes_list = [x["attributes"] for x in json_objects]

        # Define helper functions for constructing aggregate values
        def construct_read_group_id(row):
            return f"{row['run_barcode'][:5]}.{row['lane']}"

        def construct_molecular_idx(row):
            return f"{row['molecular_barcode_name']} [{row['molecular_barcode_sequence']}]"

        def construct_rg_platform(row):
            return f"{row['run_barcode']}.{row['lane']}.{row['molecular_barcode_sequence']}"

        def construct_rg_platform_lib(row):
            return f"{construct_rg_platform(row)}.{row['library_name']}"

        # Set comprehensions to generate aggregate values
        self.read_group_ids = {construct_read_group_id(x) for x in attributes_list}
        self.molecular_idx_schemes = {construct_molecular_idx(x) for x in attributes_list}
        self.rg_platform_unit = {construct_rg_platform(x) for x in attributes_list}
        self.rg_platform_unit_lib = {construct_rg_platform_lib(x) for x in attributes_list}

        # Use set comprehension to extract unique values
        self.run_barcode = {x['run_barcode'] for x in attributes_list}
        self.run_name = {x['run_name'] for x in attributes_list}
        self.instrument_names = {x['machine_name'] for x in attributes_list}
        self.flowcell_barcodes = {x['flowcell_barcode'] for x in attributes_list}

    def pairing_code(self):
        return "P" if self.paired_run else "S"

    def is_paired_end(self):
        return "paired-end" if self.paired_run else "single-end"

    def get_pdo_or_wr(self):
        if self.product_order_id is None and self.work_request_id is None:
            raise ValueError("Neither 'product_order_id' nor 'work_request_id' instance variables are set.")

        order_id = self.product_order_id if self.product_order_id else self.work_request_id if self.work_request_id else ""
        return str(order_id)

    def get_library_descriptor(self):
        library_descriptors = {
            "WholeGenomeShotgun": {
                "strategy": {"ncbi_string": "WGS", "humanized_string": "whole genome shotgun"},
                "source": {"ncbi_string": "GENOMIC", "humanized_string": "genomic DNA"},
                "selection": "RANDOM"
            },
            "cDNAShotgunReadTwoSense": {
                "strategy": {"ncbi_string": "RNA_SEQ", "humanized_string": "RNA"},
                "source": {"ncbi_string": "TRANSCRIPTOMIC", "humanized_string": "transcriptome"},
                "selection": "CDNA"
            },
            "cDNAShotgunStrandAgnostic": {
                "strategy": {"ncbi_string": "RNA_SEQ", "humanized_string": "RNA"},
                "source": {"ncbi_string": "TRANSCRIPTOMIC", "humanized_string": "transcriptome"},
                "selection": "CDNA"
            },
            "HybridSelection": {
                "strategy": {"ncbi_string": "WXS", "humanized_string": "random exon"},
                "source": {"ncbi_string": "GENOMIC", "humanized_string": "genomic DNA"},
                "selection": "Hybrid Selection"
            }
        }

        if self.library_type in library_descriptors:
            return library_descriptors[self.library_type]

        if self.library_type in ("cDNAShotgunReadTwoSense", "cDNAShotgunStrandAgnostic"):
            if self.analysis_type == "cDNA" and self.analysis_type != "AssemblyWithoutReference":
                return library_descriptors["cDNAShotgunStrandAgnostic"]

        # Default descriptor if library_type is not found
        return {
            "strategy": {},
            "source": {},
            "selection": ""
        }

    def get_read_length(self):
        reg_expr = re.search("[SBM](\d+)T", self.read_structure)

        return int(reg_expr.group(1)) if reg_expr else 0


class Experiment:
    def __init__(self, sample, read_group):
        self.sample = sample
        self.read_group = read_group

    def get_submitter_id(self):
        pairing_code = self.read_group.pairing_code()
        pdo_or_wr = self.read_group.get_pdo_or_wr()
        formatted_data_type = self.sample.formatted_data_type()["constant"].replace(" ", "_")

        return f"{self.sample.phs}.{pdo_or_wr}.{self.read_group.library_name}.{pairing_code}.{self.sample.alias}.{self.sample.project}.{formatted_data_type}.{self.sample.version}"

    def get_file_name(self):
        return f"{self.get_submitter_id()}.add.experiment.xml"

    def get_title(self):
        repo = self.sample.get_biospecimen_repo()
        library_strategy_string = self.read_group.get_library_descriptor()["strategy"]["humanized_string"]
        library_source_string = self.read_group.get_library_descriptor()["source"]["humanized_string"]
        paired_end = self.read_group.is_paired_end()

        return f"{repo} Illumina {library_strategy_string} sequencing of '{library_source_string}' {paired_end} library '{self.read_group.library_name}' containing sample '{self.sample.alias}' {self.sample.subject_string()}"

    @staticmethod
    def get_read_spec(label, index, base_coord):
        return {
            "read_label": label,
            "read_type": "Forward" if label == "forward" else "Reverse",
            "read_index": index,
            "base_coord": base_coord,
            "read_class": "Application Read"
        }

    def get_spot_length(self):
        return (
            str(self.read_group.get_read_length() * 2)
            if self.read_group.paired_run else str(self.read_group.get_read_length())
        )

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
            kit_str += f" {dict_value.capitalize()} Kit: "
            kit_str += " ".join(f"{key}={value}" for key, value in sub_metadata[dict_value].items())
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

    def set_study_ref(self, experiment):
        study_ref = ET.SubElement(
            experiment,
            "STUDY_REF",
            accession=self.sample.phs
        )

    def set_design(self, experiment):
        design = ET.SubElement(
            experiment,
            "DESIGN"
        )
        ET.SubElement(
            design,
            "DESIGN_DESCRIPTION"
        ).text = self.get_design_description()

        sample_descriptor = ET.SubElement(
            design,
            "SAMPLE_DESCRIPTOR",
            refname=self.sample.alias,
            refcenter=self.sample.phs
        )

        self.set_library_descriptor(design)
        self.set_spot_descriptor(design)

    def set_library_descriptor(self, design):
        library_descriptor = ET.SubElement(design, "LIBRARY_DESCRIPTOR")

        ET.SubElement(library_descriptor, "LIBRARY_NAME").text = self.read_group.library_name
        ET.SubElement(library_descriptor, "LIBRARY_STRATEGY").text = self.read_group.get_library_descriptor()["strategy"]["ncbi_string"]
        ET.SubElement(library_descriptor, "LIBRARY_SOURCE").text = self.read_group.get_library_descriptor()["source"]["ncbi_string"]
        ET.SubElement(library_descriptor, "LIBRARY_SELECTION").text = self.read_group.get_library_descriptor()["selection"]
        layout = ET.SubElement(library_descriptor, "LIBRARY_LAYOUT")
        ET.SubElement(layout, "PAIRED")

    @staticmethod
    def set_spec_values(dict, decode_spec):
        read_spec = ET.SubElement(decode_spec, "READ_SPEC")

        ET.SubElement(read_spec, "READ_INDEX").text = dict["read_index"]
        ET.SubElement(read_spec, "READ_LABEL").text = dict["read_label"]
        ET.SubElement(read_spec, "READ_CLASS").text = dict["read_class"]
        ET.SubElement(read_spec, "READ_TYPE").text = dict["read_type"]
        ET.SubElement(read_spec, "BASE_COORD").text = dict["base_coord"]

    def set_spot_descriptor(self, design):
        spot_descriptor = ET.SubElement(design, "SPOT_DESCRIPTOR")
        decode_spec = ET.SubElement(spot_descriptor, "SPOT_DECODE_SPEC")

        ET.SubElement(decode_spec, "SPOT_LENGTH").text = self.get_spot_length()

        self.set_spec_values(self.get_read_spec("forward", "0", "1"), decode_spec)
        self.set_spec_values(self.get_read_spec("reverse", "1", str(self.read_group.get_read_length() + 1)), decode_spec)

    def set_platform(self, experiment):
        platform = ET.SubElement(experiment, "PLATFORM")
        illumina = ET.SubElement(platform, "ILLUMINA")

        ET.SubElement(illumina, "INSTRUMENT_MODEL").text = self.read_group.model

    def set_experiment_attributes(self, experiment):
        experiment_attrs = ET.SubElement(experiment, "EXPERIMENT_ATTRIBUTES")

        for key, value in self.generate_experiment_attributes().items():
            experiment_attr = ET.SubElement(experiment_attrs, "EXPERIMENT_ATTRIBUTE")

            ET.SubElement(experiment_attr, "TAG").text = key
            ET.SubElement(experiment_attr, "VALUE").text = value

    def create_file(self):
        print("creating experiment xml files")

        root = ET.Element("EXPERIMENT_SET")
        root.set("xsi:noNamespaceSchemaLocation", "http://www.ncbi.nlm.nih.gov/viewvc/v1/trunk/sra/doc/SRA_1-5/SRA.experiment.xsd?view=co")
        root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
        experiment = ET.SubElement(root, "EXPERIMENT")

        self.set_identifiers(experiment)
        ET.SubElement(experiment, "TITLE").text = self.get_title()
        self.set_study_ref(experiment)
        self.set_design(experiment)
        self.set_platform(experiment)
        self.set_experiment_attributes(experiment)

        write_xml_file(self.get_file_name(), root)


class Run:
    def __init__(self, sample, read_group, experiment):
        self.sample = sample
        self.read_group = read_group
        self.experiment = experiment

    def get_submitter_id(self):
        flowcell_barcodes = ".".join(self.read_group.flowcell_barcodes)
        sample_id = self.sample.alias
        return f"{flowcell_barcodes}.{sample_id}.{self.sample.project}.{self.sample.version}.{self.sample.file_type}"

    def get_file_name(self):
        return f"{self.get_submitter_id()}.xml"

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

    @staticmethod
    def create_identifiers(parent, submitter_id):
        identifier = ET.SubElement(parent, "IDENTIFIERS")
        ET.SubElement(identifier, "SUBMITTER_ID", namespace=BROAD_ABBREVIATION).text = submitter_id

    def create_experiment_ref(self, run):
        experiment_ref = ET.SubElement(run, "EXPERIMENT_REF")
        self.create_identifiers(experiment_ref, self.experiment.get_submitter_id())

    def create_data_blocks(self, run):
        data_block = ET.SubElement(run, "DATA_BLOCK")
        files = ET.SubElement(data_block, "FILES")

        ET.SubElement(files, "FILE", filename=self.sample.data_file, filetype=self.sample.file_type,
                      checksum_method="MD5", checksum=self.sample.md5)

    def create_run_attrs(self, run):
        run_attrs = ET.SubElement(run, "RUN_ATTRIBUTES")

        for key, value in self.generate_run_attributes().items():
            run_attr = ET.SubElement(run_attrs, "RUN_ATTRIBUTE")
            ET.SubElement(run_attr, "TAG").text = key
            ET.SubElement(run_attr, "VALUE").text = value

    def create_file(self):
        print("creating run xml files")

        root = ET.Element("RUN_SET")
        root.set("xsi:noNamespaceSchemaLocation", "http://www.ncbi.nlm.nih.gov/viewvc/v1/trunk/sra/doc/SRA_1-5/SRA.run.xsd?view=co")
        root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
        run = ET.SubElement(root, "RUN")

        self.create_identifiers(run, self.get_submitter_id())
        self.create_experiment_ref(run)
        self.create_data_blocks(run)
        self.create_run_attrs(run)

        write_xml_file(self.get_file_name(), root)


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

    @staticmethod
    def get_submission_comment():
        return f"Produced by user picard on {get_submission_comment_formatted_date()} EST {get_run_date().year}"

    def create_actions(self, submission):
        actions = ET.SubElement(submission, "ACTIONS")
        action_protect = ET.SubElement(actions, "ACTION")
        ET.SubElement(action_protect, "PROTECT")
        action_release = ET.SubElement(actions, "ACTION")
        ET.SubElement(action_release, "RELEASE")
        action_experiment = ET.SubElement(actions, "ACTION")
        ET.SubElement(action_experiment, "ADD", source=self.experiment.get_file_name(), schema="experiment")
        print("this is the experiment file name ", self.experiment.get_file_name())
        action_run = ET.SubElement(actions, "ACTION")
        ET.SubElement(action_run, "ADD", source=self.run.get_file_name(), schema="run")
        print("this is the run file name ", self.run.get_file_name())

    @staticmethod
    def create_submission_attributes(submission):
        submission_attributes = ET.SubElement(submission, "SUBMISSION_ATTRIBUTES")
        submission_attribute = ET.SubElement(submission_attributes, "SUBMISSION_ATTRIBUTE")
        ET.SubElement(submission_attribute, "TAG").text = "Submission Site"
        ET.SubElement(submission_attribute, "VALUE").text = "NCBI_PROTECTED"

    def create_file(self):
        print("Creating submission xml file")

        root = ET.Element("SUBMISSION_SET")
        root.set("xsi:noNamespaceSchemaLocation", "http://www.ncbi.nlm.nih.gov/viewvc/v1/trunk/sra/doc/SRA_1-5/SRA.submission.xsd?view=co")
        root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
        submission = ET.SubElement(root, "SUBMISSION", submission_date=get_date(), submission_comment=self.get_submission_comment(), lab_name="Genome Sequencing", alias=self.get_alias(), center_name=BROAD_ABBREVIATION)

        contacts = ET.SubElement(submission, "CONTACTS")
        contact = ET.SubElement(contacts, "CONTACT", name="sra_sumissions", inform_on_status="mailto:dsde-ops@broadinstitute.org", inform_on_error="mailto:dsde-ops@broadinstitute.org")

        self.create_actions(submission)
        self.create_submission_attributes(submission)

        write_xml_file("submission.xml", root)


# Helper Functions #
def write_xml_file(file_name, root):
    file_path = f"/cromwell_root/xml/{file_name}"
    with open(file_path, 'wb') as xfile:
        xfile.write(ET.tostring(root, encoding="ASCII"))


def get_submission_comment_formatted_date():
    return datetime.now().strftime("%A %B %d %H:%M:%S")


def get_date():
    current_datetime = datetime.now()
    date_str = current_datetime.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
    return f"{date_str}-04:00"


def get_run_date():
    return datetime.now()


def call_telemetry_report(phs_id):
    base_url = f"https://www.ncbi.nlm.nih.gov/projects/gap/cgi-bin/GetSampleStatus.cgi?rettype=xml&study_id={phs_id}"
    headers = {"Content-Type": "application/json"}
    response = requests.get(base_url, headers=headers)

    return response.text
