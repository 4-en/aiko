from dotenv import load_dotenv
import os
import discord
from concurrent.futures import ThreadPoolExecutor
from aiko2.core import Conversation, Message, User, Role
from aiko2.pipeline import Pipeline
from aiko2.generator import OpenAIGenerator, Gemini15Flash8B, GPT4OMiniGenerator
from aiko2.retriever import WebRetriever, MemoryRetriever, RetrievalRouter, query_type_routing_function, negated_routing_function, QueryType
from aiko2.evaluator import Gemini15Flash8BEvaluator
from aiko2.utils import split_text, Memory
import traceback
import asyncio

class BasicDiscordBot(discord.Client):
    
    def __init__(self, *, intents, **options):
        super().__init__(intents=intents, **options)
        self.message_queue: list[tuple[discord.TextChannel, Conversation]] = []
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.conversations: dict[int, Conversation] = {}
        memory_retriever = MemoryRetriever()
        web_retriever = WebRetriever()
        router = RetrievalRouter()
        router.add_retriever(memory_retriever)
        router.add_retriever(web_retriever, negated_routing_function(query_type_routing_function([QueryType.PERSONAL]))) # only use web retriever for non-personal queries
        self.pipeline = Pipeline(Gemini15Flash8B(), retriever=router, evaluator=Gemini15Flash8BEvaluator(), memory_handler=memory_retriever)
        self.bot_user = User(self.pipeline.config.name, Role.ASSISTANT)
        self._generating = False

        self.channel_blacklist = set()
    
    async def on_ready(self):
        print(f'Logged on as {self.user}!')


    async def _send_message(self, channel, content):
        # make sure content is not longer than 2000 characters
        if len(content) > 2000:
            chunks = split_text(content, 1900)
            for chunk in chunks:
                await channel.send(chunk)
                asyncio.sleep(0.5)
        else:
            await channel.send(content)

        
    async def _generate_reply(self, channel:discord.TextChannel, conversation):
        self._generating = True
        async with channel.typing():
            response = await asyncio.get_event_loop().run_in_executor(self.executor, self.pipeline.generate, conversation)
            self._generating = False

            if response:
                content = response.content
                await self._send_message(channel, content)

        if self.message_queue:
            # only respond to the last message in the queue
            # TODO: improve this to handle multiple messages
            channel, conv = self.message_queue.pop(-1)
            self.message_queue = []
            await self._generate_reply(channel, conv)

    async def execute_command(self, message:discord.Message):
        # very basic command to test functions

        if message.content.startswith('!clear'):
            channel_id = message.channel.id
            self.conversations[channel_id] = Conversation()
            await message.channel.send('Conversation cleared.')
            return
        
        if message.content.startswith('!save'):
            print('Saving pipeline...')
            self.pipeline.save()
            await message.channel.send('Pipeline saved.')
            return
        
        if message.content.startswith('!add_memory'):
            memory = message.content.replace('!add_memory', '').strip()
            splits = memory.split(':', maxsplit=1)
            if len(splits) != 2:
                await message.channel.send('Invalid memory format. Use !add_memory <person>:<memory>')
                return
            person, memory = splits
            mem = Memory(person=person, memory=memory, topic=None)
            self.pipeline.memory_handler.add_memory(mem, person)
            await message.channel.send(f'Memory added for {person}.')
            return
        
        if message.content.startswith('!toggle'):
            # toggle replies for this channel
            channel_id = message.channel.id
            if channel_id in self.channel_blacklist:
                self.channel_blacklist.remove(channel_id)
                await message.channel.send('Replies enabled.')
            else:
                self.channel_blacklist.add(channel_id)
                await message.channel.send('Replies disabled.')
            return
        
        if message.content.startswith('!help'):
            help_text = """
            **Available commands:**
            **!clear** - *Clear the conversation*
            **!save** - *Saves memories to disk*
            **!add_memory** <person>:<memory> - *Add a memory*
            **!toggle** - *Toggle replies on/off*
            **!help** - *Show this help*
            """
            embed = discord.Embed(title="Help", description=help_text, color=0x00ff00)
            await message.channel.send(embed=embed)
            return

        
        

    async def on_message(self, message:discord.Message):
        try:
            print(f'Message from {message.author}: {message.content}')

            if message.content == None or message.content == '': return

            if message.content.startswith('!'):
                await self.execute_command(message)
                return
            

            
            channel_id = message.channel.id

            if channel_id in self.channel_blacklist:
                return

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

            if not self._generating:
                await self._generate_reply(message.channel, conversation.copy())
            else:
                self.message_queue.append((message.channel, conversation.copy()))

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