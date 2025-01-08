import csv
import json
import boto3
import pprint
import psycopg2
from psycopg2 import sql
from datetime import datetime

# Create S3 client
s3 = boto3.client("s3")

bucket_name = "og82-drop-turing"

assets = []
assets_not_found = []

def create_connection():
    """Create a connection to the PostgreSQL database."""
    conn = psycopg2.connect(
       dbname=  os.getenv("DB_NAME") or 'track_s3'
       user=  os.getenv("USER_NAME") or 'postgres'
       password=  os.getenv("PASSWORD") or  '123456'
       host=   os.getenv("HOST") or  'localhost'
       port=   os.getenv("PORT") or '5432'
    )
    return conn

def insert_into_deliverables_table(records):
    """Insert multiple deliverable_id, project_name, s3_path, and last_modified into the deliverables in bulk."""
    query = sql.SQL("""
        INSERT INTO deliverables (deliverable_id, project_name, s3_path, last_modified)
        VALUES (%s, %s, %s, %s)
        RETURNING id;
    """)

    try:
        conn = create_connection()
        cursor = conn.cursor()
        current_time = datetime.now()
        
        # Prepare the data for insertion
        data_to_insert = [(record['deliverable_id'], record['project_name'], record['s3_path'], current_time) for record in records]

        # Use executemany for bulk insertion
        cursor.executemany(query, data_to_insert)
        conn.commit()

        print(f'Inserted {cursor.rowcount} records into deliverables_table.')
    except Exception as err:
        print('Error inserting into deliverables_table:', err)
    finally:
        cursor.close()
        conn.close()

def get_assets_list():
    """Fetches a list of asset names from the specified S3 bucket."""
    global assets  # To modify the global assets list

    count = 0

    # Paginator used to get more than 1000 objects
    paginator = s3.get_paginator("list_objects_v2")
    pages = paginator.paginate(Bucket=bucket_name)

    # Iterate through pages and collect asset names
    for page in pages:
        if 'Contents' in page:  # Check if there are any objects in the page
            for obj in page['Contents']:
                image = obj["Key"].split("/")[-1]  # Get the image name from the key
                isJson = image.strip().endswith('.json')

                # Check if the image is a JSON file
                if isJson:
                    count += 1
                    assets.append(obj)  # Append the JSON file object to the assets list

    print(f"Total assets found: {count}")
    return assets  # Return the list of assets

def read_json_from_s3(json_key):
    """
    Reads a JSON file from the S3 bucket and returns the parsed data.
    :param json_key: The key (path) of the JSON file in the S3 bucket.
    :return: Parsed JSON data (as Python dict or list).
    """
    try:
        # Download the JSON file from S3 as a stream
        response = s3.get_object(Bucket=bucket_name, Key=json_key)
        content = response['Body'].read().decode('utf-8')  # Read and decode the file content

        # Parse the JSON content
        json_data = json.loads(content)

        return json_data
    except Exception as e:
        print(f"Error reading {json_key}: {e}")
        return None

def fetch_unique_deliverable_ids_with_project_name(assets_list):
    """
    Iterates through the assets list and fetches the unique deliverable_id and project ID from each JSON file.
    :return: A list of dictionaries with project_name and deliverable_id.
    """
    results = []  # List to store deliverable IDs and project IDs
    
    for asset in assets_list:
        json_key = asset['Key']  # The S3 key of the JSON file
        last_modified = asset['LastModified']
        # Extract project ID (the part before the first slash in the S3 key)
        project_name = json_key.split('/')[0]

        # Read JSON data from S3
        json_data = read_json_from_s3(json_key)
        print(f"Deliverable ID from {json_key}:")

        # If JSON data is an array, iterate through it
        if json_data and isinstance(json_data, list):
            for json_obj in json_data:
                # Check if each object in the array has the deliverable_id key
                if 'deliverable_id' in json_obj:
                    deliverable_id = json_obj['deliverable_id']

                    # Append the result as a dictionary
                    results.append({
                        'project_name': project_name,
                        'deliverable_id': deliverable_id,
                        's3_path': json_key,
                        'last_modified': last_modified.strftime('%Y-%m-%d %H:%M:%S %Z')
                    })
                else:
                    print(f"Deliverable ID not found in object of {json_key}")
        else:
            print(f"Invalid JSON structure or no data in {json_key}")
    
    # Return only unique entries (using a set of tuples to ensure uniqueness)
    unique_results = filter_unique_by_deliverable_id(results)
    
    # Insert unique results into the database in bulk
    insert_into_deliverables_table(unique_results)

    return unique_results

def filter_unique_by_deliverable_id(results):
    seen = set()  # To store unique deliverable_id
    unique_results = []

    for record in results:
        deliverable_id = record['deliverable_id']
        
        if deliverable_id not in seen:
            seen.add(deliverable_id)
            unique_results.append(record)

    return unique_results

# Main execution
if __name__ == "__main__":
    # Fetch and print the asset list
    assets_list = get_assets_list()
    print("Assets List:")
    # print(assets_list)

    # Fetch unique deliverable IDs and project IDs from each JSON file in the assets list
    unique_results = fetch_unique_deliverable_ids_with_project_name(assets_list)
    print("Unique Deliverable IDs and Project IDs:")
    pretty_data = json.dumps(unique_results, indent=4)
    print(len(pretty_data))
