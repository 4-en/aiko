from .base_pipeline import BasePipeline
from aiko2.pipeline.pipeline_components import MemoryHandler
from aiko2.core import Conversation, Message, User, Role, Memory, RetrievalResults, QueryType
from aiko2.config import Config

from aiko2.evaluator import BaseEvaluator
from aiko2.generator import BaseGenerator
from aiko2.refiner import BaseRefiner
from aiko2.retriever import BaseRetriever
from aiko2.utils import get_storage_location
import os
from dotenv import load_dotenv

class Pipeline(BasePipeline):
    """
    Pipeline class to represent a pipeline.
    This class controls the retrieval and generation process.
    This is a simple, linear pipeline that can use components passed to it to generate responses.
    It can be used to generate responses based on a conversation, and can be extended with additional components.
    

    The pipeline consists of an evaluator, a retriever, a generator, and a refiner.
    The retriever adds context to the conversation, which is then passed
    to the generator to generate a response. The refiner can be used to
    refine the response generated by the generator.
    
    At minimum, the pipeline requires a generator to generate responses, which would simply pass the conversation to the generator.

    Pipeline:
        Input: Conversation
            ↓
        Evaluator  (Decides whether and what to retrieve)
            ↓
        Retriever  (Fetches relevant information, if needed)
            ↓
        Generator  (LLM generates response)
            ↓
        Refiner    (Post-processing, formatting, filtering)
            ↓
        Output: Message | None
    
    """

    def __init__(
            self, 
            generator: BaseGenerator,
            evaluator: BaseEvaluator=None, 
            retriever: BaseRetriever=None,
            refiner: BaseRefiner=None,
            memory_handler: MemoryHandler=None,
            root_dir: str=None,
            config: Config=None
        ) -> None:   
        """
        Initialize the pipeline.

        This simple pipeline consists of a retriever, generator, and refiner.
        The retriever adds context to the conversation, which is then passed
        to the generator to generate a response. The refiner can be used to
        refine the response generated by the generator.

        Pipeline:
            Input: Conversation
                ↓
            Evaluator  (Decides whether to retrieve or not)
                ↓
            Retriever  (Fetches relevant information, if needed)
                ↓
            Generator  (LLM generates response)
                ↓
            Refiner    (Post-processing, formatting, filtering)
                ↓
            Output: Message | None

        Parameters
        ----------
        generator : Generator
            The generator to use to generate responses based on the conversation
            and any additional information retrieved by the retriever.
        evaluator : Evaluator | None, optional
            The evaluator to use to evaluate the conversation.
            It decides whether to retrieve information or not, and
            if so, it generates one or more queries to retrieve information.
            If None, no evaluator will be used.
        retriever : Retriever
            The retriever to use to retrieve information based on the queries
            generated by the evaluator.
            If None, no retriever will be used.
        refiner : Refiner | None, optional
            The refiner to use to refine responses generated by the generator.
            If None, no refiner will be used.
        root_dir : str, optional
            The root directory to use for the pipeline.
            If None, the default root directory will be used.
            - Windows: %APPDATA%/aiko
            - Linux: ~/share/aiko
            - macOS: ~/Library/Application Support/aiko
        config : Config, optional
            The configuration to use for the pipeline.
            If None, tries to load the configuration from the root directory.
        """
        self.generator = generator
        self.evaluator: BaseEvaluator = evaluator
        self.retriever: BaseRetriever = retriever
        self.refiner: BaseRefiner = refiner
        self.memory_handler: MemoryHandler = memory_handler
        self.root_dir = root_dir or get_storage_location("aiko", create=True)
        self.config: Config = config or Config().load(self.root_dir+"/config.txt")
        
        print(f"Root dir: {self.get_root_dir()}")
        
        # load environment variables from .env file in root directory
        dotenv_path = self.get_root_dir()+"/.env"
        if not os.path.exists(dotenv_path):
            print(f"Creating .env file in {self.get_root_dir()}")
            with open(dotenv_path, "w") as f:
                f.write("# Add environment variables here")
        else:
            load_dotenv(self.get_root_dir()+"/.env")
        
        # Setup the generator
        self.generator._set_pipeline(self)

        if self.evaluator:
            self.evaluator._set_pipeline(self)
        
        if self.memory_handler:
            self.memory_handler._set_pipeline(self)
            
        self._system_message = self._generate_system_message()

    def save(self) -> None:
        """
        Save the pipeline.
        This method can be used to save pipeline components to disk.
        """
        
        if self.memory_handler:
            self.memory_handler.save()
        
        self.config.save(self.root_dir+"/config.txt")

    def add_memories(self, memories: list[Memory], domain: str=None) -> None:
        """
        Add memories to the memory handler.

        Parameters
        ----------
        memories : list[Memory]
            The memories to add.
        domain : str, optional
            The domain to add the memories to.
            If None, the memories will be added to the default domain.
        """
        if self.memory_handler:
            for memory in memories:
                memory_str = memory.memory
                print(f"Adding memory: {memory_str}")
                print(f"Person: {memory.person}, Relevance: {memory.time_relevance}, Time: {memory.memory_age}, Truthfulness: {memory.truthfulness}")
                self.memory_handler.add_memory(memory, domain)

        
    def get_root_dir(self) -> str:
        """
        Get the root directory of the pipeline.

        Returns
        -------
        str
            The root directory of the pipeline.
            (Without trailing slash)
        """
        return os.path.abspath(self.root_dir)
    
    def get_data_dir(self) -> str:
        """
        Get the data directory of the pipeline.

        Returns
        -------
        str
            The data directory of the pipeline.
            (Without trailing slash)
        """
        return os.path.abspath(self.root_dir+"/data")
    
    def get_config(self) -> Config:
        """
        Get the configuration of the pipeline.

        Returns
        -------
        Config
            The configuration of the pipeline.
        """
        return self.config
    
    def get_config_dir(self) -> str:
        """
        Get the directory of configuration files.
        The main configuration file is usually stored in the root directory.

        Returns
        -------
        str
            The directory of the configuration file.
        """
        return os.path.abspath(self.root_dir+"/config")
        
    def _generate_system_message(self) -> Message:
        """
        Generates a system message as instruction for the model.
        This message is inserted as the first message of a conversation.

        Returns
        -------
        Message
            The system message.
        """
        
        instruction = self.config.instructions
        if not instruction:
            instruction = "You are a helpful AI assistant. Please provide useful information to the user."
        
        return Message(instruction, User("System", Role.SYSTEM))
        

    def generate(self, conversation: Conversation) -> Message | None:
        """
        Generate a response based on the conversation.

        Parameters
        ----------
        conversation : Conversation
            The conversation to generate a response from.

        Returns
        -------
        Message | None
            The generated response.
            If no response was generated, return None.
            This can happen if the pipeline is setup to decide 
            whether to generate a response or not, for example if
            the message wasn't directed at the AI.
        """
        
        # in case the conversation was not a request from an api and is the same object used to
        # store the actual conversation history, we need to copy it to avoid modifying the original
        # with things like instructions, system messages, etc.
        conversation = conversation.copy()
        conversation = self._limit_input_length(conversation)
        
        # Evaluate the conversation
        queries = []
        evaluator_context = []
        memories = []
        if self.evaluator:
            try:
                evaluation = self.evaluator.evaluate(conversation)
                queries = evaluation.queries
                evaluator_context = evaluation.context
                memories = evaluation.memories
                reply_expectation = evaluation.reply_expectation
                if reply_expectation <= 0.3:
                    # TODO: NOTE: This is kinda arbitrary, maybe a better way to handle this
                    # would be to have a bunch of yes/no questions about the conversation
                    # state and calculate a score based on that.
                    
                    # also take into consideration meta data of conversation, like users, timestamps, private/group chat, etc.
                    return None
            except Exception as e:
                print(f"Failed to evaluate conversation: {e}")
                # continue without queries

            
        
        # Retrieve information
        if len(queries) > 0 and self.retriever:
            # queries = [query for query in queries if query and query.query_type != "PERSONAL"]
            # TODO: make better use of meta data
            # print(f"Retrieving information for queries: {queries}")
            retrieved_info = self.retriever.retrieve(conversation, queries)
            retrieved_info.purge(min_score=0.5, max_results=3)
            if len(retrieved_info) > 0:
                # self._append_retrieval_results(conversation, retrieved_info)
                summary = self.evaluator.summarize_retrieval(retrieved_info, evaluator_context[0] if len(evaluator_context) > 0 else None)
                print(f"Retrieved information: {summary}")
                self._append_summary(conversation, summary)
            else:
                print("No information retrieved")

                
        # add memories after retrieval
        if len(memories) > 0:
            self.add_memories(memories)
        
        # insert the system message as the first message
        conversation.messages.insert(0, self._system_message)
        
        
        # Generate response
        # print(f"Request: {conversation}")
        response = self.generator.generate(conversation)
        
        # Refine response
        if self.refiner:
            response = self.refiner.refine(conversation, response)
        
        return response
    
    def _append_summary(self, conversation: Conversation, summary: str):
        """
        Append a summary of the retrieved information to the conversation.

        Parameters
        ----------
        conversation : Conversation
            The conversation to append the summary to.
        summary : str
            The summary of the retrieved information to append to the conversation.
        """
        last_message = conversation.messages[-1]
        conversation.messages = conversation.messages[:-1]

        summary = f"{summary}"
        message = Message(summary, User(self.config.name, Role.ASSISTANT))
        conversation.messages.append(message)
        conversation.messages.append(last_message)

    
    def _append_retrieval_results(self, conversation: Conversation, retrieved_info: RetrievalResults):
        """
        Append the retrieved information to the conversation.

        Parameters
        ----------
        conversation : Conversation
            The conversation to append the retrieved information to.
        retrieved_info : RetrievalResults
            The retrieved information to append to the conversation.
        """
        # creates new messages in the conversation, for example:
        # <INNER MONOLOGUE> The capital of France is Paris. <-- retrieved information
        # <USER> What is the capital of France?
        # <ASSISTANT> (Answer based on retrieved information)
        # <USER> Thanks!
        # We insert the retrieved information before the last message in the conversation,
        # to make it easier for the model to attend to the actual question asked by the user.
        # TODO: Consider adding user question before AND after the retrieved information? This might help the model to extract the correct context.

        last_message = conversation.messages[-1]
        conversation.messages = conversation.messages[:-1]
        
        query_results = retrieved_info.top_k(3)

        for result in reversed(query_results): # reversed so best results are last
            query_result = result.result
            if query_result and len(query_result) > 10:
                print(f"Appending query result: {query_result[:100]}... Score: {result.score}")
                message = Message(query_result, User("INNER_MONOLOGUE", Role.USER))
                conversation.messages.append(message)

        conversation.messages.append(last_message)
    
    def _limit_input_length(self, conversation: Conversation) -> Conversation:
        """
        Limit the input length of the conversation.
        To limit api/computing costs, we limit the input length of the conversation.
        To take advantage of caching (specifically for the OpenAI API), we will try to
        keep the beginning of the sequence as consistent as possible.

        For example, if the limit is 4096 tokens, we will not cut off at the exact token, but rather
        cut off a fixed number of tokens from the start of the conversation once the limit is reached.
        This allows us to keep the beginning of the conversation consistent between multiple requests,
        even if the end of the conversation changes every time.

        Another option would be to use message ids to keep track of the last message that was included
        and cache last conversations sent to the API.
        
        Example:
        Limit: 10 tokens
        - Seq 1: "A B C D E F G" (Fine, 7 tokens)
        - Seq 2: "A B C D E F G H I J (Fine, 10 tokens)
        - Seq 3: "A B C D E F G H I J K L" (Limit reached, cut off 5 tokens (until <= 10 tokens)) -> "F G H I J K L"
        - Seq 4: "A B C D E F G H I J K L M N" (Limit reached, cut off 5 tokens (until <= 10 tokens)) -> "F G H I J K L M N"
        The start of sequence 3 and 4 is consistent, while the end changes. The "F G H I J K L" can be cached
        and reduce cost when sending the next request.

        Note: This only works if the request contains the full conversation history withouth manually
        shortening it. If the conversation is manually shortened, this method will not work as intended.

        Parameters
        ----------
        conversation : Conversation
            The conversation to limit the input length of.

        Returns
        -------
        Conversation
            The conversation with the input length limited.
        """

        total_tokens = conversation.estimate_tokens()
        max_tokens = self.config.max_input_length
        cut_off_window = self.config.cut_off_window

        if total_tokens <= max_tokens or max_tokens <= 0:
            return conversation
        

        # some checks to avoid annoying debugging
        if max_tokens < cut_off_window:
            raise ValueError("cut_off_window must be less than or equal to max_input_length")
        
        if max_tokens < 128:
            raise ValueError("max_input_length must be at least 128 tokens")
        
        target_tokens = max_tokens - cut_off_window

        # cut off messages from beginning until total tokens <= target tokens
        while total_tokens > target_tokens:
            # remove first message
            message = conversation.messages.pop(0)
            total_tokens -= message.estimate_tokens()

        return conversation