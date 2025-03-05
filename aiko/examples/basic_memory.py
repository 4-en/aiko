from aiko.pipeline import MemoryPipeline
from aiko.core import Conversation, Message, User, Role
from aiko.utils import get_storage_location

pipeline = MemoryPipeline(root_dir=get_storage_location("example_memory_pipeline"))

USER_NAME = "Alice"
user = User(USER_NAME, Role.USER)
conversation = Conversation()

print("Enter 'exit' to save and exit the program.")
while True:
    user_input = input(f"{USER_NAME}: ")
    if user_input.lower() == 'exit':
        pipeline.save()
        break

    message = Message(user_input, user)
    conversation.add_message(message)

    response = pipeline.generate(conversation)
    if response:
        print(response)
        conversation.add_message(response)
    else:
        print("(no response)")