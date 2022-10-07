task ascpFile {
    File uploadFile
    String uploadSite
    String uploadPath
    String ascpUser

    String gcr_project

    command {
      set -e
      mkdir upload &&
      ascp -k0 -Q -l 500M -i /keys/ncbi_id_rsa.private -T -L upload ${uploadFile} ${ascpUser}@${uploadSite}:${uploadPath};
      ERRORS=$(grep "Source file transfers failed" upload/aspera-scp-transfer.log | rev | cut -f 1 -d ' ');
      [[ $ERRORS[*] =~ '!' ]] && echo "An error was detected during aspera upload." && exit 1
      cat upload/aspera-scp-transfer.log
    }

    runtime {
      docker: "gcr.io/" + gcr_project + "/ascp-client:latest"
      disks: "local-disk 200 HDD"
      memory: "8 GB"
      maxRetries: 1
    }

    output {
        File transferLog = "upload/aspera-scp-transfer.log"
    }
}

workflow TransferFile {
    call ascpFile

    output {
         ascpFile.*
    }
}