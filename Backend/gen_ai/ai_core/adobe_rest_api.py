import os
import requests
import time
import logging
import asyncio
import aiohttp
import ssl
from django.conf import settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def get_access_token(api_key, api_secret):
    """
    Obtain an access token using JWT.

    Parameters:
    - api_key (str): The API key.
    - api_secret (str): The API secret.

    Returns:
    - str: The access token or None in case of an error.
    """
    try:
        url = "https://pdf-services.adobe.io/token"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        payload = {"client_id": api_key, "client_secret": api_secret}

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=payload) as response:
                if response.status == 200:
                    response_json = await response.json()
                    return response_json.get("access_token")
                else:
                    logger.error(f"Error obtaining access token: {await response.text()}")
                    return None
    except Exception as e:
        logger.exception(f"Exception in get_access_token: {str(e)}")
        return None

async def create_pdf_asset(api_key, access_token, media_type):
    """
    Create a PDF asset.

    Parameters:
    - api_key (str): The API key.
    - access_token (str): The access token.
    - media_type (str): The media type.

    Returns:
    - dict: Asset data or None in case of an error.
    """
    try:
        url = "https://pdf-services.adobe.io/assets"
        headers = {"X-API-Key": api_key, "Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
        payload = {"mediaType": media_type}

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status == 200:
                    asset_data = await response.json()
                    return asset_data
                else:
                    logger.error(f"Error creating PDF asset: {await response.text()}")
                    return None
    except Exception as e:
        logger.exception(f"Exception in create_pdf_asset: {str(e)}")
        return None

async def upload_to_s3(s3_url, pdf_bytesio):
    """
    Upload a file to S3 asynchronously using aiohttp.

    Parameters:
    - s3_url (str): The S3 URL.
    - pdf_bytesio (io.BytesIO): The BytesIO containing the file.

    Returns:
    - None
    """
    try:
        headers = {"Content-Type": "application/pdf"}
        file_bytes = pdf_bytesio.read()

        # Explicitly disable SSL certificate verification
        #connector = aiohttp.TCPConnector(ssl=False)

        #async with aiohttp.ClientSession(connector=connector) as session:
        async with aiohttp.ClientSession() as session:
            async with session.put(s3_url, headers=headers, data=file_bytes) as response:
                if response.status == 200:
                    logger.info("File uploaded successfully.")
                else:
                    logger.error(f"Error uploading file to S3: {await response.text()}")
    except Exception as e:
        logger.exception(f"Exception in upload_to_s3: {str(e)}")

async def create_pdf_extract_job(api_key, access_token, asset_id):
    """
    Create a PDF extract job asynchronously.

    Parameters:
    - api_key (str): The API key.
    - access_token (str): The access token.
    - asset_id (str): The asset ID.

    Returns:
    - str: Job location or None in case of an error.
    """
    try:
        url = "https://pdf-services.adobe.io/operation/extractpdf"
        headers = {"X-API-Key": api_key, "Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

        payload = {
            "assetID": asset_id,
            "getCharBounds": False,
            "includeStyling": False,
            "elementsToExtract": ["text", "tables"],
            "tableOutputFormat": "xlsx",
            "renditionsToExtract": ["tables", "figures"],
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status == 201:
                    job_location = response.headers.get("Location")
                    logger.info(f"Job created successfully. Job location: {job_location}")
                    return job_location
                else:
                    logger.error(f"Error creating PDF extract job: {await response.text()}")
                    return None
    except Exception as e:
        logger.exception(f"Exception in create_pdf_extract_job: {str(e)}")
        return None

async def get_pdf_extract_job_status(api_key, access_token, job_location):
    """
    Get the status of a PDF extract job asynchronously.

    Parameters:
    - api_key (str): The API key.
    - access_token (str): The access token.
    - job_location (str): The job location.

    Returns:
    - dict: Job status or None in case of an error.
    """
    try:
        while True:
            async with aiohttp.ClientSession() as session:
                async with session.get(job_location, headers={"Authorization": f"Bearer {access_token}", "x-api-key": api_key}) as response:
                    if response.status == 200:
                        job_status = await response.json()
                        logger.info(f"Job Status: {job_status}")

                        if job_status["status"] in ["done", "failed"]:
                            return job_status
                        else:
                            # Sleep for a while before polling again
                            await asyncio.sleep(1)
                    else:
                        logger.error(f"Error getting PDF extract job status: {await response.text()}")
                        return None
    except Exception as e:
        logger.exception(f"Exception in get_pdf_extract_job_status: {str(e)}")
        return None

async def download_json_from_adobe_api(download_uri):
    """
    Download JSON content from the Adobe API asynchronously.

    Parameters:
    - download_uri (str): The download URI.

    Returns:
    - dict: Downloaded JSON content or None in case of an error.
    """
    try:
        #async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
        async with aiohttp.ClientSession() as session:    
            async with session.get(download_uri) as response:
                if response.status == 200:
                    json_content = await response.json()
                    logger.info(f"JSON content downloaded successfully")
                    return json_content
                else:
                    logger.error(f"Error downloading JSON content: {await response.text()}")
                    return None
    except Exception as e:
        logger.exception(f"Exception in download_json_from_adobe_api: {str(e)}")
        return None

async def pdf_extract(api_key, api_secret, pdf_name, pdf_bytesio):
    """
    Process a single PDF.

    Parameters:
    - api_key: str
    - api_secret: str
    - pdf_name: str, the name of the PDF file
    - pdf_bytesio: io.BytesIO

    Returns:
    - dict: Extracted content with PDF name
    """
    try:
        # Step 1: Get Access Token
        access_token = await get_access_token(api_key, api_secret)

        # Step 2: Create PDF Asset
        asset_data = await create_pdf_asset(api_key, access_token, media_type="application/pdf")

        # Step 3: Upload to S3
        await upload_to_s3(asset_data.get("uploadUri"), pdf_bytesio)

        # Step 4: Create PDF Extract Job
        job_location = await create_pdf_extract_job(api_key, access_token, asset_data.get("assetID"))

        # Step 5: Get PDF Extract Job Status
        job_status = await get_pdf_extract_job_status(api_key, access_token, job_location)

        # Step 6: Download JSON from Adobe API
        downloaded_json = await download_json_from_adobe_api(job_status.get("content", {}).get("downloadUri"))

        # Include PDF name in the result dictionary
        result = {"pdf_name": pdf_name, "extracted_content": downloaded_json}
        return result
    except Exception as e:
        logger.exception(f"Exception in pdf_extract: {str(e)}")
        return None

async def process_files(pdfDocs):
    """
    Process all PDFs in a list of BytesIO objects asynchronously.

    Parameters:
    - pdfDocs: List[io.BytesIO]

    Returns:
    - List[dict]: Extracted content for each PDF
    """
    try:
        client_id = settings.PDF_SERVICES_CLIENT_ID
        client_secret = settings.PDF_SERVICES_CLIENT_SECRET

        tasks = []
        
        for pdf in pdfDocs:
            task = asyncio.create_task(
                pdf_extract(client_id, client_secret, pdf.name, pdf)
            )
            tasks.append(task)

        json_output = await asyncio.gather(*tasks)

        return json_output
    except Exception as e:
        logger.exception(f"Exception in process_files: {str(e)}")
        return None