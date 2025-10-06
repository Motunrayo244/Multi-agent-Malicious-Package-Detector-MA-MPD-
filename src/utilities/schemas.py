from pydantic import BaseModel
from enum import Enum

class RootAgentOutput(BaseModel):
    package_formatted_path: str
    
class MetadataAgentOutput(BaseModel):
    package_name: str
    package_version: str
    metadata_version: str
    author_name: str
    author_email: str
    package_homepage: str
    package_summary: str
    package_description: str
    num_of_files: int
    num_of_python_files: int
    available_python_files: list[str]
    
class Classification(str, Enum):
    benign = "benign"
    malicious = "malicious"

class ClassificationAgentOutput(BaseModel):
    classification: Classification
    justification: str
    suspicious_files: list[str] = []


