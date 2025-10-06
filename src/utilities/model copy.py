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
logger = logging.getLogger(__name__)

load_dotenv()

parser = configparser.ConfigParser()
parser.read("config.ini")  # Ensure your config file is loaded

BASE_MODEL_URL = parser.get("MODEL_CONFIG", "MASMPD_BASE_URL", fallback="")
BASE_MODEL_NAME = parser.get("MODEL_CONFIG", "MASMPD_BASE_MODEL", fallback="meta-llama/Llama-3.1-8B-Instruct")
BASE_API_KEY = os.getenv("MODEL_API_KEY", "")

class MASModel(ModelProvider):
    def __init__(self, 
                 model_name: str = BASE_MODEL_NAME, 
                 model_url: Optional[str] = BASE_MODEL_URL,
                 api_key: Optional[str] = BASE_API_KEY,
                 disable_tracing: bool = False):

        if not model_name or not model_url or not api_key:
            raise ValueError(
                "Please set the model_name, model_url, and api_key via environment variables or parameters."
            )

        self.model_name = model_name
        
        if not self.model_name.startswith("gpt"):
            self.client = AsyncOpenAI(
                base_url=model_url,
                api_key=api_key,
               
            )
        set_tracing_disabled(disabled=disable_tracing)

    def get_model(self):

        if self.model_name.startswith("gpt"):
            return self.model_name
        return OpenAIChatCompletionsModel(
            model=self.model_name,
            openai_client=self.client
        )
       

    def disable_tracing(self):
        set_tracing_disabled(disabled=True)
        logger.info("Tracing has been disabled for the model.")
    def enable_tracing(self):   
        set_tracing_disabled(disabled=False)
        logger.info("Tracing has been enabled for the model.")
        
