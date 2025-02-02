from aiko2.core import Conversation, Message, User, Role
from dataclasses import dataclass, field
import typing_extensions as typing
from aiko2.generator.base_generator import BaseGenerator
from aiko2.retriever import Query, QueryType
import json
from aiko2.utils import ComponentMixin, Memory

class EvaluatorResponse(typing.TypedDict):
    """
    A dictionary representing the response from an evaluator.
    """
    queries: list[str]
    context: list[str]


@dataclass
class Evaluation:
    """
    A class to represent the evaluation of a conversation.
    This can include queries for information retrieval or the results
    of function calls.
    """
    evaluation_input: Conversation # The conversation to evaluate
    queries: list[Query] = field(default_factory=list) # Queries for information retrieval, may be empty
    context: list[str] = field(default_factory=list) # additional context for the conversation, may be empty
    memories: list[Memory] = field(default_factory=list) # Memories to store, may be empty
    reply_expectation: float = 0.0 # The 'likelihood' of replying to the message, 0.0 to 1.0, with 1.0 being most likely. Somewhat arbitrary, so might want to ignore this.
    

class BaseEvaluator(ComponentMixin):
    """
    Base class for an evaluator.
    An evaluator decides whether to retrieve information or not.
    It generates one or more queries to retrieve information if needed.
    """
    
    def __init__(self, generator:BaseGenerator):
        self.generator = generator

    def _set_pipeline(self, pipeline):
        super()._set_pipeline(pipeline)
        if self.generator:
            self.generator._set_pipeline(pipeline)
    

        
    def _create_evaluation(self, conversation:Conversation, json_input:dict) -> Evaluation:
        """
        Convert a JSON object to an evaluation.
        Keys in the JSON object are:
        - queries: list of queries to retrieve information (list[str])
        - context: list of context for the conversation (list[str])

        Parameters
        ----------
        conversation : Conversation
            The conversation that was evaluated.
        json : dict
            The JSON object to convert.

        Returns
        -------
        Evaluation
            The evaluation converted.
        """
        
        if json_input is None or type(json_input) is not dict:
            # handle invalid JSON generated by llm
            json_input = {}
        
        queries = json_input.get("queries", [])
        memories = json_input.get("memories", [])
        reply_expectation = json_input.get("reply_expectation", 0.0)
        
        queries_response = []
        for query in queries:
            query_str = query.get("query", "")
            topic = query.get("topic", "")
            query_type = query.get("type", "GENERAL")
            query_type = QueryType.from_string(query_type)
            
            if query_str == "" or topic == "":
                continue
            
            queries_response.append(Query(query_str, topic, query_type))
            
        memories_response = []
        for memory in memories:
            memory_str = memory.get("memory", "")
            person = memory.get("person", "")
            topic = memory.get("topic", "")
            
            if memory_str == "" or person == "" or topic == "":
                continue
            
            memories_response.append(Memory(memory_str, person, topic))
            
        context_response = [] # TODO: add context to evaluation
            
        evaluation = Evaluation(
            conversation,
            queries_response,
            context_response,
            memories_response,
            reply_expectation
        )
        
        return evaluation
        
    def get_instructions(self) -> str:
        """
        Get the instructions for the evaluator.

        Returns
        -------
        str
            The instructions for the evaluator.
        """
        name = self.get_config_value("name", "Assistant")
        instructions = f"""You are an evaluator for {name}.
        Your task is to decide whether to reply to a chat message or not, based on the conversation context, by generating a probability between 0.0 and 1.0 of replying to the message.
        This number represents how expected it is that the message should be replied to. For example, if {name} is in a conversation with the speaker or the speaker is asking a question, the probability should be higher.
        If the message is not directed at {name}, the probability should be lower.
        
        Then, decide whether it is necessary to retrieve external information to reply to the message, by generating up to 3 queries to retrieve information.
        When asking about a specific person, including {name}, use the third person and their name. The questions can be about general information or about more personal information.
        Even if the user didn't directly ask a question, you can still generate queries to retrieve information if it could help in replying to the message.
        You should generate questions about both {name} and any other people or topics relevant to the conversation and to the next reply.
        For example, if person A asks person B if they like pizza, you could generate this query: "Does person B like pizza?" and "What food does person B like?".
        
        Your other task is to decide if any content of the message should be memorized. Content that should be memorized is anything personal, either about yourself or another person.
        This includes statements, plans, interests, appearances and more. You can see it as storing information about something.
        You should not memorize any information that general knowledge, such as the capital of a country or the date of a holiday, unless specifically asked to do so.
        The memories should also be written in the third person and include the name of the person the memory is about.
        For example, a memory about {name} could look like this: {name} likes cookie dough ice cream.
        """
        
        return instructions + "\n\n" + self._get_format_instruction()
    
    def _get_format_instruction(self) -> str:
        """
        Get the format for the llm output.
        """
        
        format_instruction = """Use this JSON schema:
        QueryType = 'GENERAL' | 'PERSONAL' | 'NEWS' | 'RESEARCH' | 'OTHER'
        Memory = {'memory': str, 'person': str, 'topic': str}
        Query = {'query': str, 'topic': str, 'type': QueryType}
        Evaluation = {'reply_expectation': float, 'queries': list[Query], 'memories': list[Memory]}
        Return: Evaluation"""
        
        return format_instruction

    def evaluate(self, conversation:Conversation) -> Evaluation:
        """
        Evaluate the conversation and return one or more queries to retrieve information.

        Parameters
        ----------
        conversation : Conversation
            The conversation to evaluate.

        Returns
        -------
        Evaluation
            The evaluation of the conversation.
        """
        
        if self.generator == None:
            raise ValueError("Generator is not set.")
        
        if self.get_config() == None:
            raise ValueError("Evaluator not setup. Config not set.")
        
        input_messages_length = self.get_config_value("max_evaluation_input_messages", 1)
        if input_messages_length == None or input_messages_length < 1:
            input_messages_length = 1
            
        input_messages = conversation.messages[-input_messages_length:]
        input_messages = [message for message in input_messages if message.user.role != Role.SYSTEM]
        
        system_message = Message(self.get_instructions(), User("System", Role.SYSTEM))
        input_messages.insert(0, system_message)
        
        input_conversation = Conversation(input_messages)
        
        evaluation = Evaluation(input_conversation)
        
        output_message = self.generator.generate(input_conversation)
        if output_message == None:
            return evaluation
        
        output_string = output_message.content
        
        # try to unscuff the json
        if not output_string.startswith("{") or not output_string.startswith("["):
            # sometimes the output is not valid JSON, so we need to fix it
            # try to find the first '{' or '[' and remove everything before it
            first_square_bracket = output_string.find("[")
            first_curly_bracket = output_string.find("{")
            if first_square_bracket > -1 and first_square_bracket < first_curly_bracket:
                # find ending bracket
                ending_bracket = output_string.rfind("]")
                if ending_bracket > -1:
                    output_string = output_string[first_square_bracket:ending_bracket+1]
            elif first_curly_bracket > -1:
                # find ending bracket
                ending_bracket = output_string.rfind("}")
                if ending_bracket > -1:
                    output_string = output_string[first_curly_bracket:ending_bracket+1]   
            


        
        try:
            json_output = json.loads(output_string)
            evaluation = self._create_evaluation(input_conversation, json_output)
            
        except json.JSONDecodeError:
            print("Error decoding JSON output from generator.")
            print(output_string)
            return evaluation
        except Exception as e:
            print("Error processing output from generator.")
            print(e)
            return evaluation
        
        return evaluation
        
        