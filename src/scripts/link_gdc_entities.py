import argparse
import requests
import json
from google.cloud import storage

def link_entity(sample_file, token):
    """Creates all entities such as case, sample, aliquot and readGroup and pushes to gdc"""

    # Parse the incoming sample file
    metadata = readMetadata(sample_file)
    sampleMetadata = metadata['samples'][0]

    project = metadata['project']
    program = metadata['program']

    # Now create the array of entities to be submitted
    linkData = createLinkData(sampleMetadata, program, project)

    print("linkdata", linkData)
    # Use the link data and call gdc to create the entities
    linkSampleAndAliqout(linkData, token, program, project)

def linkSampleAndAliqout(linkData, token, program, project):
    """Helper function to create entities inside of gdc"""

    endpoint = 'https://api.gdc.cancer.gov/v0/submission'
    url = f"{endpoint}/{program}/{project}"

    response = requests.put(url,
        data = json.dumps(linkData),
        headers = getHeaders(token)
    )

    print("response for creating links", response.text)

def getHeaders(token):
    """Returns general headers for gdc api call"""

    return {
        "Content-Type": "application/json",
        "X-Auth-Token": token
    }

def createLinkData(sampleMetadata, program, project):
    """Creates all entities and returns them as an array of dictionaries"""

    case = createCase(program, project)
    sample = createSample(sampleMetadata, program, project)
    aliquot = createAliquot(sampleMetadata)
    readGroups = createReadGroups(sampleMetadata)

    return [case, sample, aliquot] + readGroups

def createReadGroups(sampleMetadata):
    """Creates an array of readGroups"""

    readGroups = []
    submitterIdConstant = f"{sampleMetadata['aggregation_project']}.{sampleMetadata['sample_alias']}"

    for readGroup in sampleMetadata['read_groups']:
        readGroups.append({
            "type": "read_group",
            "aliquots": {
                "submitter_id": sampleMetadata['sample_alias']
            },
            "submitter_id": f"{readGroup['flow_cell_barcode']}.{readGroup['lane_number']}.{submitterIdConstant}",
            "experiment_name": readGroup['experiment_name'],
            "sequencing_center": readGroup['sequencing_center'],
            "platform": readGroup['platform'],
            "library_selection": readGroup['library_selection'],
            "library_strategy": readGroup['library_strategy'],
            "library_name": readGroup['library_name'],
            "lane_number": readGroup['lane_number']
            "is_paired_end": readGroup['is_paired_end'],
            "read_length": readGroup['read_length'],
            "read_group_name": readGroup['read_group_name'],
            "target_capture_kit": readGroup['target_capture_kit'],
            "to_trim_adapter_sequence": True,
            "platform": "Illumina"
        })
    
    return readGroups

def createAliquot(sampleMetadata):
    """Creates aliquot and links it to the sample"""

    return {
        "type": "aliquot",
        "samples": {
            "submitter_id": f"{sampleMetadata['sample_alias']}-sample"
        },
        "submitter_id": sampleMetadata['sample_alias']
    }

def createSample(sampleMetadata, program, project):
    """Creates a sample and links it to the case"""

    return {
        "type": "sample",
        "cases": {
            "submitter_id": f"{program}-{project}-0001"
        },
        "submitter_id": f"{sampleMetadata['sample_alias']}-sample",
        "sample_type": "Primary Tumor", # needed?
        "tissue_type": "Tumor"# needed?
    }

def createCase(program, project):
    """Creates the case by using the program and project"""

    return {
        "type": "case",
        "projects": {
            "code": project
        },
        "submitter_id": f"{program}-{project}-0001"
    }

def readMetadata(sample_file):
    """Reads the metadata json file"""

    with open(sample_file, 'r') as my_file:
        return json.load(my_file) # TODO - Need to be more defensive here

    print("Error when trying to parse the input Metadata file")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-f', '--file', required=True, help='.json file that contains all the data for the given sample')
    parser.add_argument('-t', '--token', required=True, help='Api token to communicate with GDC')
    args = parser.parse_args()

    link_entity(args.file, args.token)
