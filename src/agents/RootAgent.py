import logging
from agents import Agent, ModelSettings,Runner
from src.utilities.tools import unpack_archive, unpack_folder, is_archieve
from src.utilities.package_state import MASState
from src.utilities.prompts import SUPERVISOR_PROMPT
from src.utilities.schemas import RootAgentOutput
from src.agents.classificationAgentsInterface import ClassificationAgentsInterface
from typing import List, Any, Optional

class RootAgent(ClassificationAgentsInterface):
    def __init__(self, 
                state: MASState= MASState(),
                model_name: Optional[str] = None,
                api_key: Optional[str] = None,
                 model_url: Optional[str] = None
                ):
        super().__init__(state=state, model_name=model_name, api_key=api_key, model_url=model_url) # type: ignore
        
        self.supervisor_tools:List[Any] = [unpack_archive, unpack_folder,is_archieve]
        self.settings = ModelSettings(
            tool_choice="auto",
            temperature=0.1
        )
        self.logging = logging.getLogger("root Agent")
        self.create_root_agent()
        self.logging.info(f"Root Agent initialized with model: {self.supervisor_agent.model}")
        
    def create_root_agent(self):
        self.supervisor_agent = Agent[MASState](
            name="root Agent",
            handoff_description="A supervisor agent that orchestrates the workflow of the package detection system.",
            instructions=SUPERVISOR_PROMPT,
            tools=self.supervisor_tools,
            model=self.model.get_model(),
            model_settings=self.settings,
            output_type=RootAgentOutput
        )


    def set_agent_instructions(self, instructions: str):
        """Sets the instructions for the supervisor agent."""
        self.supervisor_agent.instructions = instructions

    async def run_root_agent(self, state: MASState):
        """
        Runs the root agent to orchestrate the workflow of the package detection system.
        """
        self.logging.info(f"running root agent for package location: {state.package_location}")
        root_agent_result = await Runner.run(self.supervisor_agent,
                                             input=f""" Analyse the package at {state.package_location}.""",
                                             context=state, max_turns= 5)
        return root_agent_result # type: ignore, 
