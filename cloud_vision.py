from google.cloud import storage
import json
import re
from google.cloud import vision
import sys
from langchain_google_genai import GoogleGenerativeAI
from datetime import datetime
from cloud_datastore import model_instance
import asyncio
from concurrent.futures import ThreadPoolExecutor

llm = GoogleGenerativeAI(model="gemini-1.5-flash",temperature=0)
date_formatted = datetime.now().strftime('%Y-%m-%d')
json_file_name = f"json_data_{date_formatted}.json"

def send_to_datastore(data):
    # Parse the JSON-like data into a Python dictionary if it's a string
    if isinstance(data, str):
        data = json.loads(data)
    # Parse the date_time field to a datetime object
    date_time_obj = datetime.fromisoformat(data["date_time"])

    # Format date and time separately
    date_str = date_time_obj.strftime("%Y-%m-%d")
    time_str = date_time_obj.strftime("%H:%M:%S")  # 24-hour format

    # Update the dictionary with separate date and time
    data["date"] = date_str
    data["time"] = time_str
    # Remove the original date_time field if no longer needed
    del data["date_time"]
    bill_type = data["bill_type"]
    date = data["date"]
    time =data["time"]
    total_amount = data["total_amount"]
    state = data["location"]["state"]
    city = data["location"]["city"]
    vendor_name = data["vendor_name"]
  
    model_instance.insert(bill_type ,vendor_name , date, time ,total_amount , city, state)
    
    return f"Data sent to the datastore"
    

def async_detect_document(gcs_source_uri, gcs_destination_uri):
    """OCR with PDF/TIFF as source files on GCS"""


    # Supported mime_types are: 'application/pdf' and 'image/tiff'
    mime_type = "application/pdf"

    # How many pages should be grouped into each json output file.
    batch_size = 2

    client = vision.ImageAnnotatorClient()

    feature = vision.Feature(type_=vision.Feature.Type.DOCUMENT_TEXT_DETECTION)

    gcs_source = vision.GcsSource(uri=gcs_source_uri)
    input_config = vision.InputConfig(gcs_source=gcs_source, mime_type=mime_type)
    
    gcs_destination = vision.GcsDestination(uri=gcs_destination_uri)
    output_config = vision.OutputConfig(
        gcs_destination=gcs_destination, batch_size=batch_size
    )
    
    async_request = vision.AsyncAnnotateFileRequest(
        features=[feature], input_config=input_config, output_config=output_config
    )

    operation = client.async_batch_annotate_files(requests=[async_request])

    print("Waiting for the operation to finish.")
    operation.result(timeout=420)

    # Once the request has completed and the output has been
    # written to GCS, we can list all the output files.
    storage_client = storage.Client()

    match = re.match(r"gs://([^/]+)/?(.*)", gcs_destination_uri.strip())
    bucket_name = match.group(1)
    prefix = match.group(2)

    bucket = storage_client.get_bucket(bucket_name)

    # List objects with the given prefix, filtering out folders.
    blob_list = [
        blob
        for blob in list(bucket.list_blobs(prefix=prefix))
        if not blob.name.endswith("/")
    ]

    # Process the first output file from GCS.
    # Since we specified batch_size=2, the first response contains
    # the first two pages of the input file.
    output = blob_list[0]

    json_string = output.download_as_bytes().decode("utf-8")
    response = json.loads(json_string)

    # The actual response for the first page of the input file.
    first_page_response = response["responses"][0]
    annotation = first_page_response["fullTextAnnotation"]
    
    prompt = f"""You are an AI trained to convert the given text into a structured JSON response. Analyze the text provided in the context, and return the response strictly in JSON format. Use 'nan' for any missing fields.
    Extract and classify the context into a JSON structure as per the given specification. Ensure the bill_type is classified into one of the specified categories: 'restaurant', 'public transport', 'hotel', 'retail', 'taxi', 'tourist attraction'. The response should only include the fields: bill_type, total_amount, vendor_name, date and time (with timezone), and geographical location (city, state, and country). If there is no total amount visible, use the subtotal and add the tax if it's a numerical value; if tax is not numerical or not present, use just the subtotal.
    
    context: {annotation["text"]}
    
    Example: 
    If hotel the json will look like below
    "bill_type": "hotel",
    "vendor_name": "Hotel Example",
    "date_time": "2024-06-05T12:00:00-05:00",
    "total_amount": 199.99,
    "location": 
      "city": "San Francisco",
      "state": "California",
      "country": "USA"
    
    If public_transport the json will look like below
    "bill_type": "public_transport",
    "vendor_name": "City Transit",
    "date_time": "2024-06-05T09:00:00-05:00",
    "total_amount": 3.50,
    "location": 
      "city": "Chicago",
      "state": "Illinois",
      "country": "USA"
   If restaurant the json will look like below 
    "bill_type": "restaurant",
    "vendor_name": "Grill House",
    "date_time": "2024-06-05T19:30:00-05:00",
    "total_amount": 45.75,
    "location": 
      "city": "Austin",
      "state": "Texas",
      "country": "USA"
    If retail the json will look like below
     "bill_type": "retail",
     "vendor_name": "Retail Store",
     "date_time": "2024-06-05T15:45:00-05:00",
     "total_amount": 80.20,
     "location": 
       "city": "New York",
       "state": "New York",
       "country": "USA"
    If taxi the json will look like below
    "bill_type": "taxi",
    "vendor_name": "City Cabs",
    "date_time": "2024-06-05T22:15:00-05:00",
    "total_amount": 27.00,
    "location": 
      "city": "Las Vegas",
      "state": "Nevada",
      "country": "USA"
    If tourist_attraction the json will look like below
    "bill_type": "tourist_attraction",
    "vendor_name": "City Museum",
    "date_time": "2024-06-05T14:00:00-05:00",
    "total_amount": 30.00,
    "location":
      "city": "Philadelphia",
      "state": "Pennsylvania",
      "country": "USA"
    If cafe the json will look like below
      "bill_type": "cafe",
      "vendor_name": "Central Perk",
      "date_time": "2024-06-05T10:30:00-05:00",
      "total_amount": 12.50,
      "location": 
        "city": "Seattle",
        "state": "Washington",
        "country": "USA"
    if gas the json will look like below
      "bill_type": "gas",
      "vendor_name": "Gas Station",
      "date_time": "2024-06-05T08:00:00-05:00",
      "total_amount": 50.00,
      "location": 
        "city": "Denver",
        "state": "Colorado",
        "country": "USA"
    """
    
    response = llm.invoke(prompt)
    
    formatted_data = response.strip('`json\n').strip('`\n')
    send_to_datastore(formatted_data)

async def process_blob(executor, blob_name, bucket_name, destination_bucket_name):
    """Asynchronous wrapper to process each blob using threading."""
    print(f'Processing file: {blob_name}')
    source_bucket = f"gs://{bucket_name}/{blob_name}"
    dest_bucket = f"gs://{destination_bucket_name}/{blob_name}-"
    await asyncio.get_running_loop().run_in_executor(
        executor, async_detect_document, source_bucket, dest_bucket
    )

async def process_specific_file(bucket_name, destination_bucket_name, filename):
    """Process a specific file in the specified bucket."""
    with ThreadPoolExecutor() as executor:
        await process_blob(executor, filename, bucket_name, destination_bucket_name)


