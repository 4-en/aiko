from aiko.core import Conversation, Message, User, Role, Memory, TimeRelevance, RetrieverType
from dataclasses import dataclass, field
import typing_extensions as typing
from aiko.generator.base_generator import BaseGenerator
from aiko.core import Query, QueryType, RetrievalResults
import json
from aiko.pipeline.pipeline_components import ComponentMixin
from aiko.utils import parse_timestamp
from pydantic import BaseModel
from enum import Enum

# TODO: change person to list of people
"""Use this JSON schema:
        QueryType = 'PERSONAL' | 'NEWS' | 'RESEARCH' | 'OTHER'
        TimeRelevance = 'NOW' | 'WEEK' | 'MONTH' | 'YEAR' | 'ALWAYS'
        MemoryAge = str # str in format #d for age in days, otherwise DD-MM-YYYY or DD-MM or YYYY or DD or name of the weekday or month
        Memory = {'memory': str, 'person': str, 'topic': str, 'time_relevance': TimeRelevance, 'memory_age': MemoryAge, 'truthfulness': float} # the memory string should be in the third person and only contain the information, not the context (Yes: "Person A likes pizza.", No: "Person B said that A likes pizza.")
        Query = {'query': str, 'topic': str, 'type': QueryType, 'time_relevance': TimeRelevance}
        Evaluation = {'thoughts': str, 'reply_expectation': float, 'queries': list[Query], 'memories': list[Memory]}
Return: Evaluation"""
        
class EvaluationResponseQueryType(Enum):
    PERSONAL = "PERSONAL"
    NEWS = "NEWS"
    RESEARCH = "RESEARCH"
    OTHER = "OTHER"
    
class EvaluationResponseTimeRelevance(Enum):
    NOW = "NOW"
    WEEK = "WEEK"
    MONTH = "MONTH"
    YEAR = "YEAR"
    ALWAYS = "ALWAYS"


class EvaluationResponseQuery(BaseModel):
    query: str
    topic: str
    type: EvaluationResponseQueryType
    time_relevance: EvaluationResponseTimeRelevance
    
class EvaluationResponseMemory(BaseModel):
    memory: str
    person: str
    topic: str
    time_relevance: EvaluationResponseTimeRelevance
    memory_age: str
    truthfulness: float
    
class EvaluationResponse(BaseModel):
    thoughts: str
    reply_expectation: float
    queries: list[EvaluationResponseQuery]
    memories: list[EvaluationResponseMemory]

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
    
    def __init__(self, generator:BaseGenerator=None):
        self.generator = generator

    def _set_pipeline(self, pipeline):
        super()._set_pipeline(pipeline)

        had_generator = self.generator != None
        if not had_generator:
            self.generator = self.get_generator()

        if had_generator and self.generator != None:
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
        thoughts = json_input.get("thoughts", "")
        query_context = []
        if thoughts != "": # add thoughts to query context
            query_context.append(thoughts)
            print(f"Thinking: {thoughts}")
        
        queries_response = []
        for query in queries:
            query_str = query.get("query", "")
            topic = query.get("topic", "")
            query_type = query.get("type", "GENERAL")
            time_relevance = query.get("time_relevance", "ALWAYS")
            query_type = QueryType.from_string(query_type)
            time_relevance = TimeRelevance.from_string(time_relevance)
            
            if query_str == "" or topic == "":
                continue
            
            queries_response.append(Query(query_str, topic, query_type, time_relevance=time_relevance))
            
        memories_response = []
        for memory in memories:
            memory_str = memory.get("memory", "")
            person = memory.get("person", "")
            topic = memory.get("topic", "")
            
            time_relevance = memory.get("time_relevance", "ALWAYS")
            time_relevance = TimeRelevance.from_string(time_relevance)
            
            memory_age = memory.get("memory_age", 0)
            memory_age = parse_timestamp(memory_age)
            
            truthfulness = memory.get("truthfulness", 1.0)
            
            if memory_str == "" or person == "" or topic == "":
                continue
            
            memories_response.append(Memory(memory_str, [person], topic, time_relevance, truthfulness, memory_age))
            
            
        evaluation = Evaluation(
            conversation,
            queries_response,
            query_context,
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
        # instructions = f"""You are {name}'s inner monologue.
        # You are given a piece of a conversation and have to evaluate it in order to help {name} form a reply, similar to an inner monologue. First, think out loud about the conversation and its state. Decide what kind of reply is expected and what information is needed to form a reply.
        # If you already know what is needed or expected, write it down. Otherwise, think about what you would need to know to reply to the message. This could be information about the speaker, the topic, or anything else relevant to the conversation.
        
        # Your task then is to decide whether to reply to a chat message or not, based on the conversation context, by generating a probability between 0.0 and 1.0 of replying to the message.
        # This number represents how expected it is that the message should be replied to. For example, if {name} is in a conversation with the speaker or the speaker is asking a question, the probability should be higher.
        # If the message is not directed at {name}, the probability should be lower.
        
        # Then, decide whether it is necessary to retrieve external information to reply to the message, by generating up to 3 queries to retrieve information.
        # When asking about a specific person, including {name}, use the third person and their name. The questions can be about general information or about more personal information. For example, if the user asks about the opinion of {name} on digital art, you could first generate a query about digital art in general and then a query about {name}'s opinion on digital art.
        # Even if the user didn't directly ask a question, you can still generate queries to retrieve information if it could help in replying to the message.
        # You should generate questions about both {name} and any other people or topics relevant to the conversation and to the next reply.
        # For example, if person A asks person B if they like pizza, you could generate this query: "Does person B like pizza?" and "What food does person B like?".
        # The type of the query should be 'PERSONAL' if it's related to someone from the conversation, 'NEWS' if it's about current events, 'RESEARCH' if it's about general or more advanced knowledge, or 'OTHER' if it doesn't fit into any of these categories.
        
        # Your other task is to decide if any content of the message should be memorized. Content that should be memorized is anything personal, either about yourself or another person.
        # This includes statements, plans, interests, appearances and more. You can see it as storing information about something.
        # You should not memorize any information that general knowledge, such as the capital of a country or the date of a holiday, unless specifically asked to do so.
        # The memories should also be written in the third person and include the name of the person the memory is about.
        # For example, a memory about {name} could look like this: {name} likes cookie dough ice cream.
        # Memories should also contain a value of memory_age, which is the age of the memory in days or the date in one of the accepted format. It should be as accurate as possible given the information. This refers to the time the memory is about. For example, if someone said that they had pizza for dinner yesterday, the memory_age is 1. If someone said that they had pizza for dinner on monday, the memory_age is "monday".
        # The truthfulness of the memory should be included in the memory as a float between 0.0 and 1.0, where 0.0 is completely false and 1.0 is completely true. For example, in normal conversation, if someone is making a statement about themselves, it's usually true, so the truthfulness should be close to 1.0. If someone is making a statement about someone else, it could be less true, so the truthfulness should be lower, around 0.8. If the information is very unbelievable or goes against your knowledge, the truthfulness should be lower, around 0.2. If the information is an obvious lie, the truthfulness should be 0.0.
        
        # Queries and memories should contain the entire context they are about. For example, if person A said that he likes pizza, the memory should be "Person A likes pizza.", and not "He likes it."
        # Queries and memories have to contain a value of TimeRelevance, which can be 'NOW', 'WEEK', 'MONTH', 'YEAR', or 'ALWAYS'. This value represents how relevant the information is in time. For example, if the user asks or says something about the current weather, the time relevance is 'NOW', but if the user asks about a a cooking recipe, the time relevance is 'ALWAYS'. Depending on the context, MONTH or YEAR can be used if new information is generally better, but doesn't have to be as up-to-date as NOW. For example, this could be about the latest album of a band or the newest movie in a genre.
        
        # Queries should be used to gain information that is needed to reply to the message, while memories should be used to store information that might be needed in the future. You can not use queries to decide whether to memorize information or not.
        # """

        instructions = f"""Think out loud about the conversation and its state.
        You are given a piece of a conversation and have to evaluate it in order to form a reply, similar to an inner monologue. First, think out loud about the conversation and its state. Decide what kind of reply is expected and what information is needed to form a reply.
        If you already know what is needed or expected, write it down. Otherwise, think about what you would need to know to reply to the message. This could be information about the speaker, the topic, or anything else relevant to the conversation.
        
        Your task then is to decide whether to reply to a chat message or not, based on the conversation context, by generating a probability between 0.0 and 1.0 of replying to the message.
        This number represents how expected it is that the message should be replied to. For example, if you are in a conversation with the speaker or the speaker is asking a question, the probability should be higher.
        If the message is not directed at you, or someone else is expected to reply, the probability should be lower. If it's unclear, the probability should be in the middle.
        
        Then, decide whether it is necessary to think about additional information to reply to the message, by generating up to 3 queries to retrieve information, either from your memory/feelings or from external sources.
        If you don't need additional information, think the answer out loud.
        When thinking about a specific person, including yourself, use the third person and their name. The questions can be about general information or about more personal information. For example, if the user asks about your opinion on digital art, you could first generate a query about digital art in general and then a query about {name}'s opinion on digital art.
        Even if the user didn't directly ask a question, you can still generate queries to retrieve information if it could help in replying to the message.
        You should generate questions about both yourself and any other people or topics relevant to the conversation and to the next reply.
        For example, if person A asks person B if they like pizza, you could generate this query: "Does person B like pizza?" and "What food does person B like?".
        The type of the query should be 'PERSONAL' if it's related to you or someone from the conversation, 'NEWS' if it's about current events, 'RESEARCH' if it's about general or more advanced knowledge, or 'OTHER' if it doesn't fit into any of these categories.
        Don't generate queries about basic common knowledge or the conversation context itself, only about specific information that could be useful for replying.
        
        Your other task is to decide if any content of the message should be memorized. Content that should be memorized is anything personal, either about yourself or another person, or new knowledge that could be useful in the future.
        This includes statements, plans, interests, appearances and more. You can see it as storing information about something.
        You should not memorize any information that very general knowledge, such as the capital of a country or the date of a holiday, unless specifically asked to do so.
        Something that is more specific or something you didn't know yet, even if it's not something personal, should be memorized by using 'GENERAL' as the type and 'NONE' as the person.
        The memories should also be written in the third person and include the name of the person the memory is about.
        For example, a memory about yourself could look like this: "{name} likes cookie dough ice cream."
        Memories should also contain a value of memory_age, which is the age of the memory in days or the date in one of the accepted format. It should be as accurate as possible given the information. This refers to the time the memory is about. For example, if someone said that they had pizza for dinner yesterday, the memory_age is 1. If someone said that they had pizza for dinner on monday, the memory_age is "monday".
        The truthfulness of the memory should be included in the memory as a float between 0.0 and 1.0, where 0.0 is completely false and 1.0 is completely true. For example, in normal conversation, if someone is making a statement about themselves, it's usually true, so the truthfulness should be close to 1.0. If someone is making a statement about someone else, it could be less true, so the truthfulness should be lower, around 0.8. If the information is very unbelievable or goes against your knowledge, the truthfulness should be lower, around 0.2. If the information is an obvious lie, the truthfulness should be 0.0.
        
        Queries and memories should contain the entire context they are about. For example, if person A said that he likes pizza, the memory should be "Person A likes pizza.", and not "He likes it." It should also not contain things like "What is he talking about?" or "What is the conversation about?", only specific questions or statements.
        Queries and memories have to contain a value of TimeRelevance, which can be 'NOW', 'WEEK', 'MONTH', 'YEAR', or 'ALWAYS'. This value represents how relevant the information is in time. For example, if the user asks or says something about the current weather, the time relevance is 'NOW', but if the user asks about a a cooking recipe, the time relevance is 'ALWAYS'. Depending on the context, MONTH or YEAR can be used if new information is generally better, but doesn't have to be as up-to-date as NOW. For example, this could be about the latest album of a band or the newest movie in a genre.
        
        Queries should be used to gain information that is needed to reply to the message, while memories should be used to store information that might be needed in the future. You can not use queries to decide whether to memorize information or not.
        """
        
        # TODO: test this more and remove config instructions if not working well
        # Also maybe adjust evaluator instructions.
        return f"{self.get_config_value("instructions", "")}\n\n{instructions}\n\n{self._get_format_instruction()}"
    
    def _get_format_instruction(self) -> str:
        """
        Get the format for the llm output.
        """
        
        format_instruction = """Use this JSON schema:
        QueryType = 'PERSONAL' | 'NEWS' | 'RESEARCH' | 'OTHER'
        TimeRelevance = 'NOW' | 'WEEK' | 'MONTH' | 'YEAR' | 'ALWAYS'
        MemoryAge = str # str in format #d for age in days, otherwise DD-MM-YYYY or DD-MM or YYYY or DD or name of the weekday or month
        MemoryType = 'PERSONAL' | 'GENERAL'
        Memory = {'memory': str, type: MemoryType, 'person': str | 'NONE', 'topic': str, 'time_relevance': TimeRelevance, 'memory_age': MemoryAge, 'truthfulness': float} # the memory string should be in the third person and only contain the information, not the context (Yes: "Person A likes pizza.", No: "Person B said that A likes pizza.") If the memory is more general knowledge, use 'GENERAL' as the type and 'NONE' as the person.
        Query = {'query': str, 'topic': str, 'type': QueryType, 'time_relevance': TimeRelevance}
        Evaluation = {'thoughts': str, 'reply_expectation': float, 'queries': list[Query], 'memories': list[Memory]}
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
        
        input_messages_length = self.get_config_value("max_evaluation_input_messages", 5)
        if input_messages_length == None or input_messages_length < 1:
            input_messages_length = 1
            
        input_messages = conversation.messages[-input_messages_length:]
        input_messages = [message for message in input_messages if message.user.role != Role.SYSTEM]

        print(f"Eval Input messages: {len(input_messages)}")
        
        system_message = Message(self.get_instructions(), User("System", Role.SYSTEM))
        input_messages.insert(0, system_message)
        
        input_conversation = Conversation(input_messages)
        
        evaluation = Evaluation(input_conversation)
        
        output_message = self.generator.generate(input_conversation)
        if output_message == None:
            return evaluation
        
        output_string = output_message.message_text
        
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
    
    def _get_summary_instructions(self) -> str:
        """
        Get the instructions for summarizing the evaluation.

        Returns
        -------
        str
            The instructions for summarizing the evaluation.
        """
        name = self.get_config_value("name", "Assistant")
        instruction =  f"""Your name is {name}. You are thinking and trying to order and summarize your thoughts. Your task is to create an answer and summary to a given set of questions and answers, alongside the message you are responding to.
        Your answer should be a continuous text that includes the necessary information to answer the questions, but not the questions themselves. If questions or answers are similar enough, you can combine into one information.
        Answer in first person as if you are thinking out loud, based on the type of information. You should start with phrases like "I think", "I remember", "I know", "I read", "I heard", "I believe", or similar.
        For example, if the questions are "What is the capital of France?" and "How many people live in France?", you could answer with "I remember the capital of France is Paris and I think around 67 million people live in France.
        Don't include any information that is not relevant or adds value to the questions or the context of the conversation.
        Also repeat information of your previous answer and thoughts, if any, to summarize everything."""

        return instruction
        
    def summarize_retrieval(self, retrieval:RetrievalResults, prev_summary:str=None) -> str:
        """
        Summarize the retrieval for the evaluation.

        Parameters
        ----------
        retrieval : RetrievalResults
            The retrieval results.

        Returns
        -------
        str
            The summary of the retrieval.
        """
        
        if retrieval == None:
            return None
        
        if len(retrieval) == 0:
            return None
        
        question_str = ""
        answer_str = ""

        for queries in retrieval.results.values():
            if len(queries) == 0:
                continue
            question_str += f"Q: {queries[0].query}\n"
            if queries[0].source != None:
                source_str = ""
                if queries[0].retriever_type == RetrieverType.MEMORY:
                    source_str = "Memory"
                elif queries[0].retriever_type == RetrieverType.WEB:
                    url = queries[0].source
                    title = queries[0].source_title
                    source_str = f"Web: {title} ({url})"
                else:
                    source_str = queries[0].source
                answer_str += f"{source_str}: {queries[0].result}\n\n"
            else:
                answer_str += f"{queries[0].result}\n\n"

        context = f"{question_str}\n{answer_str}"

        summary_conversation = Conversation()

        instruction_message = Message(self._get_summary_instructions(), User("System", Role.SYSTEM))
        summary_conversation.add_message(instruction_message)

        if prev_summary != None:
            prev_summary_message = Message(prev_summary, User(self.get_config_value("name", "Assistant"), Role.ASSISTANT))
            summary_conversation.add_message(prev_summary_message)

        context_message = Message(context, User("Context", Role.USER))
        summary_conversation.add_message(context_message)


        summary_message = self.generator.generate(summary_conversation)

        if summary_message == None:
            return None

        return summary_message.message_text

    def _get_memory_instructions(self) -> str:
        """
        Get the instructions for memorizing information.

        Returns
        -------
        str
            The instructions for memorizing information.
        """
        
        instruction = f"""You are managing and reordering a collection of statements, facts or memories. 
        You will be given a list of memories. Then, your task is to decide how similar the memories are to each other. If two or more memories are similar or even include the same information, you should merge them into one memory by combining the information.
        Memories should be written in the third person and include the name of the person the memory is about. If the memories are about different topics or different people, they should not be merged.
        Before merging, you should first think out loud about your process and what you plan to do. If there are no memories that you think are similar enough, return an empty list.
        
        Use this json schema:
        NewMemory = {'source_ids': list[int], 'memory': str}
        Return: {'thoughts': str, 'new_memories': list[NewMemory]}"""

        return instruction
        
    def merge_memories(self, memories:list[Memory]) -> list[Memory]:
        """
        Merge two lists of memories.

        Parameters
        ----------
        memories : list[Memory]
            A list of potential similar memories.

        Returns
        -------
        list[Memory] | None
            A new list of memories with similar memories merged.
            None if no memories were merged.
        """

        # TODO: move to a system that keeps all memories and groups the ones that are similar / the same / contradicting
        # then, create a summary memory for the group
        # this way, we can keep all memories and still have a way to summarize them
        # also, if we find 3 memories stating A and 1 stating not A, we can keep all
        # of them and based on truthfulness and time relevance decide which one is most likely true
        # optionally, we can also do additional research if we have contradicting memories, until a certain threshold is reached
        
        if len(memories) < 2:
            return None
          
        id_to_memory = {}
        for i, memory in enumerate(memories):
            
            # assign id to memories
            id_to_memory[i] = memory
                
        # create the input message
        request = {
            "memories": [
                {
                    "id": i,
                    "memory": memory.memory
                }
                for i, memory in id_to_memory.items()
            ]  
        }
        

        request_str = json.dumps(request)
        
        input_messages = [
            Message(self._get_memory_instructions(), User("System", Role.SYSTEM)),
            Message(request_str, User("User", Role.USER))
        ]
        input_conversation = Conversation(input_messages)
        
        output_message = self.generator.generate(input_conversation)
        
        if output_message == None:
            return None
        
        output_str = output_message.message_text
        
        new_memories = []
        removed_memories = []
        
        try:
            json_output = json.loads(output_str)
            new_memories = json_output.get("new_memories", [])
        except json.JSONDecodeError:
            print("Error decoding JSON output from generator.")
            print(output_str)
            return None
        except Exception as e:
            print("Error processing output from generator.")
            print(e)
            return None
        
        for new_memory in new_memories:
            source_ids = new_memory.get("source_ids", [])
            memory_str = new_memory.get("memory", "")
            
            if len(source_ids) < 2:
                continue

            source_mems = [id_to_memory[source_id] for source_id in source_ids]
            source_mems = [memory for memory in source_mems if memory not in removed_memories]
            if len(source_mems) < 2:
                continue

            entities = set()
            for source_id in source_ids:
                entities.update(id_to_memory[source_id].entities)
            entities = list(entities)

            topic = id_to_memory[source_ids[0]].topic
            time_relevance = max([id_to_memory[source_id].time_relevance for source_id in source_ids])
            truthfulness = sum([id_to_memory[source_id].truthfulness for source_id in source_ids]) / len(source_ids)
            
            merged_memory = Memory(memory_str, entities, topic, time_relevance, truthfulness)
            new_memories.append(merged_memory)
            
            for source_id in source_ids:
                removed_memories.append(id_to_memory[source_id])
            
        
        if len(new_memories) == 0:
            return None
        
        for memory in memories:
            if memory not in removed_memories:
                new_memories.append(memory)
                
        return new_memories
        
        
        