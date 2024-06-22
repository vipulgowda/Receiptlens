from PIL import Image
from fpdf import FPDF
from google.cloud import storage
import os
import asyncio
from cloud_vision import process_specific_file


def image_to_pdf(image_filename, output_filename, bucket_name, dest_bucket_name, output_file):
    """
    Converts a single image (JPEG or PNG) to a PDF file and uploads it to Google Cloud Storage.

    Args:
    image_filename (str): Path to the image file.
    output_filename (str): Name of the resulting PDF to save and upload.
    bucket_name (str): Name of the Google Cloud Storage bucket to upload the PDF.
    """
    # Open the image with Pillow
    with Image.open(image_filename) as img:
        # Convert image to RGB if not already
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Get image dimensions in pixels
        width_px, height_px = img.size
        
        # Convert dimensions from pixels to points (72 points/inch)
        # Assuming the image DPI is the typical 72 (if not specified in the image metadata)
        width_pt = width_px * (72 / img.info.get('dpi', (72, 72))[0])
        height_pt = height_px * (72 / img.info.get('dpi', (72, 72))[0])
        
        # Create instance of FPDF class, use 'P' for portrait and 'L' for landscape based on image dimensions
        orientation = 'P' if width_pt <= height_pt else 'L'
        pdf = FPDF(orientation=orientation, unit="pt", format=(width_pt, height_pt))

        # Add a page to the PDF
        pdf.add_page()

        # Add image to page
        pdf.image(image_filename, 0, 0, width_pt, height_pt)
    
    # Save the PDF to a temporary file
    temp_pdf = f'temp_{output_file}'
    pdf.output(temp_pdf)

    # Initialize a client and upload to Google Cloud Storage
    client = storage.Client()
    bucket = client.get_bucket(bucket_name)
    blob = bucket.blob(output_file)

    # Upload the created PDF
    blob.upload_from_filename(temp_pdf)

    # Optionally, delete the temporary file if needed
    os.remove(temp_pdf)
    
    asyncio.run(process_specific_file(bucket_name, dest_bucket_name, output_file))
    
    
