from dotenv import load_dotenv
import os
import discord
from aiko2.core import Conversation, Message, User, Role
from aiko2.pipeline import Pipeline
from aiko2.generator import OpenAIGenerator

class BasicDiscordBot(discord.Client):
    
    def __init__(self, *, intents, **options):
        super().__init__(intents=intents, **options)
        self.conversations = {}
        self.pipeline = Pipeline(OpenAIGenerator())
        self.bot_user = User(self.pipeline.config.name, Role.ASSISTANT)
    
    async def on_ready(self):
        print(f'Logged on as {self.user}!')
        
    async def _generate_reply(self, channel, conversation):
        response = self.pipeline.generate(conversation)
        if response:
            content = response.content
            await channel.send(content)
        

    async def on_message(self, message:discord.Message):
        print(f'Message from {message.author}: {message.content}')
        
        channel_id = message.channel.id
        user_id = message.author.id
        
        conversation = self.conversations.get(channel_id, Conversation())
        
        if message.author == self.user:
            # add as bot message
            message = Message(content=message.content, user=self.bot_user)
            conversation.add_message(message)
            return
        
        user = User(name=message.author.name, role=Role.USER)
        message = Message(content=message.content, user=user)
        conversation.add_message(message)
        self.conversations[channel_id] = conversation
        
            
    async def on_error(self, event, *args, **kwargs):
        print(f'An error occurred in event {event}: {args} {kwargs}')
        
def main():
    load_dotenv()
    token = os.getenv('DISCORD_TOKEN')
    intents = discord.Intents.default()
    client = BasicDiscordBot(intents=intents)
    client.run(token)
    
if __name__ == '__main__':
    main()