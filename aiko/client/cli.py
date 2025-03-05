from aiko.pipeline import Pipeline
from aiko.core import Conversation, Message, User, Role
from aiko.generator import TestGenerator, OpenAIGenerator, GeminiGenerator, Gemini15Flash8B
from aiko.evaluator import Gemini15Flash8BEvaluator
from aiko.config import Config
from aiko.retriever import WebRetriever



class CLI:
    """
    Basic command line interface to rest RAG functions.
    """
    def run():
        # logging.basicConfig(level=logging.DEBUG)

        pipeline = Pipeline(Gemini15Flash8B(), evaluator=Gemini15Flash8BEvaluator(), retriever=WebRetriever())

        print("Welcome to Aiko!")
        name = input("What is your name? ")
        print("Type 'exit' to exit the program.")

        user = User(name, Role.USER)
        conversation = Conversation()


        while True:
            user_input = input(f"{name}: ")
            if user_input.lower() == 'exit':
                break

            message = Message(user_input, user)
            conversation.add_message(message)

            response = pipeline.generate(conversation)
            if response:
                print(response)
                conversation.add_message(response)
            else:
                print("(no response)")



if __name__ == '__main__':
    CLI.run()