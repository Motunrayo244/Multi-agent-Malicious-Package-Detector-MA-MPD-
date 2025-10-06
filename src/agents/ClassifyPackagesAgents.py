from typing import Any,Optional
from src.agents.MetaDataAgent import MetaDataAgent
from src.agents.ClassificationAgent import ClassificationAgent
from src.agents.RootAgent import RootAgent
from src.agents.classificationAgentsInterface import ClassificationAgentsInterface




class ClassifyPackagesAgents(ClassificationAgentsInterface):
    def __init__(self, model_name: Optional[str] = None, api_key: Optional[str] = None,
                 model_url: Optional[str] = None):
        """Initializes the moderator agents with the specified model."""
        super().__init__(model_name=model_name, api_key=api_key, model_url=model_url) # type: ignore

        self.model_name = model_name # type: ignore
        self.api_key = api_key # type: ignore
        self.model_url = model_url # type: ignore

        self.set_root_agent()
        self.set_metadata_agent()     
        self.set_classification_agent()
        
        
    def set_classify_packages_agents(self, root_agent: Optional[RootAgent] = None,
                                     metadata_agent: Optional[ClassificationAgent] = None,
                                     classification_agent: Optional[ClassificationAgent] = None):
        """Sets the agents to the provided instances."""
        if root_agent:
            self.root_agent = root_agent 
        if metadata_agent:
            self.metadata_agent = metadata_agent
        if classification_agent:        
            self.classification_agent = classification_agent
      
            
            
    def get_agents(self) -> dict[str, Any]:
        """Returns a dictionary of the classification agents."""
        return {
            "root_agent": self.root_agent,
            "metadata_agent": self.metadata_agent,
            "classification_agent": self.classification_agent
        }


    def set_root_agent(self, model_name: Optional[str] = None, api_key: Optional[str] = None,
                            model_url: Optional[str] = None):
        """Sets the root agent with a new instance."""
        self.root_agent = RootAgent(
            model_name=model_name if model_name is not None else self.model_name,  # type: ignore
            api_key=api_key if api_key is not None else self.api_key,
            model_url=model_url if model_url is not None else self.model_url,
        )
        
    def set_metadata_agent(self, model_name: Optional[str] = None, api_key: Optional[str] = None,
                            model_url: Optional[str] = None):
        """Sets the metadata agent with a new instance."""
        self.metadata_agent = MetaDataAgent(
            model_name=model_name if model_name is not None else self.model_name,  # type: ignore
            api_key=api_key if api_key is not None else self.api_key,
            model_url=model_url if model_url is not None else self.model_url,
        )
        
    def set_classification_agent(self, model_name: Optional[str] = None, api_key: Optional[str] = None,
                            model_url: Optional[str] = None):
        """Sets the classification agent with a new instance."""
        self.classification_agent = ClassificationAgent(
            model_name=model_name if model_name is not None else self.model_name,  # type: ignore
            api_key=api_key if api_key is not None else self.api_key,
            model_url=model_url if model_url is not None else self.model_url,
        )
            