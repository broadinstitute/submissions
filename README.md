# Submissions

## Description
This repo is intended to be used to submit samples to the GDC data repository.

## GDC Submission Steps

1. LINK ENTITIES - If you are working in a test environment you will need to link any data before you send it to GDC. For example, when submitting samples you will need to make sure that the case, sample, aliquots and read groups are already created inside of your GDC project. In PROD this will be handled pre pipeline, but for testing purposes you need to run this script "src/scripts/link_gdc_entities.py". Example sample file - gdcsubtest.json.

    python src/scripts/link_gdc_entities.py -f "path to file that contains sample info" -t "gdc token"

2. VERIFY REGISTRATION - This is the first real stage of the pipeline, and is its own workflow inside of the Terra workspace. This will essentially take sample id and write back to the sample data table to verify if the sample is registered or not. Below is an example call made by the wdl task to the python script

    python main.py --project "TEST4" --program "BROAD" --alias_value "sample_id value" --data_type "WGS" --aggregation_project "RP-1329"
        --step "verify_registration" --token "token value"
 
3. AddReadsField - Simple wdl task that takes in a sample Id and returns a file with all of the readGroups. It does this by calling the Terra Api and returning all of the reads from the read_groups table that match the sample_id. Join field = sample_identifier.

    python src/scripts/extract_reads_data.py -w "gdc_submissions_development" -p "gdc_submissions" -s "sample id to match on"

4. Submit Metadata - Now if the sample is verified and the registration_status field in the table was set to true from the previous step, the metadata can be submitted. This script will compile a a json object that will look very similiar to this file resources/metadata.json. Now the wdl task submitMetadataToGDC will run the script to submit the metadata file.
    
    python3 main.py --program "BROAD" --project "TEST4" --step "submit_metadata" --alias_value "sample if" - -agg_path "gs path to bam file in bucket" --        agg_project "RP-1329" --data_type "WGS" --file_size 383751452100 --md5 f7a0efcc5025ea374d50d01484a13186 --read_groups readGroup.json --token "123"
    
5. RetrieveGdcManifest - Uses a curl command to make a call to this endpoint - 
    https://api.gdc.cancer.gov/v0/submission/program/project/manifest?ids=~{sar_id}. And writes the result to a file called manifest.yml.
    
6. TransferBamToGdc - This is where the actual data file is transfered. It does this by localizing the bam file to the VM, and then uses the gdcClient to
    do the actual transfer.
    
    gdc-client upload -t ~{gdc_token} -m ~{manifest} --debug --log-file gdc_transfer.log
    
7. ValidateFileStatus - This step will wait for transfer bam to process to stop running, and then it will make and api call to GDC and get the status of
    of the file upload.
    
    python3 /main.py --alias_value "sample id" --agg_project "RP-1329" --data_type "WGS" --program "BROAD" --project "TEST4"
      --step "validate_status" --token ~{gdc_token}
      
8. CreateTableLoadFile / UpsertMetadataToDataModel - These two tasks work together to write these fields back to the sample data table. UUID, file_state,
    state, registration_status and read_json_file.
    
