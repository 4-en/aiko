import openai.resources
from .base_generator import BaseGenerator
from aiko2.core import Conversation, Message, User, Role
import openai
from enum import Enum
from dotenv import load_dotenv
from pydantic import BaseModel
import os

class OpenAIModel(Enum):
    """
    A collection of OpenAI models available for use.

    Parameters
    ----------
    Enum : str
        The model name used by the OpenAI API.
    """
    
    GPT4O = "gpt-4o"
    GPT4O_MINI = "gpt-4o-mini"
    GPTO1 = "o1"
    GPTO1_MINI = "o1-mini"
    

class OpenAIRole(Enum):
    """
    A collection of OpenAI roles available for use.
    
    Parameters
    ----------
    Enum : str
        The role used by the OpenAI API.
    """
    
    USER = "user"
    ASSISTANT = "assistant"
    DEVELOPER = "developer"
    SYSTEM = "system" # system was replaced with developer in the new API

OPENAI_API_KEY_NAME = "OPENAI_API_KEY"    

class OpenAIGenerator(BaseGenerator):
    """
    A generator that uses the OpenAI API to generate responses.
    """
    
    def __init__(self, model: OpenAIModel | str =OpenAIModel.GPT4O, base_url: str=None, api_key_name: str=OPENAI_API_KEY_NAME):
        """
        Initialize the OpenAI generator.
        
        Parameters
        ----------
        model : OpenAIModel | str, optional
            The model to use for generating responses, by default OpenAIModel.GPT4O
            Can also be a string representing the model name.
        base_url : str, optional
            The base URL for the OpenAI API, by default None
            Pass different URLs for OpenAI compatible APIs.
        api_key_name : str, optional
            The name of the environment variable that contains the OpenAI API key, by default OPENAI_API_KEY
        """
        self.is_new_openai_api = model in [OpenAIModel.GPTO1, OpenAIModel.GPTO1_MINI, OpenAIModel.GPT4O_MINI, OpenAIModel.GPT4O]
        self.model_name = model.value if isinstance(model, OpenAIModel) else model
        self.client = None
        self.assistant = None
        self.base_url = base_url
        self.api_key_name = api_key_name
        
    def _setup_client(self):
        """
        Setup the OpenAI client.
        """
        
        if self.get_config() is None:
            raise ValueError("Generator not setup. Config not set.")
        
        self.assistant = User(self.get_config_value("name", "Assistant"), Role.ASSISTANT)
        
        
        # Retrieve the OpenAI API key from the .env file
        API_KEY = self.getenv(self.api_key_name)
        
        # Initialize the OpenAI client
        self.client = openai.OpenAI(
            api_key=API_KEY,
            base_url=self.base_url
        )
        
    def convert_conversation_to_input(self, conversation: Conversation) -> list[dict]:
        """
        Convert a conversation to an input string for the generator.
        
        Parameters
        ----------
        conversation : Conversation
            The conversation to convert.
        
        Returns
        -------
        list[dict]
            The input for the generator.
        """
        messages = []
        for message in conversation.messages:
            role = OpenAIRole.USER
            if message.user.role == Role.ASSISTANT:
                role = OpenAIRole.ASSISTANT
            elif message.user.role == Role.SYSTEM:
                role = OpenAIRole.DEVELOPER if self.is_new_openai_api else OpenAIRole.SYSTEM
                
            messages.append({
                "role": role.value,
                "content": f"<{message.user.name}> {message.content}" if message.user.role == Role.USER or message.user.role == Role.ASSISTANT else message.content
            })
        return messages
    
    def convert_output_to_message(self, output:str) -> Message:
        """
        Convert the output from the OpenAI API to a Message.
        
        Parameters
        ----------
        output : str
            The output from the OpenAI API.
        
        Returns
        -------
        Message
            The message generated.
        """
        # remove the assistant name from the output in case it was added by the model
        if output.lower().startswith(self.assistant.name.lower()+":"):
            length = len(self.assistant.name) + 1
            output = output[length:].strip()
        
        if output.lower().startswith(f"<{self.assistant.name.lower()}>"):
            length = len(self.assistant.name) + 2
            output = output[length:].strip()
        
        message = Message(output, self.assistant)
        return message
    
    def generate(self, conversation, context=None, response_format: BaseModel = None, **kwargs) -> Message:
        """
        Generate a response based on the conversation using the OpenAI API.
        
        Parameters
        ----------
        conversation : Conversation
            The conversation to generate a response for.
        context : str, optional
            The context of the conversation. Can include retrieved information,
            inner monologue, etc.
        response_format : BaseModel, optional
            The format of the model output.
            If None, the output will be a string.
            Otherwise, try to generate json output based on the model.
        kwargs : dict
            Additional keyword arguments for openai.ChatCompletion.create.
            Overwrites default and config values.
            
        Returns
        -------
        Message
            The response generated.
        """
        if self.get_config() is None:
            raise ValueError("Generator not setup. Config not set.")
        
        if self.client is None:
            self._setup_client()
            if self.client is None:
                raise ValueError("OpenAI client not initialized.")
            
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=self.convert_conversation_to_input(conversation),
                temperature=self.get_config_value("temperature", 1.0),
                max_completion_tokens=self.get_config_value("max_generated_tokens", 200),
                response_format=openai.NOT_GIVEN if response_format is None else response_format
            )
            return self.convert_output_to_message(response.choices[0].message.content)
        except Exception as e:
            # TODO: handle this better
            raise e
        
                
class GPT4OGenerator(OpenAIGenerator):
    """
    A generator that uses the GPT-4o model from OpenAI to generate responses.
    """
    
    def __init__(self):
        super().__init__(model=OpenAIModel.GPT4O)

class GPT4OMiniGenerator(OpenAIGenerator):
    """
    A generator that uses the GPT-4o-mini model from OpenAI to generate responses.
    """
    
    def __init__(self):
        super().__init__(model=OpenAIModel.GPT4O_MINI)

class GPTO1Generator(OpenAIGenerator):
    """
    A generator that uses the GPT-o1 model from OpenAI to generate responses.
    """
    
    def __init__(self):
        super().__init__(model=OpenAIModel.GPTO1)
        
    