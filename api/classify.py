import asyncio
import configparser
import json
import logging
import os
from pathlib import Path
import shutil
import tempfile
import uuid
import zipfile

from psycopg2 import pool

import asyncpg
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from pythonjsonlogger.json import JsonFormatter
from src.scripts import classify_package as classifier
from src.utilities.schemas import Classification


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
# Configure root logger to write to a file with appropriate format and level
# logging.basicConfig(
#     level=logging.INFO,  # capture all logs of INFO level and above
#     format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
#     handlers=[
#         logging.FileHandler(log_file, mode='a', encoding='utf-8'),
#         logging.StreamHandler()  
#     ]
# )


parser= configparser.ConfigParser()
parser.read("config.ini")  # Ensure your config file is loaded
global model_name, SERVICE_NAME
model_name = parser.get("MODEL_CONFIG", "MASMPD_BASE_MODEL", fallback="")

SERVICE_NAME =  parser.get("KNOWLEDGE_BASE", "SERVICE_NAME", fallback="ma-mpd-hosted-sevice")

app = FastAPI()
load_dotenv()  # Load environment variables from .env file if needed
TABLE_NAME = parser.get("KNOWLEDGE_BASE", "TABLE_NAME", fallback='mampd_classification')
COMPRESSION_EXTENSIONS = {'.tar.gz','.zip'}
MAX_RETRIES = 2
RETRY_DELAY = 4  # seconds between retries
global custom_temp_dir
custom_temp_dir = os.path.join(os.getcwd(), ".MAMPD_temp")
os.makedirs(custom_temp_dir, exist_ok=True)


async def init_db_pool():
    global db_pool
    db_pool = await asyncpg.create_pool(
        min_size=1,
        max_size=20,
        max_inactive_connection_lifetime=120,
        max_queries=500,
        user=os.getenv("PG_USER"),
        password=os.getenv("PG_PASSWORD"),
        host=os.getenv("PG_DB_HOST"),
        port=int(os.getenv("PG_DB_PORT")),
        database=os.getenv("PG_DB_NAME"),
        server_settings={"search_path": os.getenv("MAS_MPD_SCHEMA")}
    )

async def get_experiment(service_name: str):
    try:
        # Using parameterized queries to avoid SQL injection risk
        query = """
            SELECT id 
            FROM experiments.experiments 
            WHERE experiment_name = $1 AND experiment_status = 'active' 
            ORDER BY updated_at ASC 
            LIMIT 1;
        """
        # Pass the parameters using asyncpg's safe parameterized query
        async with db_pool.acquire() as conn:
            results = await conn.fetch(query, service_name)
        
        if results:
            # Assuming the first result will be returned as a string
            return str(results[0]['id'])  # Extracting the 'id' and returning as string
        else:
            return ""  # Return an empty string if no results found

    except Exception as e:
        # Handling database errors and re-raising as HTTPException
        raise HTTPException(status_code=500, detail=str(e))



@app.on_event("startup")
async def startup_event():
    global EXPERIMENT_ID
    await init_db_pool()
    EXPERIMENT_ID = await get_experiment(SERVICE_NAME) 

async def parse_classification_result(result: dict) -> dict:
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

async def store_classification_result(classification_id: str, data: dict,dataset_id:str, experiment_id:str):
    result_entry = await parse_classification_result(data)  
    async with db_pool.acquire() as conn:
        prompt_id_query = """
            SELECT prompt_id
            FROM experiments.prompts
            WHERE agent='classification Agent'
              AND agent_group='classifier'
              AND status = 'active'
            ORDER BY created_at DESC
            LIMIT 1;
        """
        prompt_id_result = await conn.fetchrow(prompt_id_query)
    
        if not prompt_id_result:
            raise HTTPException(status_code=404, detail="No active prompt found for classification agent")
    
        prompt_id = prompt_id_result['prompt_id']
        result_entry['prompt_id'] = prompt_id
        result_entry['classification_id'] = classification_id
        result_entry['dataset_id'] = dataset_id
        result_entry['experiment_id'] = experiment_id
        
        if isinstance(result_entry.get('package_metadata'), dict):
            result_entry['package_metadata'] = json.dumps(result_entry['package_metadata'])
        
        if isinstance(result_entry.get('suspicious_files'), list):
            result_entry['suspicious_files'] = result_entry['suspicious_files']
            
        # Ensure 'model_name' is defined, or use a fallback
        result_entry['model'] = model_name if 'model_name' in globals() else 'default_model'

        # Prepare the SQL query with dynamic columns
        columns = ', '.join(result_entry.keys())
        placeholders = ', '.join(f"${i + 1}" for i in range(len(result_entry)))
    
        # Construct the insert SQL statement
        sql = f"INSERT INTO {TABLE_NAME} ({columns}) VALUES ({placeholders})"
        
        # Log the query and the values for debugging
        logger.debug(f"SQL Query: {sql}")
        logger.debug(f"Values: {result_entry.values()}")

        try:
            # Execute the query
            status = await conn.execute(sql, *result_entry.values())
            logger.debug(f"Insert status: {status}")

            # Check if insertion was successful
            if status.endswith(" 1"):
                logger.info(f"Insert succeeded for {classification_id}")
            else:
                logger.warning(f"Insert may have failed for {classification_id}")

        except Exception as e:
            # If any error occurs during insert, log it
            logger.error(f"Error executing insert for {classification_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))


async def upload_file_to_temp(upload_file: UploadFile) -> str:
    """Save the uploaded file to a temporary location.
    If compressed archive, save as is.
    If .py file, zip it.
    Otherwise, reject."""
    
    suffix = os.path.splitext(upload_file.filename)[1].lower()
    temp_dir = tempfile.mkdtemp(dir=custom_temp_dir)

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
            # Since upload_file.file is a stream, we need to read and write it into the zip
            # We'll read it into memory here:
            file_contents = await upload_file.read()
            zipf.writestr(upload_file.filename, file_contents)
        return zip_path

    else:
        raise HTTPException(
            status_code=400,
            detail="File format not acceptable. Only compressed archives or .py files are allowed."
        )
        

async def move_folder_to_temp(folder_path: str) -> str:
    temp_dir = tempfile.mkdtemp(dir=custom_temp_dir)
    if not os.path.isdir(folder_path):
        # p = Path(folder_path).resolve()
        # temp_dir = Path(temp_dir)
        # file_path = temp_dir / p.name
        # shutil.copy2(p, file_path)
        # return str(file_path)
        raise HTTPException(status_code=400, detail=f"Provided path is not a folder or does not exist: {folder_path}")
    
    copied_folder_path = os.path.join(temp_dir, os.path.basename(folder_path))
    shutil.copytree(folder_path, copied_folder_path)
    return copied_folder_path


async def upload_file_or_folder(upload_file: UploadFile | None, folder_path: str | None) -> str:
    """Handle the upload of either a file or a folder."""
    if upload_file and folder_path:
        raise HTTPException(status_code=400, detail="Provide only one of file or folder_path")
    
    if upload_file:
        # Save uploaded file to a temp location
        tmp_path = await upload_file_to_temp(upload_file)
        
        return tmp_path

    elif folder_path:
        # Check if folder exists on server
        tmp_path = await move_folder_to_temp(folder_path)
        
        return tmp_path

    else:
        raise HTTPException(status_code=400, detail="No file or folder_path provided")
    
    
@app.post("/classify") 
async def classify(
    upload_file: UploadFile | None = File(default=None),
    folder_path: str | None = Form(default=None),
    dataset_id: str = Form(default=None),
    guideline:str | None = Form(default=None)
    
):
    """Endpoint to classify an uploaded file or folder."""
   
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            classification_id = str(uuid.uuid4())
            temp_path = await upload_file_or_folder(upload_file, folder_path)
            
            classification_result = await classifier.classify(temp_path,guideline)
            classification_result["input_file"] = os.path.basename(temp_path)
            await store_classification_result(classification_id, classification_result,dataset_id, EXPERIMENT_ID )
            return {"classification_id": classification_id}

        except Exception as e:
            # Check if the error message contains 'Max turns exceeded'
            if attempt < MAX_RETRIES:
                logger.error(f"Attempt {attempt} failed , retrying...")
                await asyncio.sleep(RETRY_DELAY)
            else:
                raise HTTPException(status_code=500, detail=f"Max turns exceeded after {MAX_RETRIES} retries: {str(e)}")
            

@app.get("/classification/{classification_id}/result")
async def get_classification_result(classification_id: str):
    try:
        async with db_pool.acquire() as conn:
            query = """
                SELECT * 
                FROM {TABLE_NAME} 
                WHERE classification_id = $1
            """.format(TABLE_NAME=TABLE_NAME)  # Dynamically inserting table name
            result = await conn.fetchrow(query, classification_id)
            if not result:
                raise HTTPException(status_code=404, detail="Classification result not found")
            return dict(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/classification-results")
async def get_classification_results():
    try:
        async with db_pool.acquire() as conn:
            query = """
                SELECT classification_id, package_name, classification, justification, suspicious_files 
                FROM {TABLE_NAME}
            """.format(TABLE_NAME=TABLE_NAME)  # Dynamically inserting table name
            results = await conn.fetch(query)
            if not results:
                raise HTTPException(status_code=404, detail="No classification results found")
            return [dict(result) for result in results]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



    

