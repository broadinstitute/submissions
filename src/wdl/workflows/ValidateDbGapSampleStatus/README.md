# Validate dbGaP Sample Status

This WDL queries dbGaP for a give sample's file validation status and updates the sample table metadata to indicate the status that is returned. 

## Inputs Table: 
| Input Name            | Description                                                                                              | Type    | Required | Default  |
|-----------------------|----------------------------------------------------------------------------------------------------------|---------|----------|----------|
| **workspace_name**    | The workspace name                                                                                       | String  | Yes      | N/A      |
| **workspace_project** | The workspace billing project                                                                            | String  | Yes      | N/A      |
| **sample_id**         | The sample identifier. MUST be unique for a given sample.                                                | String  | Yes      | N/A      |
| **sample_alias**      | The collaborator sample ID                                                                               | String  | Yes      | N/A      |
| **phs_id**            | The phs ID for all the samples                                                                           | String  | Yes      | N/A      |
| **data_type**         | The data type - this should be uniform for ALL samples being processed. One of: "WGS", "Exome", or "RNA" | String  | Yes      | N/A      |

