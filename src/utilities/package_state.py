from pydantic import BaseModel, Field
from typing import Any, Optional, Dict, List
from typing_extensions import Annotated


class MASState(BaseModel):
    package_location: str = ""
    package_name: Optional[str] = None
    package_version: Optional[str] = None
    metadata_version: Optional[str] = None
    author_name: Optional[str] = None
    author_email: Optional[str] = None
    package_homepage: Optional[str] = None
    package_summary: Optional[str] = None
    package_description: Optional[str] = None

    package_formatted_path: Optional[str] = None

    num_of_files: Optional[int] = None
    num_of_python_files: Optional[int] = None

    available_python_files: List[str] = Field(default_factory=list)
    package_behaviour: Dict[str, Any] = Field(default_factory=dict)
    suspicious_malicious_files: Dict[str, Any] = Field(default_factory=dict)
    guidelines: Optional[str] = None

    messages: List[str] = Field(default_factory=list)
    package_class: Annotated[List[Any], None] = Field(default_factory=list) 
    classification_explanation: Annotated[List[Any], None] = Field(default_factory=list)
    error: Optional[str] = None

    async def add_message(self, update: Any) -> None:
        self.messages.append(str(update))

    async def updated(self, **changes) -> "MASState":
        return self.copy(update=changes)
    
    async def get_formated_path(self) -> str:
        if self.package_formatted_path is None:
            raise ValueError("Package formatted path is not set.")
        return self.package_formatted_path



