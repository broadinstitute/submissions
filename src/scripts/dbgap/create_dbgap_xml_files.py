import argparse

from src.services.terra import TerraAPIWrapper
from dbgap_classes import Sample, ReadGroup, Experiment, Run, Submission


def run_xml_creation(sample_id, billing_project, workspace_name, md5):
    terra_service = TerraAPIWrapper(billing_project, workspace_name)
    sample_json = terra_service.call_terra_api(sample_id, "sample")
    read_group_json = terra_service.call_terra_api(sample_id, "read-group")

"""
    sample_json = [
        {
        "attributes": {
            "aggregation_project": "RP-1545",
            "location": "OnPrem",
            "md5": "gs://fc-d40787e1-06e7-40e7-af19-134b48dd88a1/RP-1545/Exome/16177_CCPM_1300040_BLOOD/v4/16177_CCPM_1300040_BLOOD.bam.md5",
            "hard_clipping_used": False,
            "aggregation_path": "gs://fc-d40787e1-06e7-40e7-af19-134b48dd88a1/RP-1545/Exome/16177_CCPM_1300040_BLOOD/v4/16177_CCPM_1300040_BLOOD.bam",
            "alias": "16177_CCPM_1300040_BLOOD",
            "version": 4,
            "phs_id": "phs001285",
            "data_type": "Exome"
        },
        "entityType": "sample",
        "name": "RP-1545_16177_CCPM_1300040_BLOOD_v4_Exome_DBGAP"
        }
    ]
    read_group_json = [
        {
        "attributes": {
            "product_order_id": "PDO-19179",
            "sample_type": "Normal",
            "machine_name": "SL-HXY",
            "sample_material_type": "DNA:DNA Genomic",
            "paired_run": 1,
            "library_name": "0342416761_Illumina_P5-Nawoh_P7-Najod",
            "run_date": "2019-08-23 00:00:00",
            "library_type": "HybridSelection",
            "lane": 6,
            "run_barcode": "H3FMMCCX2190823",
            "version": 4,
            "data_type": "Exome",
            "bait_set": "whole_exome_illumina_coding_v1",
            "sample_alias": "16177_CCPM_1300040_BLOOD",
            "reference_sequence": "/seq/references/Homo_sapiens_assembly19/v1/Homo_sapiens_assembly19.fasta",
            "mean_insert_size": 184.88859,
            "molecular_barcode_sequence": "GAACCTAG-TGATATTC",
            "work_request_id": 0,
            "aggregation_project": "RP-1545",
            "model": "Illumina HiSeq X 10",
            "research_project_id": "RP-1545",
            "analysis_type": "Resequencing",
            "sample_id": "RP-1545_16177_CCPM_1300040_BLOOD_v4_Exome_DBGAP",
            "submission_metadata": "[{'key': 'target_capture_kit_vendor', 'value': 'Illumina'}, {'key': 'target_capture_kit_name', 'value': 'Nextera Exome Kit (96 Spl)'}, {'key': 'library_preparation_kit_catalog_number', 'value': 'KK8504'}, {'key': 'library_preparation_kit_vendor', 'value': 'Kapa BioSystems'}, {'key': 'library_preparation_kit_version', 'value': 'v1.1'}, {'key': 'target_capture_kit_target_region', 'value': 'http://support.illumina.com/content/dam/illumina-support/documents/documentation/chemistry_documentation/samplepreps_nextera/nexterarapidcapture/nexterarapidcapture_exome_targetedregions_v1.2.bed'}, {'key': 'library_preparation_kit_name', 'value': 'KAPA Hyper Prep Kit with KAPA Library Amplification Primer Mix (10X).'}, {'key': 'target_capture_kit_catalog_number', 'value': '20020617'}]",
            "standard_deviation": 71.34563,
            "read_structure": "76T8B8B76T",
            "analysis_date": "2019-08-25 00:00:00",
            "molecular_barcode_name": "Illumina_P5-Nawoh_P7-Najod",
            "root_sample_id": "SM-J461C",
            "flowcell_barcode": "H3FMMCCX2",
            "individual_alias": "16177_CCPM_1300040",
            "run_name": "190823_SL-HXY_0576_BFCH3FMMCCX2",
            "product_part_number": "P-EX-0040",
            "reference_sequence_name": "Homo_sapiens_assembly19",
            "research_project_name": "Tolaney_Wagle (DFCI) - 16-177 ER+ and HER- Metastatic Breast Cancer",
            "sample_lsid": "broadinstitute.org:bsp.prod.sample:JD5I5"
        },
        "entityType": "read-group",
        "name": "H3FMMCCX2.6.4.RP-1545.16177_CCPM_1300040_BLOOD"
        },
        {
        "attributes": {
            "product_order_id": "PDO-19179",
            "sample_type": "Normal",
            "machine_name": "SL-HXY",
            "sample_material_type": "DNA:DNA Genomic",
            "paired_run": 1,
            "library_name": "0342416761_Illumina_P5-Nawoh_P7-Najod",
            "run_date": "2019-08-23 00:00:00",
            "library_type": "HybridSelection",
            "lane": 7,
            "run_barcode": "H3FMMCCX2190823",
            "version": 4,
            "data_type": "Exome",
            "bait_set": "whole_exome_illumina_coding_v1",
            "sample_alias": "16177_CCPM_1300040_BLOOD",
            "reference_sequence": "/seq/references/Homo_sapiens_assembly19/v1/Homo_sapiens_assembly19.fasta",
            "mean_insert_size": 184.88859,
            "molecular_barcode_sequence": "GAACCTAG-TGATATTC",
            "work_request_id": 0,
            "aggregation_project": "RP-1545",
            "model": "Illumina HiSeq X 10",
            "research_project_id": "RP-1545",
            "analysis_type": "Resequencing",
            "sample_id": "RP-1545_16177_CCPM_1300040_BLOOD_v4_Exome_DBGAP",
            "submission_metadata": "[{'key': 'target_capture_kit_catalog_number', 'value': '20020617'}, {'key': 'library_preparation_kit_name', 'value': 'KAPA Hyper Prep Kit with KAPA Library Amplification Primer Mix (10X).'}, {'key': 'target_capture_kit_name', 'value': 'Nextera Exome Kit (96 Spl)'}, {'key': 'library_preparation_kit_version', 'value': 'v1.1'}, {'key': 'library_preparation_kit_catalog_number', 'value': 'KK8504'}, {'key': 'library_preparation_kit_vendor', 'value': 'Kapa BioSystems'}, {'key': 'target_capture_kit_vendor', 'value': 'Illumina'}, {'key': 'target_capture_kit_target_region', 'value': 'http://support.illumina.com/content/dam/illumina-support/documents/documentation/chemistry_documentation/samplepreps_nextera/nexterarapidcapture/nexterarapidcapture_exome_targetedregions_v1.2.bed'}]",
            "standard_deviation": 71.34563,
            "read_structure": "76T8B8B76T",
            "analysis_date": "2019-08-25 00:00:00",
            "molecular_barcode_name": "Illumina_P5-Nawoh_P7-Najod",
            "root_sample_id": "SM-J461C",
            "flowcell_barcode": "H3FMMCCX2",
            "individual_alias": "16177_CCPM_1300040",
            "run_name": "190823_SL-HXY_0576_BFCH3FMMCCX2",
            "product_part_number": "P-EX-0040",
            "reference_sequence_name": "Homo_sapiens_assembly19",
            "research_project_name": "Tolaney_Wagle (DFCI) - 16-177 ER+ and HER- Metastatic Breast Cancer",
            "sample_lsid": "broadinstitute.org:bsp.prod.sample:JD5I5"
        },
        "entityType": "read-group",
        "name": "H3FMMCCX2.7.4.RP-1545.16177_CCPM_1300040_BLOOD"
        },
        {
        "attributes": {
            "product_order_id": "PDO-19179",
            "sample_type": "Normal",
            "machine_name": "SL-HXY",
            "sample_material_type": "DNA:DNA Genomic",
            "paired_run": 1,
            "library_name": "0342416761_Illumina_P5-Nawoh_P7-Najod",
            "run_date": "2019-08-23 00:00:00",
            "library_type": "HybridSelection",
            "lane": 8,
            "run_barcode": "H3FMMCCX2190823",
            "version": 4,
            "data_type": "Exome",
            "bait_set": "whole_exome_illumina_coding_v1",
            "sample_alias": "16177_CCPM_1300040_BLOOD",
            "reference_sequence": "/seq/references/Homo_sapiens_assembly19/v1/Homo_sapiens_assembly19.fasta",
            "mean_insert_size": 184.88859,
            "molecular_barcode_sequence": "GAACCTAG-TGATATTC",
            "work_request_id": 0,
            "aggregation_project": "RP-1545",
            "model": "Illumina HiSeq X 10",
            "research_project_id": "RP-1545",
            "analysis_type": "Resequencing",
            "sample_id": "RP-1545_16177_CCPM_1300040_BLOOD_v4_Exome_DBGAP",
            "submission_metadata": "[{'key': 'target_capture_kit_vendor', 'value': 'Illumina'}, {'key': 'target_capture_kit_name', 'value': 'Nextera Exome Kit (96 Spl)'}, {'key': 'library_preparation_kit_name', 'value': 'KAPA Hyper Prep Kit with KAPA Library Amplification Primer Mix (10X).'}, {'key': 'library_preparation_kit_version', 'value': 'v1.1'}, {'key': 'library_preparation_kit_catalog_number', 'value': 'KK8504'}, {'key': 'target_capture_kit_target_region', 'value': 'http://support.illumina.com/content/dam/illumina-support/documents/documentation/chemistry_documentation/samplepreps_nextera/nexterarapidcapture/nexterarapidcapture_exome_targetedregions_v1.2.bed'}, {'key': 'library_preparation_kit_vendor', 'value': 'Kapa BioSystems'}, {'key': 'target_capture_kit_catalog_number', 'value': '20020617'}]",
            "standard_deviation": 71.34563,
            "read_structure": "76T8B8B76T",
            "analysis_date": "2019-08-25 00:00:00",
            "molecular_barcode_name": "Illumina_P5-Nawoh_P7-Najod",
            "root_sample_id": "SM-J461C",
            "flowcell_barcode": "H3FMMCCX2",
            "individual_alias": "16177_CCPM_1300040",
            "run_name": "190823_SL-HXY_0576_BFCH3FMMCCX2",
            "product_part_number": "P-EX-0040",
            "reference_sequence_name": "Homo_sapiens_assembly19",
            "research_project_name": "Tolaney_Wagle (DFCI) - 16-177 ER+ and HER- Metastatic Breast Cancer",
            "sample_lsid": "broadinstitute.org:bsp.prod.sample:JD5I5"
        },
        "entityType": "read-group",
        "name": "H3FMMCCX2.8.4.RP-1545.16177_CCPM_1300040_BLOOD"
        },
        {
        "attributes": {
            "product_order_id": "PDO-19179",
            "sample_type": "Normal",
            "machine_name": "SL-HXT",
            "sample_material_type": "DNA:DNA Genomic",
            "paired_run": 1,
            "library_name": "0342416761_Illumina_P5-Nawoh_P7-Najod",
            "run_date": "2019-08-27 00:00:00",
            "library_type": "HybridSelection",
            "lane": 8,
            "run_barcode": "H3G2HCCX2190827",
            "version": 4,
            "data_type": "Exome",
            "bait_set": "whole_exome_illumina_coding_v1",
            "sample_alias": "16177_CCPM_1300040_BLOOD",
            "reference_sequence": "/seq/references/Homo_sapiens_assembly19/v1/Homo_sapiens_assembly19.fasta",
            "mean_insert_size": 184.88859,
            "molecular_barcode_sequence": "GAACCTAG-TGATATTC",
            "work_request_id": 0,
            "aggregation_project": "RP-1545",
            "model": "Illumina HiSeq X 10",
            "research_project_id": "RP-1545",
            "analysis_type": "Resequencing",
            "sample_id": "RP-1545_16177_CCPM_1300040_BLOOD_v4_Exome_DBGAP",
            "submission_metadata": "[{'key': 'library_preparation_kit_vendor', 'value': 'Kapa BioSystems'}, {'key': 'target_capture_kit_name', 'value': 'Nextera Exome Kit (96 Spl)'}, {'key': 'library_preparation_kit_catalog_number', 'value': 'KK8504'}, {'key': 'target_capture_kit_catalog_number', 'value': '20020617'}, {'key': 'target_capture_kit_target_region', 'value': 'http://support.illumina.com/content/dam/illumina-support/documents/documentation/chemistry_documentation/samplepreps_nextera/nexterarapidcapture/nexterarapidcapture_exome_targetedregions_v1.2.bed'}, {'key': 'library_preparation_kit_name', 'value': 'KAPA Hyper Prep Kit with KAPA Library Amplification Primer Mix (10X).'}, {'key': 'library_preparation_kit_version', 'value': 'v1.1'}, {'key': 'target_capture_kit_vendor', 'value': 'Illumina'}]",
            "standard_deviation": 71.34563,
            "read_structure": "76T8B8B76T",
            "analysis_date": "2019-08-29 00:00:00",
            "molecular_barcode_name": "Illumina_P5-Nawoh_P7-Najod",
            "root_sample_id": "SM-J461C",
            "flowcell_barcode": "H3G2HCCX2",
            "individual_alias": "16177_CCPM_1300040",
            "run_name": "190827_SL-HXT_0734_BFCH3G2HCCX2",
            "product_part_number": "P-EX-0040",
            "reference_sequence_name": "Homo_sapiens_assembly19",
            "research_project_name": "Tolaney_Wagle (DFCI) - 16-177 ER+ and HER- Metastatic Breast Cancer",
            "sample_lsid": "broadinstitute.org:bsp.prod.sample:JD5I5"
        },
        "entityType": "read-group",
        "name": "H3G2HCCX2.8.4.RP-1545.16177_CCPM_1300040_BLOOD"
        }
    ]

    """
    sample = Sample(sample_json, md5)
    read_group = ReadGroup(read_group_json)

    experiment = Experiment(sample, read_group)
    experiment.create_file()

    run = Run(sample, read_group, experiment)
    run.create_file()

    submission = Submission(experiment, run, sample.phs)
    submission.create_file()

    print("Done creating xml files")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')
    parser.add_argument(
        '-w',
        '--workspace_name',
        required=True,
        help='name of workspace in which to make changes'
    )
    parser.add_argument(
        '-p',
        '--project',
        required=True,
        help='billing project (namespace) of workspace in which to make changes'
    )
    parser.add_argument('-s', '--sample_id', required=True, help='sample_id to extract read data')
    parser.add_argument('-m', '--md5', required=True, help='md5 value for the sample')
    args = parser.parse_args()

    run_xml_creation(args.sample_id, args.project, args.workspace_name, args.md5)
