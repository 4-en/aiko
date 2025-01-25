from .base_generator import BaseGenerator
from aiko2.core import Conversation, Message, User, Role
import openai
from enum import Enum
from dotenv import load_dotenv
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
    SYSTEM = "developer" # system was replaced with developer in the new API

OPENAI_API_KEY_NAME = "OPENAI_API_KEY"    

class OpenAIGenerator(BaseGenerator):
    """
    A generator that uses the OpenAI API to generate responses.
    """
    
    def __init__(self, model: OpenAIModel=OpenAIModel.GPT4O):
        """
        Initialize the OpenAI generator.
        
        Parameters
        ----------
        model : OpenAIModel, optional
            The model to use for generating responses, by default OpenAIModel.GPT4O
        role : OpenAIRole, optional
            The role to use for generating responses, by default OpenAIRole.ASSISTANT
        """
        self.model = model
        self.client = None
        
    def _setup_client(self):
        """
        Setup the OpenAI client.
        """
        
        if self.get_config() is None:
            raise ValueError("Generator not setup. Config not set.")
        
        self.assistant = User(self.get_config_value("name", "Assistant"), Role.ASSISTANT)
        
        # load .env
        load_dotenv()
        
        # Retrieve the OpenAI API key from the .env file
        API_KEY = os.getenv(OPENAI_API_KEY_NAME)
        
        if not API_KEY:
            raise ValueError(f"Missing OpenAI API Key. Set the {OPENAI_API_KEY_NAME} environment variable.")
        
        # Initialize the OpenAI client
        self.client = openai.OpenAI(
            api_key=API_KEY
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
                role = OpenAIRole.DEVELOPER
                
            messages.append({
                "role": role.value,
                "content": message.content,
                "name": message.user.name
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
        # add this since openai sometimes adds the assistant name to the output
        if output.startswith(self.assistant.name + ": "):
            output = output[len(self.assistant.name) + 2:]
        message = Message(output, self.assistant)
        return message
    
    def generate(self, conversation) -> Message:
        """
        Generate a response based on the conversation using the OpenAI API.
        
        Parameters
        ----------
        conversation : Conversation
            The conversation to generate a response for.
            
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
                model=self.model.value,
                messages=self.convert_conversation_to_input(conversation),
                temperature=self.get_config_value("temperature", 0.7),
                max_completion_tokens=self.get_config_value("max_generated_tokens", 200),
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
        
    