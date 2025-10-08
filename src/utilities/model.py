import asyncio
import os
from dotenv import load_dotenv
from typing import Optional

from openai import AsyncOpenAI
from agents import (
    ModelProvider,
    OpenAIChatCompletionsModel,
    set_tracing_disabled,
)
import configparser
import logging

from agents.extensions.models.litellm_model import LitellmModel
from litellm import BadRequestError, NotFoundError, Timeout


logger = logging.getLogger(__name__)

load_dotenv()

parser = configparser.ConfigParser()
parser.read("config.ini")  # Ensure your config file is loaded

BASE_MODEL_NAME = parser.get("MODEL_CONFIG", "MASMPD_BASE_MODEL", fallback="gpt-4o-mini")
BASE_API_KEY = os.getenv("MODEL_API_KEY", "")
class MASModel():
    def __init__(self, 
                 model_name: str = BASE_MODEL_NAME, 
                 api_key: str = BASE_API_KEY,
                 disable_tracing: bool = False):

        if not model_name or not api_key:
            logger.error(
                "Model initialization failed: model_name, model_url, and api_key must be provided."
            )
            raise ValueError(
                "Please set the model_name, model_url, and api_key via environment variables or parameters."
            )

        self.model_name = model_name
        try:
            self.model = LitellmModel(model=self.model_name, api_key=api_key)
             
                
        except (BadRequestError, NotFoundError, Timeout) as e:
            logger.error(f"Failed to initialize model {self.model_name}: {e}")
            raise
        set_tracing_disabled(disabled=disable_tracing)

    def get_model(self):
        """get model"""
        
        return self.model

    def disable_tracing(self):
        """Disable teacing"""
        set_tracing_disabled(disabled=True)
        logger.info("Tracing has been disabled for the model.")
        
    def enable_tracing(self):   
        set_tracing_disabled(disabled=False)
        logger.info("Tracing has been enabled for the model.")
        
        
