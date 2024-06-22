from flask import Flask, request, redirect, url_for, render_template
import os
from dotenv import load_dotenv
from cloud_datastore import model_instance 
from image_to_pdf import image_to_pdf


app = Flask(__name__)
load_dotenv()  # This loads the environment variables from .env file.
cwd = os.getcwd()

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'image' in request.files:
        image = request.files['image']
        if image.filename != '':
            # Paths retrieved from environment variables
            image_path = os.path.join(cwd, os.getenv('IMAGE_SAVE_PATH'))
            pdf_output_path = os.path.join(cwd, os.getenv('PDF_OUTPUT_PATH'))
            bucket_name = os.getenv('BUCKET_NAME')
            dest_bucket_name = os.getenv('DEST_BUCKET_NAME')
            output_file_name = os.getenv('PDF_OUTPUT_FILE_NAME')

            # Save the image in a secure way or process it
            image.save(image_path)
            image_to_pdf(image_path, pdf_output_path, bucket_name, dest_bucket_name, output_file_name)
    return redirect(url_for('listItems'))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/list')
def listItems():
    results = model_instance.select()  # This should fetch data and return a list of dictionaries.
    return render_template('list.html', bills=results)  # No need to specify './templates/'

@app.route('/edit')
def editItems():
    results = model_instance.select()  # This should fetch data and return a list of dictionaries.
    return render_template('edit.html', bills=results)  # No need to specify './templates/'

@app.route('/update', methods=['POST'])
def update():
    """
    Update the record when the update button is pressed
    """
    bill_id = request.form.get('id')
    updated_data = {
        'bill_type': request.form.get('bill_type'),
        'vendor_name': request.form.get('vendor_name'),
        'date': request.form.get('date'),
        'time': request.form.get('time'),
        'total_amount': float(request.form.get('total_amount')),
        'city': request.form.get('city'),
        'state': request.form.get('state')
    }
    result =  model_instance.update(bill_id, updated_data) # Assumes you have an update method
    if result:
        return redirect(url_for('listItems'))
    else:
        return "Update Failed", 500

@app.route('/delete', methods=['POST'])
def delete():
        """
        Delete the record when the delete button is pressed
        """
        bill_id = request.form.get('id')
        bill_id = int(bill_id)
        model_instance.delete(bill_id)
        return redirect(url_for('listItems'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)  # Listen on all network interfaces.