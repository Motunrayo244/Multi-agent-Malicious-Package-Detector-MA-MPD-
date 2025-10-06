import configparser
import logging
from src.scripts import setup_logging
from src.agents.ClassifyPackagesAgents import ClassifyPackagesAgents
from src.utilities.package_state import MASState
from agents import (
    set_trace_processors,
    trace
)
from typing import Any
from dotenv import load_dotenv
from langsmith.wrappers import OpenAIAgentsTracingProcessor


set_trace_processors([OpenAIAgentsTracingProcessor()])

classify_agents = ClassifyPackagesAgents()
parser = configparser.ConfigParser()
parser.read("config.ini")  # Ensure your config file is loaded
load_dotenv()

logger = logging.getLogger("classify_package AgentGroup")
async def create_classify_graph(state: MASState)-> dict[str, MASState | Any]:

    with trace(workflow_name="classififier-Service"):

        root_result = await classify_agents.root_agent.run_root_agent(state=state) # type: ignore
        logger.info(f"Root Agent Result completed")
        metadata_result = await classify_agents.metadata_agent.run_metadata_agent(state=state)# type: ignore
        logger.info(f"Metadata Agent Result completed")
        classification_result = await classify_agents.classification_agent.run_classification_agent(state=state) # type: ignore
        logger.info(f"Classification Agent Result completed")

    return {
        "state": state.model_dump(),
        "root_result": root_result,
        "metadata_result": metadata_result,
        "classification_result": classification_result
    } # type: ignore
    
async def classify(package_path: str, guidelines:str) -> dict[str, MASState | Any]:
    """creates the states of a classification and classifies the package."""
    logger.info(f"Starting classification for package: {package_path}")
    state = MASState(package_location=package_path, guidelines=guidelines)
    return await create_classify_graph(state)