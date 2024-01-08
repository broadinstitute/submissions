import os
import logging
import subprocess
import argparse

logging.basicConfig(
    format="%(levelname)s: %(asctime)s : %(message)s", level=logging.INFO
)

ENCRYPTED_FILE_PREFIX = "encrypted_"

def encrypt_file(aggregation_path: str, crypt4gh_encryption_key: str) -> None:
    """
    Encrypts the given data file using crypt4gh.

    Parameters:
    - aggregation_path (str): The file to encrypt.
    - crypt4gh_encryption_key (str): The key supplied by EGA.
    """
    filename = os.path.basename(aggregation_path)
    # leaving this for now. Will need to reach out to ega on the file naming
    # probably doesnt matter
    #output_file = f"{ENCRYPTED_FILE_PREFIX}{filename}.c4gh"
    output_file = f"{filename}"
    command = f'crypt4gh encrypt --recipient_pk {crypt4gh_encryption_key} < {aggregation_path} > {output_file}'

    try:
        subprocess.run(command, check=True, capture_output=True, shell=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Error encrypting file: {e.stderr.decode()}") from e

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Encrypt the given data file using crypt4gh"
    )
    parser.add_argument(
        "--aggregation_path", required=True, help="The file to encrypt"
    )
    parser.add_argument(
        "--crypt4gh_encryption_key", required=True, help="The key supplied by EGA"
    )
    args = parser.parse_args()

    logging.info("Starting script to encrypt data file")

    encrypt_file(args.aggregation_path, args.crypt4gh_encryption_key)

    logging.info("Script finished")