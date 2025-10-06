from __future__ import annotations as _annotations
import json
import logging
import os
import re
from pathlib import Path
from typing import List
from classificationService.classificationUtilities.extract_package import _unpack_archive, folder_to_json
from classificationService.classificationUtilities.package_state import MASState
from classificationService.classificationUtilities.schemas import Classification

from agents import RunContextWrapper, function_tool

logger = logging.getLogger("tools Logger")

@function_tool(name_override ="check_user_input_is_archieve", use_docstring_info=True)
def is_archieve(ctx: RunContextWrapper[MASState],
                       user_input: str):

    """
    Verify if the folder provided by the user is an archieve or a folder
    
    Args:
    user_file_input: the package path provided by the user.
    
    """
    archieve_extensions = ['.zip', '.tar', '.tar.gz', '.tar.bz2', '.tar.xz', '.tgz', '.tbz2', '.tbz', 'whl']
    if user_input.endswith(tuple(archieve_extensions)):
        return True
    else:
        folder_content = list(Path(user_input).expanduser().resolve().iterdir())
        if len(folder_content) == 0:
            return False
        else:
            for file in folder_content:
                if file.is_file() and file.suffix in archieve_extensions:
                    return True
                elif file.is_dir():
                    return False


@function_tool(name_override ="unpack_archive_tool", use_docstring_info=True)
async def unpack_archive(ctx: RunContextWrapper[MASState],
                       zip_path: str) :
    """
    Unpacks the specified archive into a temporary folder and produces a JSON dump.
    update the context with the path to the formatted package.

    Args:
        zip_path (str): The path to the archive to be unpacked.
    """
    package_formatted_path = _unpack_archive(Path(zip_path).expanduser().resolve())
    
    ctx.context.package_formatted_path = str(package_formatted_path)
    ctx.context.messages.append("Archive extraction and Formatting completed")
   
    assert ctx.context.package_formatted_path is not None, "package_formatted_path is required"
    return f"Updated the path of the formatted package content {package_formatted_path}"


    
@function_tool(name_override="unpack_folders", use_docstring_info=True)
async def unpack_folder(ctx: RunContextWrapper[MASState],
                    folder_path: str):
    """
    Navigates through the input folder, processes the contents, and produces a JSON dump.
    update the context with the path to the formatted package.

    Args:
        folder_path (str): The path to the folder to be processed.
    """
    PLAIN_ROOT   = Path(".temp") / "plain"     # single‑package JSON dumps
    out_json = PLAIN_ROOT / f"{folder_path.split('/')[-1]}_dump.json"

    package_formatted_path = folder_to_json(Path(folder_path).expanduser().resolve(),out_json)
    ctx.context.package_formatted_path = str(package_formatted_path)
    ctx.context.package_location = str(package_formatted_path)
    ctx.context.messages.append("Folder extraction and Formatting completed")
    
    assert ctx.context.package_formatted_path is not None, "package_formatted_path is required"
    
    return f"Updated the path of the formatted package content {package_formatted_path}"


@function_tool(name_override="extract_package_information", use_docstring_info=True)
async def extract_package_info(ctx: RunContextWrapper[MASState],
                               formatted_package_path: str):
    """
    Extracts metadata from the PKG-INFO content, Package name
    - Package version
    - Metadata version
    - Author's name and email
    - Package homepage URL
    - Package summary and full description

    Args:
        formatted_package_path (str): Path to the formatted package JSON data.
    """
    # Check if the file exists
    if not os.path.isfile(formatted_package_path):
        ctx.context.error = f"File does not exist: {formatted_package_path}"
        return ctx

    # Attempt to open and parse the file
    try:
        with open(formatted_package_path, 'r', encoding='utf-8') as f:
            package_content = json.load(f)
    except json.JSONDecodeError as e:
        ctx.context.error = f"Error decoding JSON from the package file: {str(e)}"
        logger.error(f"Error decoding JSON from the package file: {str(e)}")
        
        return ctx
    except Exception as e:
        ctx.context.error = f"Unexpected error while reading the package file: {str(e)}"
        logger.error(f"Unexpected error while reading the package file: {str(e)}")
        return ctx

    # Check if 'PKG-INFO' key exists in the content
    if  "PKG-INFO" not in package_content and "METADATA" not in package_content:
       
        ctx.context.error = "metadata details of the package is not found"
        return ctx

    pkg_info = package_content["PKG-INFO"].get("content", "")  if  "PKG-INFO" in package_content  else   package_content["METADATA"].get("content", "")       # Extract the metadata content
    
    if not pkg_info:
        ctx.context.messages = "PKG-INFO content is empty continue without extracting package info"
        return ctx
    # Initialize dictionary to hold processed metadata
    pkg_info_dict = {}

    # Process the 'PKG-INFO' string line by line
    try:
        for line in pkg_info.split('\n'):
            if ":" in line:
                key, value = line.split(":", 1)  # Split at the first colon
                pkg_info_dict[key.lower().strip()] = value.strip()
    except Exception as e:
        ctx.context.error = f"Error processing PKG-INFO: {str(e)}"
        logger.error(f"Error processing PKG-INFO: {str(e)}")
        return ctx

    # Extract metadata and store it in context
    ctx.context.package_name = pkg_info_dict.get("name", 'NA')
    ctx.context.package_version = pkg_info_dict.get("version", 'NA')
    ctx.context.author_name = pkg_info_dict.get("author", 'NA')
    ctx.context.author_email = pkg_info_dict.get("author-email", 'NA')
    ctx.context.package_homepage = pkg_info_dict.get("home-page", 'NA')
    ctx.context.metadata_version = pkg_info_dict.get("metadata-version", 'NA')
    ctx.context.package_summary = pkg_info_dict.get("summary", 'NA')
    ctx.context.package_description = pkg_info_dict.get("description", 'NA')

    # Successful completion message
    ctx.context.messages.append("Package extraction completed successfully")
    logger.info(f"Package extraction completed successfully for {ctx.context.package_name}")

    return f"Extracted package metadata {pkg_info_dict}"

@function_tool(name_override="get_number_of_package_files", use_docstring_info=True)
async def extract_package_file_info (ctx: RunContextWrapper[MASState],
                    package_formatted_file_path: str):
    """
    Extracts the number of files in the package, including the count of Python files. Details to be extracted include
        - Total number of files in the package
        - Number of Python files
        - List of Python files included
    

    Args:
        package_formatted_file_path (str): The path to the location where the formatted package content is located.
    """
    with open(package_formatted_file_path, 'r', encoding='utf-8') as f:
        package_content = json.load(f)
    num_of_files = len(package_content)
    num_of_python_files = 0
    python_files_list = []
    for filename in package_content.keys():
        if filename.endswith('py'):
            num_of_python_files +=1
            python_files_list.append(filename)

    ctx.context.num_of_files = num_of_files
    ctx.context.num_of_python_files = num_of_python_files
    ctx.context.available_python_files = python_files_list
    ctx.context.messages.append("Information about files in the package extracted")

    assert ctx.context.num_of_files is not None, "num_of_files is required"
    assert ctx.context.num_of_python_files is not None, "num_of_python_files is required"
    assert ctx.context.available_python_files is not None, "available_python_files is required"

    return f"Extracted package file information: {num_of_files} files, {num_of_python_files} Python files, List of Python files: {python_files_list}"


@function_tool(name_override="get_python_script", use_docstring_info=True)
def get_python_script(ctx: RunContextWrapper[MASState], file_name: str) -> str:
    """
    Gets the content of a python file from the JSON formatted package.

    Args:
        file_name (str): The name of the Python script file.
    """
    
    with open(ctx.context.package_formatted_path, 'r', encoding='utf-8') as f:
        package_content = json.load(f)

    file_data = package_content.get(file_name)
    if not file_data:
        ctx.context.error = f"Error: The file {file_name} does not exist in the package."
        return "\n"
    python_script = file_data.get('content', '')
    return python_script



@function_tool(name_override="get_functions_python_script", use_docstring_info=True)
async def get_functions(python_code:str) -> List[str]:
    """
    Splits the Python code into individual functions, returning each function as a string.

    Args:
        python_code (str): The Python code to analyze.
    """
        
    pattern = r'(def\s+\w+\s*\(.*?\):(?:\n[ \t]+.+)+)'

    matches = re.findall(pattern, python_code, re.MULTILINE)

    if not matches:
        return "No function definitions found."

    # Format output: separate each function clearly
    output = []
    for i, func_text in enumerate(matches, 1):
        output.append(f"### Function {i} ###\n{func_text.strip()}\n")

    return output

@function_tool(name_override="get_imported_libraries", use_docstring_info=True)
async def get_imports(python_code: str)-> List[str]:
    """
    Extracts all imported libraries or modules from the given Python code.

    Args:
        python_code (str): The Python code to analyze.
    """
    # Matches:
    #   import module
    #   import module as alias
    #   from module import something
    #   from module.submodule import something
    pattern = r'^\s*(?:import\s+([\w\.]+(?:\s+as\s+\w+)?)|from\s+([\w\.]+)\s+import\s+([\w\.]+))'

    matches = re.findall(pattern, python_code, re.MULTILINE)

    imported_package = set()

    for match in matches:
        if match[0]:  # 'import ...' case
            imported_package.add(match[0].replace(" ", "."))  # Replace spaces with '.' for aliased imports
        elif match[1] and match[2]:  # 'from ... import ...' case
            imported_package.add(f"{match[1]}.{match[2]}")  # Combine the module and submodule

    if not imported_package:
        return "No imports found."

    # Return as sorted list for readability
    return sorted(imported_package)


@function_tool(name_override="is_classification_correct", use_docstring_info=True)
def is_classification_correct(ctx: RunContextWrapper[MASState], classification: Classification, groundtruth: Classification) -> bool:
    """
    Checks if the classification made by the agent is correct.

    Args:
        agent (Agent[MASState]): The classification agent.
    """
    # Get the expected and actual classification results
    expected = ctx.context.expected_classification
    actual = agent.output

    # Compare the results
    return expected == actual



