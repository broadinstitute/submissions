from google.cloud import storage
from urllib.parse import urlparse


def get_file_size(aggregation_path):
    client = storage.Client()
    parsed_url = urlparse(aggregation_path)
    bucket_name = parsed_url.netloc
    file_path = parsed_url.path.lstrip("/")

    bucket = client.get_bucket(bucket_name)
    blob = bucket.blob(file_path)
    blob.reload()
    file_size = blob.size
    return int(file_size)

if __name__ == '__main__':
    file_size = get_file_size("gs://fc-c6ec1fc2-6956-4e00-96b3-e6d8afb88a79/G124845/RNA/MBCProject_0337_T2/v1/MBCProject_0337_T2.bam")
    print(file_size)