version 1.0

import "../../tasks/terra_tasks.wdl" as tasks

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
        File? monitoring_script
    }

    call tasks.CreateDbgapXmlFiles as xml {
        input:
            workspace_name = workspace_name,
            billing_project = workspace_project,
            sample_id = sample_id,
            monitoring_script = monitoring_script
    }

    call ascpFile as transferXml {
        input:
            key = key,
            uploadFile = xml.xml_tar,
            uploadSite = uploadSite,
            uploadPath = uploadPath,
            ascpUser = "asp-bi",
            filename = "xml_tar.xml"
    }

    call ascpFile as transferDataFile {
        input:
            key = key,
            uploadFile = dataFile,
            uploadSite = transferXml.site,
            uploadPath = transferXml.path,
            ascpUser = "asp-bi",
            filename = "~{sample_id}.bam"
    }
}

task ascpFile {
    input {
        File uploadFile
        File key
        String uploadSite
        String uploadPath
        String ascpUser
        String filename
    }

    command {
      set -e
      mkdir upload &&
      mv ~{key} upload/private.openssh
      mv ~{uploadFile} upload/~{filename}
      ascp -k0 -Q -l 500M -i upload/private.openssh -T -L upload upload/~{filename} ${ascpUser}@${uploadSite}:${uploadPath};
      ERRORS=$(grep "Source file transfers failed" upload/aspera-scp-transfer.log | rev | cut -f 1 -d ' ');
      [[ $ERRORS[*] =~ '!' ]] && echo "An error was detected during aspera upload." && exit 1
      cat upload/aspera-scp-transfer.log
      cd upload
      ls
    }

    runtime {
      memory: "7.5 GB"
      docker: "schaluvadi/horsefish:submissionV1"
      cpu: 2
      disks: "local-disk 200 HDD"
    }

    output {
        File transferLog = "upload/aspera-scp-transfer.log"
        String site = uploadSite
        String path = uploadPath
    }
}
