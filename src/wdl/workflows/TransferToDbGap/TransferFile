import "../../tasks/terra_tasks.wdl" as tasks

task ascpFile {
    File uploadFile
    File key
    String uploadSite
    String uploadPath
    String ascpUser

    command {
      set -e
      mkdir upload &&
      ascp -k0 -Q -l 500M -i ${key} -T -L upload ${uploadFile} ${ascpUser}@${uploadSite}:${uploadPath};
      ERRORS=$(grep "Source file transfers failed" upload/aspera-scp-transfer.log | rev | cut -f 1 -d ' ');
      [[ $ERRORS[*] =~ '!' ]] && echo "An error was detected during aspera upload." && exit 1
      cat upload/aspera-scp-transfer.log
    }

    runtime {
      memory: "7.5 GB"
      docker: "schaluvadi/horsefish:submissionV1"
      cpu: 2
      preemptible: 3
      disks: "local-disk 200 HDD"
    }

    output {
        File transferLog = "upload/aspera-scp-transfer.log"
    }
}

workflow TransferToDbgap {
    input {
        String sample_id
        String workspace_name
        String workspace_project
        String uploadSite
        String uploadPath
        String ascpUser
        File key
        File dataFile
    }

    call tasks.CreateDbgapXmlFiles as xml {
        input:
            workspace_name = workspace_name,
            billing_project = workspace_project,
            sample_id = sample_id,
    }

    call ascpFile as transferXml {
        input:
            key = key,
            uploadFile = xml.xml_tar,
            uploadSite = uploadSite,
            uploadPath = uploadPath,
            ascpUser = "asp-bi"
    }

    call ascpFile as transferDataFile {
        input:
            key = key,
            uploadFile = dataFile,
            uploadSite = uploadSite,
            uploadPath = uploadPath,
            ascpUser = "asp-bi"
    }

    output {
         ascpFile.*
    }
}