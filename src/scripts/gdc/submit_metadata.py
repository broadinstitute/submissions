import argparse
import json
import time
from google.cloud import storage
from urllib.parse import urlparse

from src.services.gdc_api import GdcApiWrapper

DATA_TYPE_TO_EXPERIMENT_STRATEGY = {
    "WGS": "WGS",
    "Exome": "WXS",
    "WXS": "WXS",
    "RNA": "RNA-Seq",
    "Custom_Selection": "Targeted Sequencing"
}

class MetadataSubmission:
    def __init__(self, program=None, project=None, token=None, sample_alias=None, aggregation_path=None, agg_project=None, data_type=None, md5=None, read_groups=None):
        self.program = program
        self.project = project
        self.token = token
        self.sample_alias = sample_alias
        self.aggregation_path = aggregation_path
        self.agg_project = agg_project
        self.data_type = data_type
        self.md5 = md5
        self.read_groups = read_groups
        self.submitter_id = f"{sample_alias}.{data_type}.{agg_project}"

    def submit(self):
        metadata = self.create_metadata()
        gdc_wrapper = GdcApiWrapper(program=self.program, project=self.project, token=self.token)
        gdc_wrapper.submit_metadata(metadata)
        time.sleep(100) # Wait a second since gdc can lag a little
        self.write_bam_data_to_file()
        self.write_uuid_to_file(gdc_wrapper)

    def write_uuid_to_file(self, gdc_wrapper):
        gdc_response = gdc_wrapper.get_entity("sar", self.submitter_id).json()


        if 'data' in gdc_response and gdc_response['data'].get('submitted_aligned_reads'):
            aligned_reads = gdc_response['data']['submitted_aligned_reads']
            
            if aligned_reads:
                uuid = aligned_reads[0]['id']
                file_path = "/cromwell_root/UUID.txt"
                
                with open(file_path, 'w') as file:
                    file.write(uuid)
                
                print("Done writing UUID to file")
            else:
                print("No ids inside the submitted_aligned_reads array")
        else:
            raise RuntimeError("Data was not returned from GDC properly")

    def get_file_size(self):
        client = storage.Client()
        parsed_url = urlparse(self.aggregation_path)
        bucket_name = parsed_url.netloc
        file_path = parsed_url.path.lstrip("/")

        bucket = client.get_bucket(bucket_name)
        blob = bucket.blob(file_path)
        blob.reload()
        file_size = blob.size
        return int(file_size)

    def create_metadata(self):
        gdc_metadata = {
            "file_name": f"{self.submitter_id}.bam",
            "submitter_id": self.submitter_id,
            "data_category": "Sequencing Reads",
            "type": "submitted_aligned_reads",
            "file_size": self.get_file_size(),
            "data_type": "Aligned Reads",
            "experimental_strategy": DATA_TYPE_TO_EXPERIMENT_STRATEGY.get(self.data_type, ""),
            "data_format": "BAM",
            "project_id": f"{self.program}-{self.project}",
            "md5sum": self.md5,
            "read_groups": self.get_read_groups()
        }
        if self.data_type == "WGS":
            gdc_metadata["proc_internal"] = "dna-seq skip"

        return gdc_metadata

    def load_read_groups_from_file(self):
        """Opens reads file and loads JSON data"""
        with open(self.read_groups, 'r') as my_file:
            return json.loads(json.load(my_file))

    def get_read_groups(self):
        """Generate submitter IDs for read groups."""
        submitter_ids = []
        submitter_id_constant = f"{self.agg_project}.{self.sample_alias}"
        read_groups = self.load_read_groups_from_file()

        for read_group in read_groups:
            flow_cell_barcode = read_group["attributes"]["flow_cell_barcode"]
            lane_number = read_group["attributes"]["lane_number"]
            submitter_id = f"{flow_cell_barcode}.{lane_number}.{submitter_id_constant}"
            submitter_ids.append({"submitter_id": submitter_id})

        return submitter_ids

    def write_bam_data_to_file(self):
        """Writes BAM data to a file named bam.txt in /cromwell_root/"""
        file_path = "/cromwell_root/bam.txt"
        bam_data = f"{self.submitter_id}.bam"

        with open(file_path, 'w') as file:
            file.write(bam_data)

        print("Done writing BAM data to file")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-s', '--sample_alias', required=True, help='list of aliases to check registration status')
    parser.add_argument('-t', '--token', required=True, help='Api token to communicate with GDC')
    parser.add_argument('-pg', '--program', required=True, help='GDC program')
    parser.add_argument('-pj', '--project', required=True, help='GDC project')
    parser.add_argument('-ag', '--aggregation_path', required=True, help='Path to bam file')
    parser.add_argument('-ap', '--agg_project', required=True, help='Broad specific project for the sample')
    parser.add_argument('-d', '--data_type', required=True, help='Data type - i.e. WGS')
    parser.add_argument('-md', '--md5', required=True, help='md5 for the file')
    parser.add_argument('-rg', '--read_groups', required=True, help='JSON file with all linked read groups for the sample')
    args = parser.parse_args()

    # Pass command line arguments to the MetadataSubmission class
    MetadataSubmission(**vars(args)).submit()
