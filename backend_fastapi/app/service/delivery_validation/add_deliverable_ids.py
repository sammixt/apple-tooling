from datetime import datetime

def add_deliverable_ids(json_data,s3_path,project_name):
    """
    Iterates through the assets list and fetches the unique deliverable_id and project ID from each JSON file.
    :return: A list of dictionaries with project_name and deliverable_id.
    """
    results = []  # List to store deliverable IDs and project IDs
    
    if json_data and isinstance(json_data, list):
        for json_obj in json_data:
            # Extract required data from each JSON object
            deliverable_id = json_obj.get('deliverable_id')
            last_modified = json_obj.get('last_modified', datetime.now())

            if deliverable_id:
                results.append({
                    'project_name': project_name,
                    'deliverable_id': deliverable_id,
                    's3_path': s3_path,
                    'last_modified': last_modified.strftime('%Y-%m-%d %H:%M:%S')
                })
            else:
                print(f"Deliverable ID not found in object: {json_obj}")
    else:
        print(f"Invalid JSON structure or no data found.")

    # Filter only unique entries based on the deliverable_id
    unique_results = filter_unique_by_deliverable_id(results)

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

