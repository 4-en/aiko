from .base_generator import BaseGenerator
from aiko2.core import Conversation, Message, User, Role
import google.generativeai as genai
from enum import Enum
from dotenv import load_dotenv
import os

class GeminiModel(Enum):
    """
    A collection of Gemini models available for use.

    Parameters
    ----------
    Enum : str
        The model name used by the Gemini API.
    """
    
    GEMINI_1_5_FLASH = "gemini-1.5-flash"
    GEMINI_1_5_FLASH_8B = "gemini-1.5-flash-8b"
    GEMINI_1_5_PRO = "gemini-1.5-pro"
    GEMINI_1_0_PRO = "gemini-1.0-pro"
    

class GeminiRole(Enum):
    """
    A collection of OpenAI roles available for use.
    
    Parameters
    ----------
    Enum : str
        The role used by the OpenAI API.
    """
    
    USER = "user"
    MODEL = "model"

GEMINI_API_KEY_NAME = "GEMINI_API_KEY"    

class GeminiGenerator(BaseGenerator):
    """
    A generator that uses the Gemini API to generate responses.
    """
    
    def __init__(self, model: GeminiModel=GeminiModel.GEMINI_1_5_FLASH):
        """
        Initialize the Gemini generator.
        
        Parameters
        ----------
        model : Gemini, optional
            The model to use for generating responses, by default GeminiModel.GEMINI_1_5_FLASH
        role : GeminiRole, optional
            The role to use for generating responses, by default GeminiRole.ASSISTANT
        """
        self.model = model
        self.client = None

        self._last_instruction = None
        
    def _setup_client(self):
        """
        Setup the Gemini client.
        """
        
        if self.config is None:
            raise ValueError("Generator not setup. Config not set.")
        
        self.assistant = User(self.config.name, Role.ASSISTANT)
        
        # load .env
        load_dotenv()
        
        # Retrieve the Gemini API key from the .env file
        API_KEY = os.getenv(GEMINI_API_KEY_NAME)
        
        if not API_KEY:
            raise ValueError(f"Missing OpenAI API Key. Set the {GEMINI_API_KEY_NAME} environment variable.")
        
        # Initialize the gemini api key
        genai.configure(api_key=API_KEY)
        self.client = genai.GenerativeModel(self.model.value)
        self.client.generate_content
        
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
        found_instructions = []
        for message in conversation.messages:
            role = GeminiRole.USER
            if message.user.role == Role.ASSISTANT:
                role = GeminiRole.MODEL
            elif message.user.role == Role.SYSTEM:
                # Gemini does not support system messages, instead the instruction is added when instantiating the model
                found_instructions.append(message.content)
                continue
                
            messages.append({
                "role": role.value,
                "parts": [
                    {
                        "text": message.user.name + ": " + message.content
                    }
                ]
            })

        if len(found_instructions):
            instruction = "\n".join(found_instructions)
            if self._last_instruction == None or self._last_instruction != instruction:
                self._last_instruction = instruction
                self.client = genai.GenerativeModel(self.model.value, instruction=instruction)
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
        if output.lower().startswith(self.config.name.lower()+":"):
            output = output.replace(self.config.name+":", "").strip()
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
        if self.config is None:
            raise ValueError("Generator not setup. Config not set.")
        
        if self.client is None:
            self._setup_client()
            if self.client is None:
                raise ValueError("Gemini client not initialized.")
            
        try:
            # TODO: add custom safety settings
            # TODO: add generationConfig
            # TODO: system instruction in request
            response = self.client.generate_content(
                contents=self.convert_conversation_to_input(conversation),
                safety_settings=[
                    {
                        "threshold": "OFF",
                        "category": cat
                    } for cat in [
                        "HARM_CATEGORY_DEROGATORY",
                        "HARM_CATEGORY_TOXICITY",
                        "HARM_CATEGORY_VIOLENCE",
                        "HARM_CATEGORY_SEXUAL",
                        "HARM_CATEGORY_MEDICAL",
                        "HARM_CATEGORY_DANGEROUS",
                        "HARM_CATEGORY_HARASSMENT",
                        "HARM_CATEGORY_HATE_SPEECH",
                        "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                        "HARM_CATEGORY_DANGEROUS_CONTENT",
                        "HARM_CATEGORY_CIVIC_INTEGRITY"
                    ]
                ]
            )

            return self.convert_output_to_message(response.text)
        except Exception as e:
            # TODO: handle this better
            return f"Error: {str(e)}"