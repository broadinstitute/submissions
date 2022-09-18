import json
import argparse
import pandas
from batch_upsert_entities import create_upsert_request, call_rawls_batch_upsert

def joinTables(read_file, sample_file, project, workspace_name):
    sampleTSV = pandas.read_csv(sample_file, sep='\t')
    readTSV = pandas.read_csv(read_file, sep='\t')
    # mergedTSV = pandas.merge(sampleTSV, readTSV, how="left", left_on="sample_id", right_on="sample_identifier")
    
    sampleIdToReadGroups = [formatReadGroups(x, readTSV) for x in sampleTSV['sample_id']]

    pushReadGroupsToWorkspace(sampleIdToReadGroups)

def pushReadGroupsToWorkspace(sampleIdToReadGroups):
    for readGroupObj in sampleIdToReadGroups:
        print("read obj", readGroupObj)
        for sampleId, readObj in readGroupObj.items():
            # write this obj to a file in the workspace
            f = open(f"cromwell_root/fc-a881fb23-4d34-42ce-90cd-d0dc7e8595a7/test_data/{sampleId}.json", 'w')
            #f = open(f"cromwell_root/{sampleId}.json", 'w')
            f.write(json.dumps(readObj))
            f.close()

def formatReadGroups(sample_id, readTSV):
    joinedReads = readTSV[(readTSV['sample_identifier'] == sample_id)]
    single_attr_cols = list(readTSV.columns)
    readsArray = []

    for index, row in joinedReads.iterrows():
        readsObj = {}
        # if there are non-array/list attribute columns - cases where all columns are arrays, single_attr_cols would be empty
        if single_attr_cols:
            # for each column that is not an array
            for col in single_attr_cols:
                # get value in col from df
                attr_value = str(row[col])
                readsObj[col] = attr_value
        readsArray.append(readsObj)
    
    return {sample_id: readsArray}

def returnJSON(read):
    # print("here", read)
    return read

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-w', '--workspace_name', required=True, help='name of workspace in which to make changes')
    parser.add_argument('-p', '--project', required=True, help='billing project (namespace) of workspace in which to make changes')
    parser.add_argument('-ts', '--read_file', required=True, help='tsv file for reads that is passed from the wdl')
    parser.add_argument('-tr', '--sample_file', required=True, help='tsv file for samples that is passed from the wdl')
    args = parser.parse_args()

    joinTables(args.read_file, args.sample_file, args.project, args.workspace_name)