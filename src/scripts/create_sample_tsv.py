import json
import csv
import argparse

def createTSV(sample_file):
    metadata = readMetadata(sample_file)
    sampleMetadata = metadata['samples'][0]
    sampleMetadata['project'] = metadata['project']
    sampleMetadata['program'] = metadata['program']

    readGroups = sampleMetadata.pop('read_groups')
    readGroups = pushReadGroupsToTSV(readGroups, sampleMetadata)

    tsv_file = open("sample.tsv", "w")
    read_tsv_file = open("read.tsv", "w")

    tsv_writer = csv.writer(tsv_file, delimiter='\t')
    read_tsv_writer = csv.writer(read_tsv_file, delimiter='\t')

    tsv_writer.writerow(sampleMetadata.keys())
    tsv_writer.writerow(sampleMetadata.values())
    read_tsv_writer.writerow(readGroups[0].keys())

    for row in readGroups: # write data rows
        # print("row", row.values())
        read_tsv_writer.writerow(row.values())
    print("Done writing read groups to tsv")

    tsv_file.close()
    read_tsv_file.close()


def pushReadGroupsToTSV(readGroups, sampleMetadata):
    submitterIdConstant = f"{sampleMetadata['aggregation_project']}.{sampleMetadata['sample_alias']}"

    for readGroup in readGroups:
        readGroup['read_group_id'] = f"{readGroup['flow_cell_barcode']}.{readGroup['lane_number']}.{submitterIdConstant}"
        readGroup['sample_alias'] = sampleMetadata['sample_alias']

    return readGroups

def readMetadata(sample_file):
    """Reads the metadata json file"""

    with open(sample_file, 'r') as my_file:
        return json.load(my_file) # TODO - Need to be more defensive here

    print("Error when trying to parse the input Metadata file")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-f', '--file', required=True, help='.json file that contains all the data for the given sample')
    args = parser.parse_args()

    createTSV(args.file)