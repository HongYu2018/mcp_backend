import boto3

def get_s3_structure_string(bucket_name, aws_access_key, aws_secret_key, region_name, prefix):
    """
    Connects to an AWS S3 bucket and returns a formatted string of all folders and files.
    """
    # --- Create S3 client ---
    s3 = boto3.client(
        's3',
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=aws_secret_key,
        region_name=region_name
    )

    # --- Use paginator to get all keys ---
    paginator = s3.get_paginator('list_objects_v2')
    operation_parameters = {
        'Bucket': bucket_name,
        'Prefix': prefix,
    }

    folders = set()
    files = []

    for page in paginator.paginate(**operation_parameters):
        for content in page.get('Contents', []):
            key = content['Key']
            if key.endswith('/'):
                folders.add(key)
            else:
                # Add folder path from file key
                path_parts = key.split('/')[:-1]
                if path_parts:
                    folders.add('/'.join(path_parts) + '/')
                files.append(key)

    # --- Format output as string ---
    output = ["Folders:"]
    for folder in sorted(folders):
        output.append(f"  - {folder}")

    output.append("\nFiles:")
    for file in sorted(files):
        output.append(f"  - {file}")

    return '\n'.join(output)
