import logging
from agents import Agent, ModelSettings,Runner
from classificationService.classificationUtilities.tools import (extract_package_info, 
                                                                 extract_package_file_info, 
                                                            )
from src.utilities.package_state import MASState
from src.utilities.prompts import METADATA_PROMPT
from src.utilities.schemas import MetadataAgentOutput
from src.agents.classificationAgentsInterface import ClassificationAgentsInterface
from typing import Optional

class MetaDataAgent(ClassificationAgentsInterface):
     def __init__(self, 
                state: MASState= MASState(),
                model_name: Optional[str] = None,
                api_key: Optional[str] = None,
                 model_url: Optional[str] = None
                ):
          super().__init__(state=state, model_name=model_name, api_key=api_key, model_url=model_url)
          
          self.data_tools = [extract_package_info, extract_package_file_info] # type: ignore
          self.settings = ModelSettings(
               tool_choice="auto",
               parallel_tool_calls=True,
               temperature=0.2
          )
          self.logger = logging.getLogger("metadata Agent")
          self.logger.info(f"Metadata Agent initialized with model: {self.model.get_model()}")
          self.create_metadata_agent()
          self.logger.info(f"Metadata Agent created with model: {self.metadata_agent.model}")

     def create_metadata_agent(self):
          self.metadata_agent = Agent[MASState](
            name="metadata Agent",
            handoff_description="A metadata extraction agent that extracts information about a package.",
            instructions=METADATA_PROMPT,
            tools= self.data_tools,
            model=self.model.get_model(),
            model_settings=self.settings,
            output_type=MetadataAgentOutput
            )


     async def run_metadata_agent(self, state: MASState):
          """
          Runs the metadata agent to extract information about the package.
          """
          self.logger.info(f"Starting metadata agent with package location: {state.package_location}")
          metadata_agent_result = await Runner.run(self.metadata_agent,
                                                    input=f""" Get the package information of this package formated in the package in the JSON preformated file.
                                                  JSON File Location: {str(state.package_formatted_path)}""",
                                                    context=state, max_turns= 5)
          return metadata_agent_result # type: ignore



                



