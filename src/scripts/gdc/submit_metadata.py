import argparse
import json
from src.services import GdcApiWrapper

DATA_TYPE_TO_EXPERIMENT_STRATEGY = {
    "WGS": "WGS",
    "Exome": "WXS",
    "WXS": "WXS",
    "RNA": "RNA-Seq",
    "Custom_Selection": "Targeted Sequencing"
}

class MetadataSubmission:
    def __init__(self, program=None, project=None, token=None, sample_alias=None, aggregation_path=None, agg_project=None, data_type=None, file_size=None, md5=None, read_group_file=None):
        self.program = program
        self.project = project
        self.token = token
        self.sample_alias = sample_alias
        self.aggregation_path = aggregation_path
        self.agg_project = agg_project
        self.data_type = data_type
        self.file_size = file_size
        self.md5 = md5
        self.read_group_file = read_group_file
        self.submitter_id = f"{sample_alias}.{data_type}.{agg_project}"

    def submit(self):
        metadata = self.create_metadata()
        GdcApiWrapper(self.program, self.project, self.token).submit_metadata(metadata)

    def create_metadata(self):
        return {
            "file_name": f"{self.submitter_id}.bam",
            "submitter_id": self.submitter_id,
            "data_category": "Sequencing Reads",
            "type": "submitted_aligned_reads",
            "file_size": int(self.file_size),
            "data_type": "Aligned Reads",
            "experimental_strategy": DATA_TYPE_TO_EXPERIMENT_STRATEGY.get(self.data_type, ""),
            "data_format": "BAM",
            "project_id": f"{self.program}-{self.project}",
            "md5sum": self.md5,
            "proc_internal": "dna-seq skip",
            "read_groups": self.get_read_groups()
        }

    def load_read_groups_from_file(self):
        """Opens reads file and loads JSON data"""
        with open(self.read_group_file, 'r') as my_file:
            return json.load(my_file)

    def get_read_groups(self):
        submitter_ids = []
        submitter_id_constant = f"{self.agg_project}.{self.sample_alias}"
        read_groups = self.load_read_groups_from_file()

        for read_group in read_groups:
            submitter_ids.append({
                "submitter_id": f"{read_group['flow_cell_barcode']}.{read_group['lane_number']}.{submitter_id_constant}"
            })

        return submitter_ids

    def write_bam_data_to_file(self):
        """Extracts bam path and bam name and writes to a file named bam.txt"""
        f = open("/cromwell_root/bam.txt", 'w')
        f.write(f"{self.submitter_id}.bam")
        f.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-s', '--sample_alias', required=True, help='list of aliases to check registration status')
    parser.add_argument('-t', '--token', required=True, help='Api token to communicate with GDC')
    parser.add_argument('-pg', '--program', required=True, help='GDC program')
    parser.add_argument('-pj', '--project', required=True, help='GDC project')
    parser.add_argument('-ag', '--aggregation_path', required=True, help='Path to bam file')
    parser.add_argument('-ap', '--agg_project', required=True, help='Broad specific project for the sample')
    parser.add_argument('-d', '--data_type', required=True, help='Data type - i.e. WGS')
    parser.add_argument('-f', '--file_size', required=True, help='File size in bytes for the file')
    parser.add_argument('-md', '--md5', required=True, help='md5 for the file')
    parser.add_argument('-rg', '--read_groups', required=True, help='JSON file with all linked read groups for the sample')
    args = parser.parse_args()
    # Pass command line arguments to the MetadataSubmission class
    metadata_submission = MetadataSubmission(**vars(args))
    metadata_submission.submit()
