from src.utilities.model import MASModel
from src.utilities.package_state import MASState
from typing import Optional


BASE_MODEL = MASModel()
class ClassificationAgentsInterface:
    def __init__(self, 
                state: MASState= MASState(),
                model_name: Optional[str] = None,
                api_key: Optional[str] = None,
                 model_url: Optional[str] = None):

        self.state = state
        if model_name:
            if api_key:
                self.model = MASModel(
                    model_name=model_name,
                    model_url=model_url,
                    api_key=api_key,  # Assuming API key is set in not environment variables
                    disable_tracing= False
                )
            else:
                # If no API key is provided, use the model URL only
                self.model = MASModel(
                    model_name=model_name,
                    model_url=model_url,
                    disable_tracing= False
                )
        else:
            self.model = BASE_MODEL