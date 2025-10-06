import logging
from agents import Agent, ModelSettings,Runner
from src.utilities.tools import  get_functions, get_imports, get_python_script
from src.utilities.package_state import MASState
from src.utilities.prompts import CLASSIFIER_PROMPT
from src.utilities.schemas import ClassificationAgentOutput
from src.agents.classificationAgentsInterface import ClassificationAgentsInterface
from typing import Optional

TEMPERATURE = 0.5


class ClassificationAgent(ClassificationAgentsInterface):
    def __init__(self, 
                state: MASState= MASState(),
                model_name: Optional[str] = None,
                api_key: Optional[str] = None,
                 model_url: Optional[str] = None
                ):
        super().__init__(state=state, model_name=model_name, api_key=api_key, model_url=model_url)
        
        self.classification_tools = [get_functions, get_imports, get_python_script]
        self.settings = ModelSettings(
            tool_choice="auto",
            parallel_tool_calls=True,
            temperature=TEMPERATURE
        )
        self.create_classification_agent()
        self.logger = logging.getLogger("classification Agent")
        self.logger.info(f"Classification Agent initialized with model: {self.classification_agent.model}")
        
        
    def create_classification_agent(self):
          self.classification_agent = Agent[MASState](
            name="classification Agent",
            handoff_description="A helpfull agent that classifies if a package is malicious or not.",
            instructions=CLASSIFIER_PROMPT,
            tools=self.classification_tools,
            model=self.model.get_model(),
            model_settings=self.settings,
            output_type=ClassificationAgentOutput
            )
          
    def add_guideline_context(guidelines:str)->str:
        if not guidelines:
            return ''
        general_guide = f""" ** SOME GENERAL KNOWLEDGE**
        {guidelines}
        """
        return general_guide
          
    async def run_classification_agent(self, state: MASState):
        """
        Runs the classification agent to classify the package.
        """
        exclude = {"messages", "error", "package_class", "classification_explanation"}

        # one-liner, lets Pydantic do the work
        metadata_information = state.model_dump(exclude=exclude)

        self.logger.info(f"Starting classification agent with metadata: {metadata_information['package_location']}")

        classification_agent_result = await Runner.run(self.classification_agent,
                                             input=f""" Classify the package as malicious or benign given the metadata
                                             preformatted_package_path: {state.package_formatted_path}
                                                Metadata Information: {metadata_information}
                                                
                                                """,
                                             context=state, max_turns= 15)
        return classification_agent_result # type: ignore
