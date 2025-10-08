import asyncio
import configparser
import logging
import os
from pathlib import Path
import shutil
import tempfile
import zipfile


import requests

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from pythonjsonlogger.json import JsonFormatter
from src.scripts import classify_package as classifier
from src.utilities.schemas import Classification

load_dotenv()  
# Create logs directory if it doesn't exist
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

# Define log file path
log_file = os.path.join(log_dir, "MAMPD_application_logs.log")
logger = logging.getLogger()
logHandler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
formatter = JsonFormatter("{message}{asctime}{exc_info}", style="{")
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)



parser= configparser.ConfigParser()
parser.read("config.ini")  # Ensure your config file is loaded

global model_name, SERVICE_NAME, CUSTOM_TEMP_DIR
model_name = parser.get("MODEL_CONFIG", "MASMPD_BASE_MODEL", fallback="")
CUSTOM_TEMP_DIR = os.path.join(os.getcwd(), ".MAMPD_temp")
os.makedirs(CUSTOM_TEMP_DIR, exist_ok=True)


COMPRESSION_EXTENSIONS = {'.tar.gz', '.zip'}
MAX_RETRIES = 1
RETRY_DELAY = 4  # seconds between retries
app = FastAPI()

def parse_classification_result(result: dict) -> dict:
    package_name: str = result['state']['package_name']
    if not package_name:
        package_name:str =  result['input_file']
    package_metadata = {
        "package_name": package_name,
        "package_version": result['state']['package_version'],
        "author_name": result['state']['author_name'],
        "author_email": result['state']['author_email'],
        "package_homepage": result['state']['package_homepage'],
        "package_description": result['state']['package_description'],
        "package_summary": result['state']['package_summary'],
        "num_of_files": result['state']['num_of_files'],
        "num_of_python_files": result['state']['num_of_python_files'],
        "available_python_files": result['state']['available_python_files'],
        "package_formatted_path": result['state']['package_formatted_path']
    }
    classification = result['classification_result'].final_output.classification.value
    justification = result['classification_result'].final_output.justification
    suspicious_files = result['classification_result'].final_output.suspicious_files
    
    classification_result_data = {
        "package_name": package_name,
        "package_metadata": package_metadata,
        "classification": classification,
        "justification": justification,
        "suspicious_files": suspicious_files,
        
    }
    return classification_result_data


async def upload_file_to_temp(upload_file: UploadFile) -> str:
    """Save the uploaded file to a temporary location.
    If compressed archive, save as is.
    If .py file, zip it.
    Otherwise, reject."""
    
    suffix = os.path.splitext(upload_file.filename)[1].lower()
    temp_dir = tempfile.mkdtemp(dir=CUSTOM_TEMP_DIR)

    # Check for compressed archive extensions
    if suffix in COMPRESSION_EXTENSIONS or upload_file.content_type in ['application/zip', 'application/x-tar', 'application/gzip']:
        # Save the file as-is into temp_dir
        file_path = os.path.join(temp_dir, upload_file.filename)
        with open(file_path, "wb") as tmp_file:
            shutil.copyfileobj(upload_file.file, tmp_file)
        return file_path

    elif suffix == '.py' and upload_file.content_type in ['text/x-python', 'application/x-python-code', 'text/plain']:
        # Zip the single .py file
        zip_path = os.path.join(temp_dir, upload_file.filename + '.zip')
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            file_contents = await upload_file.read()
            zipf.writestr(upload_file.filename, file_contents)
        return zip_path

    else:
        raise HTTPException(
            status_code=400,
            detail="File format not acceptable. Only compressed archives or .py files are allowed."
        )


async def upload_file_to_temp(upload_file: UploadFile | None) -> str:
    """Handle the upload of either a file or a folder."""
    if upload_file:
        # Save uploaded file to a temp location
        tmp_path = await upload_file_to_temp(upload_file)
        
        return tmp_path
    else:
        raise HTTPException(status_code=400, detail="No file or folder_path provided")
    
def download_pypi_package(package_name, version=None):
    url = f"https://pypi.org/pypi/{package_name}/json"
    resp = requests.get(url)
    resp.raise_for_status()
    info = resp.json()
    version = version or info["info"]["version"]

    releases = info["releases"].get(version)
    if not releases:
        logger.error(f"No release for {package_name}=={version}")
        raise HTTPException(status_code=400, detail=f"No package found for {package_name}=={version}")

    source_file = next((r for r in releases if r["packagetype"] == "sdist"), releases[0])
    download_url = source_file["url"]

    filename = os.path.join(CUSTOM_TEMP_DIR, f"{package_name}-{version}.tar.gz")

    response = requests.get(download_url)
    response.raise_for_status()
    with open(filename, "wb") as f:
        f.write(response.content)

    logger.info(f"Downloaded {filename}")
    return filename

@app.post("/classify") 
async def classify(
    upload_file: UploadFile | None = File(default=None),
    package_name: str | None = Form(default=None),
    version: str | None = Form(default=None)
):
    """Endpoint to classify an uploaded file or folder."""
    temp_path = None    
    if upload_file:
        temp_path = await upload_file_to_temp(upload_file)
        
    elif package_name:
        temp_path = download_pypi_package(package_name, version)
    else:
        raise HTTPException(status_code=400, detail="No package name or upload file provided ")
    
    try:
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                classification_result = await classifier.classify(temp_path)
                result_data = parse_classification_result(classification_result)
                return result_data

            except Exception as e:
                # Check if the error message contains 'Max turns exceeded'
                if attempt < MAX_RETRIES:
                    logger.error(f"Attempt {attempt} failed , retrying...")
                    await asyncio.sleep(RETRY_DELAY)
                else:
                    raise HTTPException(status_code=500, detail=f"Max turns exceeded after {MAX_RETRIES} retries: {str(e)}")
    finally:
        # Clean up temporary files/directories
        try:
            if temp_path and os.path.exists(temp_path):
                if os.path.isdir(temp_path):
                    # If it's a directory, remove it
                    shutil.rmtree(temp_path)
                else:
                    # If it's a file, check if it's in a temp subdirectory or directly in CUSTOM_TEMP_DIR
                    parent_dir = os.path.dirname(temp_path)
                    if parent_dir != CUSTOM_TEMP_DIR and parent_dir.startswith(CUSTOM_TEMP_DIR):
                        # File is in a temp subdirectory (uploaded file case), remove the parent directory
                        shutil.rmtree(parent_dir)
                    else:
                        # File is directly in CUSTOM_TEMP_DIR (downloaded package case), just remove the file
                        os.remove(temp_path)
        except Exception as cleanup_error:
            logger.error(f"Error during cleanup: {cleanup_error}")
    



    

