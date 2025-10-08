from typing import Any,Optional
from src.mampd_agents.MetaDataAgent import MetaDataAgent
from src.mampd_agents.ClassificationAgent import ClassificationAgent
from src.mampd_agents.RootAgent import RootAgent
from src.mampd_agents.mampd_agent_interface import MAMPDAgentInterface




class MAMPDAgents(MAMPDAgentInterface):
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
        """Sets the agents to the provided instances.
        Args:
            root_agent: The root agent instance.
            metadata_agent: The metadata agent instance.
            classification_agent: The classification agent instance.
        """
        if root_agent:
            self.root_agent = root_agent 
        if metadata_agent:
            self.metadata_agent = metadata_agent
        if classification_agent:        
            self.classification_agent = classification_agent
      
            
            
    def get_agents(self) -> dict[str, Any]:
        """
        Returns:
            dict[str, Any]: A dictionary of the MAMPD agents.
        """
        return {
            "root_agent": self.root_agent,
            "metadata_agent": self.metadata_agent,
            "classification_agent": self.classification_agent
        }


    def set_root_agent(self, model_name: Optional[str] = None, api_key: Optional[str] = None,
                            model_url: Optional[str] = None):
        """Sets the root agent with a new instance.
        Args:
            model_name: The model name.
            api_key: The API key. if not provided, the default API key for model provider will be used.
            model_url: The model URL. if not provided, the default model URL for model provider will be used.
        """
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
            