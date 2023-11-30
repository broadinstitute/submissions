import os
import logging
import subprocess
import argparse

logging.basicConfig(
    format="%(levelname)s: %(asctime)s : %(message)s", level=logging.INFO
)

def encrypt_file(aggregation_path, crypt4gh_encryption_key):
    # Get the filename from the path
    filename = os.path.basename(aggregation_path)
    output_file = f'encrypted_{filename}.c4gh'

    # Command to encrypt data file, writes output to encrypted_{base name of original file}.c4gh
    command = f'crypt4gh encrypt --recipient_pk {crypt4gh_encryption_key} < {aggregation_path} > {output_file}'
    res = subprocess.run(command, capture_output=True, shell=True)

    if res.stderr:
        raise RuntimeError(res.stderr.decode())

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="This script will encrypt the given data file using crypt4gh"
    )
    parser.add_argument(
        "-aggregation_path",
        required=True,
        help="The file to encrypt"
    )
    parser.add_argument(
        "-crypt4gh_encryption_key",
        required=True,
        help="The key supplied by ega"
    )
    args = parser.parse_args()
    logging.info("Starting script to encrypt data file")

    encrypt_file(args.aggregation_path, args.crypt4gh_encryption_key)
    logging.info("Script finished")