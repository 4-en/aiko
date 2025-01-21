from .base_pipeline import BasePipeline
from aiko2.core import Conversation, Message, User, Role
from aiko2.config import Config

from aiko2.evaluator import BaseEvaluator
from aiko2.generator import BaseGenerator
from aiko2.refiner import BaseRefiner
from aiko2.retriever import BaseRetriever, RetrievalResults

class Pipeline(BasePipeline):
    """
    Pipeline class to represent a pipeline.
    This class controls the retrieval and generation process.
    At minimum, the pipeline should be able to generate a response
    using the generate method.
    """

    def __init__(
            self, 
            generator: BaseGenerator,
            evaluator: BaseEvaluator=None, 
            retriever: BaseRetriever=None,
            refiner: BaseRefiner=None,
            config: Config=None):
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
        config : Config | None, optional
            The configuration to use for the pipeline.
            If None, the default configuration will be used.
        """
        self.generator = generator
        self.evaluator: BaseEvaluator = evaluator
        self.retriever: BaseRetriever = retriever
        self.refiner: BaseRefiner = refiner
        self.config: Config = config or Config()
        
        # Setup the generator
        self.generator._setup(self.config)
        self._system_message = self._generate_system_message()
        
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
        conversation = conversation.copy()
        conversation = self._limit_input_length(conversation)
        
        # Evaluate the conversation
        queries = []
        if self.evaluator and self.retriever: # only evaluate if retriever is also present, otherwise pointless
            queries = self.evaluator.generate_queries(conversation)
        
        # Retrieve information
        if len(queries) > 0 and self.retriever:
            retrieved_info = self.retriever.retrieve(queries)
            if len(retrieved_info) > 0:
                self._append_retrieval_results(conversation, retrieved_info)
        
        # insert the system message as the first message
        conversation.messages.insert(0, self._system_message)
        
        
        # Generate response
        response = self.generator.generate(conversation)
        
        # Refine response
        if self.refiner:
            response = self.refiner.refine(conversation, response)
        
        return response
    
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
        # <Expert> The capital of France is Paris.

        # TODO: Implement this method

        return conversation
    
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