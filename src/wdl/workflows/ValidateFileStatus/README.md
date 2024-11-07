# Validate GDC Sample File Status
This WDL queries the GDC for a give sample's file validation status and updates the sample table metadata to indicate the status that is returned.

## Inputs Table: 
| Input Name            | Description                                                                             | Type    | Required | Default |
|-----------------------|-----------------------------------------------------------------------------------------|---------|----------|---------|
| **gdc_token**         | The GCP path to the GDC file containing the user token                                  | FileRef | Yes      | N/A     |
| **program**           | The GDC program name                                                                    | String  | Yes      | N/A     |
| **project**           | The GDC project name                                                                    | String  | Yes      | N/A     |
| **workspace_name**    | The workspace name                                                                      | String  | Yes      | N/A     |
| **workspace_project** | The workspace billing project                                                           | String  | Yes      | N/A     |
| **sample_id**         | The sample ID (the primary key of the sample table)                                     | String  | Yes      | N/A     |
| **sample_alias**      | The collaborator sample ID                                                              | String  | Yes      | N/A     |
| **agg_project**       | The sample's aggregation project                                                        | String  | Yes      | N/A     |
| **data_type**         | The data type. Must be one of: "WGS", "Exome", or "RNA"                                 | String  | Yes      | N/A     |
| **aggregation_path**  | The GCP path to the aggregation (bam/cram file)                                         | FileRef | Yes      | N/A     |
| **delete**            | Whether the bam/cram file should be deleted once files have been successfully validated | Boolean | No       | False   |