import requests
import json
import re
import os
import xmltodict
from lxml import etree
from io import BytesIO
from datetime import datetime
from src.services.dbgap_telemetry_report import DbgapTelemetryWrapper


BROAD_ABBREVIATION = "BI"
NONAMESPACESCHEMALOCATION = "http://www.ncbi.nlm.nih.gov/viewvc/v1/trunk/sra/doc/SRA_1-5/SRA.submission.xsd?view=co"
XSI = "http://www.w3.org/2001/XMLSchema-instance"
EXPERIMENT_XSD = "http://www.ncbi.nlm.nih.gov/viewvc/v1/trunk/sra/doc/SRA_1-5/SRA.experiment.xsd?view=co"
RUN_XSD = "http://www.ncbi.nlm.nih.gov/viewvc/v1/trunk/sra/doc/SRA_1-5/SRA.run.xsd?view=co"
SUBMISSION_XSD = "https://www.ncbi.nlm.nih.gov/viewvc/v1/trunk/sra/doc/SRA_1-5/SRA.submission.xsd?view=co"


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

    def _set_sample_attributes(self, sample_json, sample_id, md5):
        try:
            self.project = sample_json["aggregation_project"]
            self.location = sample_json["location"]
            self.version = sample_json["version"]
            self.md5 = md5
            self.phs = str(sample_json["phs_id"])
            self.data_type = sample_json["data_type"]
            self.alias = sample_json["alias"]
            self.aggregation_path = sample_json["aggregation_path"]
        except KeyError as e:
            raise ValueError(f"Missing required field: {e}")

        self.file_type = self._get_file_extension(self.aggregation_path)
        self.data_file = f"{sample_id}.{self.file_type}"
        self.dbgap_info = DbgapTelemetryWrapper(phs_id=self.phs).get_sample_info(alias=self.alias)

    @staticmethod
    def _get_file_extension(aggregation_path):
        return os.path.splitext(aggregation_path)[1][1:]

    @property
    def formatted_data_type(self):
        return self.DATA_TYPE_MAPPING.get(self.data_type, {"constant": "Unknown", "name": "Unknown"})

    @property
    def subject_string(self):
        subject_id = self.dbgap_info["submitted_subject_id"]

        return f"from subject '{subject_id}'" if subject_id else ""

    @property
    def biospecimen_repo(self):
        return self.dbgap_info["repository"]


class ReadGroup:
    def __init__(self, json_objects):
        first_read_group = json_objects[0]
        self._set_constant_values(first_read_group)
        self._set_aggregate_values(json_objects)
        self._set_submission_metadata(first_read_group)

    def _set_submission_metadata(self, first_read_group):
        # submission_metadata can have three different structures. 
        # 1. It will not exist if no samples have the column
        # 2. It can have a dict with keys itemsType , and items. This happens when the metadata is empty, but not for other samples
        # 3. Just has the metadata
        if "submission_metadata" in first_read_group and "items" not in first_read_group["submission_metadata"]:
            submission_metadata_str = first_read_group["submission_metadata"]
            submission_metadata_str_json = submission_metadata_str.replace("'", '"')
            # Replace None with null
            submission_metadata_str_json = submission_metadata_str_json.replace("None", "null")
            self.submission_metadata = self.sub_data_to_dict(json.loads(submission_metadata_str_json))
        else:
            self.submission_metadata = []

    def _set_constant_values(self, first_read_group):
        try:
            self.library_name = first_read_group["library_name"]
            self.library_type = first_read_group["library_type"]
            self.work_request_id = first_read_group.get("work_request_id")
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
        attributes_list = [x for x in json_objects]

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

        order_id = self.product_order_id if self.product_order_id else self.work_request_id
        return str(order_id)

    def get_library_descriptor(self):
        library_descriptors = {
            "WholeGenomeShotgun": {
                "strategy": {"ncbi_string": "WGS", "humanized_string": "whole genome shotgun"},
                "source": {"ncbi_string": "GENOMIC", "humanized_string": "genomic DNA"},
                "selection": "RANDOM"
            },
            "cDNAShotgun": {
                "strategy": {"ncbi_string": "RNA-Seq", "humanized_string": "RNA"},
                "source": {"ncbi_string": "TRANSCRIPTOMIC", "humanized_string": "transcriptome"},
                "selection": "cDNA"
            },
            "HybridSelection": {
                "strategy": {"ncbi_string": "WXS", "humanized_string": "random exon"},
                "source": {"ncbi_string": "GENOMIC", "humanized_string": "genomic DNA"},
                "selection": "Hybrid Selection"
            }
        }

        if self.library_type in library_descriptors:
            return library_descriptors[self.library_type]

        if (
            (self.library_type in ("cDNAShotgunReadTwoSense", "cDNAShotgunStrandAgnostic") 
            or self.analysis_type == "cDNA")
            and self.analysis_type != "AssemblyWithoutReference"
        ):
            return library_descriptors["cDNAShotgun"]

        # If library descriptor is not found, raise an error
        raise ValueError(f"No library descriptor found for the given parameters - library type: {self.library_type}")

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
        formatted_data_type = self.sample.formatted_data_type["constant"].replace(" ", "_")

        return f"{self.sample.phs}.{pdo_or_wr}.{self.read_group.library_name}.{pairing_code}.{self.sample.alias}.{self.sample.project}.{formatted_data_type}.{self.sample.version}"

    def get_file_name(self):
        return f"{self.get_submitter_id()}.add.experiment.xml"

    def get_title(self):
        repo = self.sample.biospecimen_repo
        library_strategy_string = self.read_group.get_library_descriptor()["strategy"]["humanized_string"]
        library_source_string = self.read_group.get_library_descriptor()["source"]["humanized_string"]
        paired_end = self.read_group.is_paired_end()

        return f"{repo} Illumina {library_strategy_string} sequencing of '{library_source_string}' {paired_end} library '{self.read_group.library_name}' containing sample '{self.sample.alias}' {self.sample.subject_string}"

    @staticmethod
    def get_read_spec(label, index, base_coord):
        return {
            "READ_INDEX": index,
            "READ_LABEL": label,
            "READ_CLASS": "Application Read",
            "READ_TYPE": "Forward" if label == "forward" else "Reverse",
            "BASE_COORD": base_coord
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

    def create_experiment_dict(self):
        experiment_dict = {
            "EXPERIMENT_SET": {
                "@xsi:noNamespaceSchemaLocation": EXPERIMENT_XSD,
                "@xmlns:xsi": XSI,
                "EXPERIMENT": {
                    "IDENTIFIERS": {
                        "SUBMITTER_ID": {
                            "@namespace": BROAD_ABBREVIATION,
                            "#text": self.get_submitter_id()
                        }
                    },
                    "TITLE": self.get_title(),
                    "STUDY_REF": {
                        "@accession": self.sample.phs,
                        "#text": None
                    },
                    "DESIGN": {
                        "DESIGN_DESCRIPTION": self.get_design_description(),
                        "SAMPLE_DESCRIPTOR": {
                            "@refname": self.sample.alias,
                            "@refcenter": self.sample.phs,
                            '#text': None
                        },
                        "LIBRARY_DESCRIPTOR": {
                            "LIBRARY_NAME": self.read_group.library_name,
                            "LIBRARY_STRATEGY": self.read_group.get_library_descriptor()["strategy"]["ncbi_string"],
                            "LIBRARY_SOURCE": self.read_group.get_library_descriptor()["source"]["ncbi_string"],
                            "LIBRARY_SELECTION": self.read_group.get_library_descriptor()["selection"],
                            "LIBRARY_LAYOUT": {
                                "PAIRED": None
                            }
                        },
                        "SPOT_DESCRIPTOR": {
                            "SPOT_DECODE_SPEC": {
                                "SPOT_LENGTH": self.get_spot_length(),
                                "READ_SPEC": [
                                    self.get_read_spec("forward", "0", "1"),
                                    self.get_read_spec("reverse", "1", str(self.read_group.get_read_length() + 1))
                                ]
                            }
                        }
                    },
                    "PLATFORM": {
                        "ILLUMINA": {
                            "INSTRUMENT_MODEL": "Illumina HiSeq X" if self.read_group.model == "Illumina HiSeq X 10" else self.read_group.model
                        }
                    },
                    "EXPERIMENT_ATTRIBUTES": {
                        "EXPERIMENT_ATTRIBUTE": [
                            {"TAG": key, "VALUE": value} for key, value in self.generate_experiment_attributes().items()
                        ]
                    }
                }
            }
        }

        return experiment_dict

    def create_file(self):
        print("Creating experiment xml files")

        experiment_dict = self.create_experiment_dict()
        validate_xml(experiment_dict, EXPERIMENT_XSD)
        write_xml_file(self.get_file_name(), experiment_dict)


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

    def create_run_dict(self):
        run_dict = {
            "RUN_SET": {
                "@xsi:noNamespaceSchemaLocation": RUN_XSD,
                "@xmlns:xsi": XSI,
                "RUN": {
                    "IDENTIFIERS": {
                        "SUBMITTER_ID": {
                            "@namespace": BROAD_ABBREVIATION,
                            "#text": self.get_submitter_id()
                        }
                    },
                    "EXPERIMENT_REF": {
                        "IDENTIFIERS": {
                            "SUBMITTER_ID": {
                                "@namespace": BROAD_ABBREVIATION,
                                "#text": self.experiment.get_submitter_id()
                            }
                        }
                    },
                    "DATA_BLOCK": {
                        "FILES": {
                            "FILE": {
                                "@filename": self.sample.data_file,
                                "@filetype": self.sample.file_type,
                                "@checksum_method": "MD5",
                                "@checksum": self.sample.md5
                            }
                        }
                    },
                    "RUN_ATTRIBUTES": {
                        "RUN_ATTRIBUTE": [
                            {"TAG": key, "VALUE": value} for key, value in self.generate_run_attributes().items()
                        ]
                    }
                }
            }
        }

        return run_dict

    def create_file(self):
        print("Creating run xml files")

        run_dict = self.create_run_dict()
        validate_xml(run_dict, RUN_XSD)
        write_xml_file(self.get_file_name(), run_dict)


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
        actions = {
            "ACTIONS": {
                "ACTION": [
                    {"PROTECT": None},
                    {"RELEASE": None},
                    {"ADD": {"@source": self.experiment.get_file_name(), "@schema": "experiment"}},
                    {"ADD": {"@source": self.run.get_file_name(), "@schema": "run"}}
                ]
            }
        }
        submission.update(actions)

    @staticmethod
    def create_submission_attributes(submission):
        submission_attributes = {
            "SUBMISSION_ATTRIBUTES": {
                "SUBMISSION_ATTRIBUTE": {
                    "TAG": "Submission Site",
                    "VALUE": "NCBI_PROTECTED"
                }
            }
        }
        submission.update(submission_attributes)

    def create_file(self):
        print("Creating submission xml file")

        submission_dict = {
            "SUBMISSION_SET": {
                "@xsi:noNamespaceSchemaLocation": SUBMISSION_XSD,
                "@xmlns:xsi": XSI,
                "SUBMISSION": {
                    "@submission_date": get_date(),
                    "@submission_comment": self.get_submission_comment(),
                    "@lab_name": "Genome Sequencing",
                    "@alias": self.get_alias(),
                    "@center_name": BROAD_ABBREVIATION,
                    "CONTACTS": {
                        "CONTACT": {
                            "@name": "sra_sumissions",
                            "@inform_on_status": "mailto:dsde-ops@broadinstitute.org",
                            "@inform_on_error": "mailto:dsde-ops@broadinstitute.org"
                        }
                    }
                }
            }
        }

        submission = submission_dict["SUBMISSION_SET"]["SUBMISSION"]
        self.create_actions(submission)
        self.create_submission_attributes(submission)

        validate_xml(submission_dict, SUBMISSION_XSD)
        write_xml_file("submission.xml", submission_dict)


# Helper Functions #
def validate_xml(xml_dict, xsd_url):
    try:
        # Convert dictionary to XML string
        xml_string = xmltodict.unparse(xml_dict)

        # Download XSD content
        xsd_content = requests.get(xsd_url).content
        # Create XMLSchema object
        xmlschema_doc = etree.parse(BytesIO(xsd_content))
        xmlschema = etree.XMLSchema(xmlschema_doc)
        # Parse the XML string (convert to bytes first)
        xml_doc = etree.fromstring(xml_string.encode())
        # Validate XML against XSD
        xmlschema.assertValid(xml_doc)
        print(f"Validation successful. XML is valid according to {xsd_url}.")
    except etree.XMLSchemaError as e:
        raise ValueError("Error in XML Schema: {}".format(e))
    except etree.XMLSyntaxError as e:
        raise ValueError("Error in XML Syntax: {}".format(e))
    except Exception as e:
        raise ValueError("Error: {}".format(e))


def write_xml_file(file_name, xml_dict):
    file_path = f"/cromwell_root/xml/{file_name}"
    xml_string = xmltodict.unparse(xml_dict, short_empty_elements=True, pretty=True)

    with open(file_path, 'wb') as xfile:
        xfile.write(xml_string.encode('ASCII'))


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
