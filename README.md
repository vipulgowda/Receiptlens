# ReceiptLens: Vision and Gemini AI-Powered Receipt Analysis

## Overview

ReceiptLens leverages the capabilities of Vision and Gemini AI technologies to provide advanced analysis of receipt data. This project integrates Google Cloud Vision and the Gemini pro large language model (LLM) to extract and interpret information from receipts for seamless data management and analytics.

## Features

- **Receipt Scanning**: Utilize Google Cloud Vision to accurately scan and digitize receipts.
- **Textual Insight**: Employ Gemini LLM to extract and analyze text from receipts, enhancing data accuracy and insights and convert to json.
- **Efficient Data Storage**: Stores the data efficiently

## Prerequisites

Ensure you have the following before starting:
- A Google Cloud account
- API access for Google Cloud Vision and Vertex AI
- Python 3.8 or higher
- Appropriate credentials for Google Cloud services

## Setting Up the Environment

To use ReceiptLens, you need to enable several services in your Google Cloud project. Here are the necessary steps:

1. Enable the Gcloud services:
   ```bash
   gcloud services enable \
    generativelanguage.googleapis.com \
    vision.googleapis.com \
    datastore.googleapis.com \
    storage.googleapis.com

2. Service account creation
    ```bash
    gcloud iam service-accounts create final-cs430

3. Create IAM policies for services account
    ```bash
     gcloud projects add-iam-policy-binding [YOUR_PROJECT_ID] \
     --member="serviceAccount:final-cs430@[YOUR_PROJECT_ID].iam.gserviceaccount.com" \
     --role="roles/datastore.user"

     gcloud projects add-iam-policy-binding [YOUR_PROJECT_ID] \
     --member="serviceAccount:final-cs430@[YOUR_PROJECT_ID].iam.gserviceaccount.com" \
     --role="roles/serviceusage.serviceUsageConsumer"

     gcloud projects add-iam-policy-binding [YOUR_PROJECT_ID] \
     --member="serviceAccount:final-cs430@[YOUR_PROJECT_ID].iam.gserviceaccount.com" \
     --role="roles/storage.admin"

     gcloud projects add-iam-policy-binding [YOUR_PROJECT_ID] \
     --member="serviceAccount:final-cs430@[YOUR_PROJECT_ID].iam.gserviceaccount.com" \
     --role="roles/storage.objectAdmin"

     gcloud projects add-iam-policy-binding [YOUR_PROJECT_ID] \
     --member="serviceAccount:final-cs430@[YOUR_PROJECT_ID].iam.gserviceaccount.com" \
     --role="roles/vision.admin"

4. Create key file 
    ```bash
      gcloud iam service-accounts keys create final_cs430.json \
      --iam-account final-cs430@${GOOGLE_CLOUD_PROJECT}.iam.gserviceaccount.com

4. Export Gemini API key
    ```bash
     export GOOGLE_API_KEY="<FMI>"

5. Create Gcloud Bucket
   ```bash
   gsutil mb gs://<UNIQUE_BUCKET_NAME>
   gsutil mb gs://<UNIQUE_BUCKET_NAME>-json

6. Build the docker image
      ```bash
       gcloud builds submit --timeout=900 --tag gcr.io/${GOOGLE_CLOUD_PROJECT}/final

7. Deploy container with minimal privileges
    ```bash
      gcloud run deploy final \
      --image gcr.io/${GOOGLE_CLOUD_PROJECT}/final \
      --service-account final-cs430@${GOOGLE_CLOUD_PROJECT}.iam.gserviceaccount.com \
      --set-env-vars GOOGLE_API_KEY=<API_KEY>

8. Reset 
    ```bash
      gcloud run services delete final
      gcloud container images delete gcr.io/${GOOGLE_CLOUD_PROJECT}/final
