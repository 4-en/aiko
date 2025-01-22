from aiko2.pipeline import Pipeline
from aiko2.core import Conversation, Message, User, Role
from aiko2.generator import TestGenerator, OpenAIGenerator, GeminiGenerator, Gemini15Flash8B
from aiko2.evaluator import Gemini15Flash8BEvaluator
from aiko2.config import Config

from dotenv import load_dotenv
import logging


class CLI:
    """
    Basic command line interface to rest RAG functions.
    """
    def run():
        logging.basicConfig(level=logging.INFO)

        # Load environment variables
        load_dotenv()

        pipeline = Pipeline(Gemini15Flash8B(), evaluator=Gemini15Flash8BEvaluator())

        print("Welcome to AIKO2!")
        print("Type 'exit' to exit the program.")

        user = User("User", Role.USER)
        conversation = Conversation()


        while True:
            user_input = input("USER: ")
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