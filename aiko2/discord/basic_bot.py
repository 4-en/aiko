from dotenv import load_dotenv
import os
import discord
from aiko2.core import Conversation, Message, User, Role
from aiko2.pipeline import Pipeline
from aiko2.generator import OpenAIGenerator, Gemini15Flash8B
from aiko2.config import AikoConfig, Config
import traceback

class BasicDiscordBot(discord.Client):
    
    def __init__(self, *, intents, **options):
        super().__init__(intents=intents, **options)
        self.conversations = {}
        config = AikoConfig()
        config.load("config.txt")
        self.pipeline = Pipeline(Gemini15Flash8B(), config=config)
        self.pipeline.config.save()
        self.bot_user = User(self.pipeline.config.name, Role.ASSISTANT)
    
    async def on_ready(self):
        print(f'Logged on as {self.user}!')
        
    async def _generate_reply(self, channel, conversation):
        response = self.pipeline.generate(conversation)
        if response:
            content = response.content
            await channel.send(content)
        

    async def on_message(self, message:discord.Message):
        try:
            print(f'Message from {message.author}: {message.content}')
            
            channel_id = message.channel.id
            user_id = message.author.id
            
            conversation = self.conversations.get(channel_id, Conversation())
            name =  message.author.display_name or message.author.nick or message.author.name or 'User'
            
            if message.author == self.user:
                # add as bot message
                message = Message(content=message.content, user=self.bot_user)
                conversation.add_message(message)
                return
            
            user = User(name=name, role=Role.USER, id=str(user_id))
            aiko_message = Message(content=message.content, user=user)
            conversation.add_message(aiko_message)
            self.conversations[channel_id] = conversation

            await self._generate_reply(message.channel, conversation)
        except Exception as e:
            print(f'Error processing message: {e}')
            traceback.print_exc()
        
            
    async def on_error(self, event, *args, **kwargs):
        print(f'An error occurred in event {event}: {args} {kwargs}')
        
    def main():
        load_dotenv()
        token = os.getenv('DISCORD_SECRET')
        if token is None:
            raise ValueError("Missing Discord token. Set the DISCORD_SECRET environment variable.")
        intents = discord.Intents.all()
        client = BasicDiscordBot(intents=intents)
        client.run(token)
    
if __name__ == '__main__':
    BasicDiscordBot.main()