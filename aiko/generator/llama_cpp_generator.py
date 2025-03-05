from .base_generator import BaseGenerator
from aiko.core import Conversation, Message, User, Role
from llama_cpp import Llama, ChatCompletionRequestResponseFormat
from enum import Enum

class LlamaCppRole(Enum):
    """
    A collection of roles available for use with the Llama C++ framework.
    
    Parameters
    ----------
    Enum : str
        The role used by the OpenAI API.
    """
    
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class LlamaCppGenerator(BaseGenerator):
    """Generator for local models that use the Llama C++ framework."""
    
    def __init__(self, model_path:str, hf_repo:str=None, model_params:dict={}, generator_params:dict={}):
        """
        Initialize the Llama C++ generator.

        Parameters
        ----------
        model_path : str
            The path to the model.
        hf_repo : str, optional
            The Hugging Face repository name, by default None
            If none, the model is assumed to be a local model.
        """
        self.model_path = model_path
        self.hf_repo = hf_repo
        self.assistant = None
        self.model_params = model_params
        self.generator_params = generator_params
        self.model: Llama = None

    def _get_model_params(self) -> dict:
        """
        Get the model parameters.
        """

        n_ctx=100000
        flash_attn=True
        n_gpu_layers=-1
        verbose=False

        base_params = {
            "n_ctx": n_ctx,
            "flash_attn": flash_attn,
            "n_gpu_layers": n_gpu_layers,
            "verbose": verbose
        }

        base_params.update(self.model_params)
        return base_params
    
    def _get_generator_params(self) -> dict:
        """
        Get the generator parameters.
        """
        return self.generator_params

    def _setup_generator(self):
        """
        Setup the model for generating responses.
        """
        
        if self.get_config() is None:
            raise ValueError("Generator not setup. Config not set.")
        
        self.assistant = User(self.get_config_value("name", "Assistant"), Role.ASSISTANT)

        self.model = None

        print("Setting up Llama C++ generator...")
        if self.hf_repo is None:
            self.model = Llama(self.model_path, **self._get_model_params())
        else:
            self.model = Llama.from_pretrained(self.hf_repo, self.model_path, **self._get_model_params())


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
            role = LlamaCppRole.USER
            if message.user.role == Role.ASSISTANT:
                role = LlamaCppRole.ASSISTANT
            elif message.user.role == Role.SYSTEM:
                role = LlamaCppRole.SYSTEM
                
            messages.append({
                "role": role.value,
                "content": f"<{message.user.name}> {message.message_text}" if message.user.role == Role.USER or message.user.role == Role.ASSISTANT else message.message_text
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
        # if there is a </think> tag, seperate it
        cot = ""
        message = ""
        if "</think>" in output:
            cot = output.split("</think>", 1)
            if len(cot) == 2:
                output = cot[1]
                cot = cot[0].replace("<think>", "")
            else:
                output = cot[0]
                cot = ""

        if output.startswith(self.assistant.name + ": "):
            output = output[len(self.assistant.name) + 2:]

        if output.startswith("<" + self.assistant.name + ">"):
            output = output.replace("<" + self.assistant.name + ">", "").strip()

        message = Message(output, self.assistant)
        return message
        
    
    def generate(self, conversation: Conversation, json_format:bool=False) -> Message:
        """Generate a response based on the conversation.

        Parameters
        ----------
        conversation : Conversation
            The conversation to generate a response for.

        Returns
        -------
        Message
            The generated response.
        """
        if self.model is None:
            self._setup_generator()
        t = "text" if not json_format else "json"
        response_format = ChatCompletionRequestResponseFormat(type=t)        
        try:
            input = self.convert_conversation_to_input(conversation)
            output = self.model.create_chat_completion(
                messages=input,
                response_format=response_format,
                **self._get_generator_params(),
                temperature=self.get_config_value("temperature", 1.0),
                max_tokens=self.get_config_value("max_generated_tokens", 400)
            )
            
            return self.convert_output_to_message(output["choices"][0]["message"]["content"])
        except Exception as e:
            # TODO: handle exceptions
            raise e
        

        
    