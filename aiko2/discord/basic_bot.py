from dotenv import load_dotenv
import os
import discord
from concurrent.futures import ThreadPoolExecutor
from aiko2.core import Conversation, Message, User, Role, Memory, QueryType
from aiko2.pipeline import Pipeline
from aiko2.generator import OpenAIGenerator, Gemini15Flash8B, GPT4OMiniGenerator, DeepSeekR1DistillQwen7BGenerator, DeepSeekR1DistillQwen1_5BGenerator
from aiko2.retriever import WebRetriever, MemoryRetriever, RetrievalRouter, query_type_routing_function, negated_routing_function
from aiko2.evaluator import Gemini15Flash8BEvaluator, BaseEvaluator
from aiko2.refiner import AikoRefiner
from aiko2.utils import split_text
import traceback
import asyncio
import re
import time

class BasicDiscordBot(discord.Client):
    """
    A basic Discord bot that uses the Aiko2 pipeline to generate responses.
    This is mainly for testing and demonstration purposes.
    """
    
    def __init__(self, pipeline, *, intents, **options):
        super().__init__(intents=intents, **options)
        self.message_queue: list[tuple[discord.TextChannel, Conversation]] = []
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.conversations: dict[int, Conversation] = {}
        self.pipeline = pipeline
        self.bot_user = User(self.pipeline.config.name, Role.ASSISTANT)
        self._generating = False

        self.channel_whitelist = set()
        self.recent_conversations: dict[int, float] = {}
        self.recent_conversation_timeout = 60 * 2 # 2 minutes
    
    async def on_ready(self):
        print(f'Logged on as {self.user}!')

        # set presence
        activity = discord.Activity(type=discord.ActivityType.playing,
                                    name="dm me for a chat!",
                                    details="lule",
                                    platform="TempleOS",
                                    buttons=["Ping", "Pong"])

        await self.change_presence(activity=activity)


    async def _send_message(self, channel, content):
        """
        Send a message to a channel.
        If the content is too long, it will be split into chunks of 1900 characters.
        
        Parameters
        ----------
        channel : discord.TextChannel
            The channel to send the message to
        content : str
            The content of the message"""
        # make sure content is not longer than 2000 characters
        if len(content) > 2000:
            chunks = split_text(content, 1900)
            for chunk in chunks:
                await channel.send(chunk)
                asyncio.sleep(0.5)
        else:
            await channel.send(content)

        
    async def _generate_reply(self, channel:discord.TextChannel, conversation):
        """
        Generate a reply based on the conversation and send it to the channel.
        """
        self._generating = True
        async with channel.typing():
            response = await asyncio.get_event_loop().run_in_executor(self.executor, self.pipeline.generate, conversation)
            self._generating = False

            if response and response.content and response.content.strip() != '':
                content = response.content
                content = await self.insert_emotes(content)
                self.recent_conversations[channel.id] = time.time()
                await self._send_message(channel, content)

        if self.message_queue:
            # only respond to the last message in the queue
            # TODO: improve this to handle multiple messages
            channel, conv = self.message_queue.pop(-1)
            self.message_queue = []
            await self._generate_reply(channel, conv)

    async def execute_command(self, message:discord.Message):
        """
        Execute a command.
        
        Commands:
        !clear - clear the conversation
        !save - save the pipeline
        !add_memory <person>:<memory> - add a memory
        !toggle - toggle replies on/off
        !help - show help
        
        Parameters
        ----------
        message : discord.Message
            The message containing the command
        """
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
            if channel_id in self.channel_whitelist:
                self.channel_whitelist.remove(channel_id)
                await message.channel.send('Replies disabled for this channel.')
            else:
                self.channel_whitelist.add(channel_id)
                await message.channel.send('Replies enabled for this channel.')
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

    async def replace_mentions(self, message:discord.Message, content:str) -> str:
        """
        Replace mentions in the message content with the user's display name.
        """
        for user in message.mentions:
            name = user.display_name or user.nick or user.name
            content = content.replace(f'<@!{user.id}>', name)
        return content
    
    async def replace_emotes(self, content:str) -> str:
        """
        Replace emotes in the message content with the emote's name.
        """
        # replace emotes in format <:name:id> or <a:name:id> with name
        emote_pattern = re.compile(r'<(a)?:\w+:\d+>')
        for match in emote_pattern.finditer(content):
            emote = match.group()
            splits = emote.split(':')
            name = splits[1]
            content = content.replace(emote, name)
        return content
    
    async def insert_emotes(self, message:str):
        """
        Insert emotes in the message content with the emote's name.
        """
        # replace emotes in format <:name:id> or <a:name:id> with name
        client_emotes = self.emojis
        message = f" {message} "
        punctuation = ['.', ',', '!', '?', ':', ';', '(', ')', '[', ']', '{', '}', '<', '>', '"', "'"]
        # add spaces around punctuation
        for p in punctuation:
            message = message.replace(f'{p}', f' {p} ')

        # replace emotes in format <:name:id> or <a:name:id> with name
        for emote in client_emotes:
            message = message.replace(f' {emote.name} ', f' {str(emote)} ')
        
        # revert spaces around punctuation
        for p in punctuation:
            message = message.replace(f' {p} ', f'{p}')
        return message[1:-1]
        

    async def on_message(self, message:discord.Message):
        try:
            print(f'Message from {message.author}: {message.content}')

            if message.content == None or message.content == '': return

            if message.content.startswith('!'):
                await self.execute_command(message)
                return
            

            
            channel_id = message.channel.id
            user_id = message.author.id
            
            conversation = self.conversations.get(channel_id, Conversation())
            name =  message.author.display_name or message.author.nick or message.author.name or 'User'

            content = await self.replace_mentions(message, message.content)
            content = await self.replace_emotes(content)
            
            if message.author == self.user:
                # add as bot message
                message = Message(content=content, user=self.bot_user)
                conversation.add_message(message)
                return
            
            user = User(name=name, role=Role.USER, id=str(user_id))
            aiko_message = Message(content=content, user=user)
            conversation.add_message(aiko_message)
            self.conversations[channel_id] = conversation

            should_reply = (
                channel_id in self.channel_whitelist or
                isinstance(message.channel, discord.DMChannel) or
                message.author == self.user or
                self.user in message.mentions or
                message.channel.id in self.recent_conversations and time.time() - self.recent_conversations[message.channel.id] < self.recent_conversation_timeout
            )

            if not should_reply:
                return

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
        # setup pipeline
        memory_retriever = MemoryRetriever()
        web_retriever = WebRetriever()
        router = RetrievalRouter()
        router.add_retriever(memory_retriever)
        router.add_retriever(web_retriever, negated_routing_function(query_type_routing_function([QueryType.PERSONAL]))) # only use web retriever for non-personal queries
        
        refiner = AikoRefiner()

        generator = Gemini15Flash8B()
        evaluator = BaseEvaluator(generator)
        
        # pipeline = Pipeline(Gemini15Flash8B(), retriever=router, evaluator=Gemini15Flash8BEvaluator(), memory_handler=memory_retriever, refiner=refiner)
        pipeline = Pipeline(generator, retriever=router, evaluator=evaluator, memory_handler=memory_retriever, refiner=refiner)
        
        # setup discord bot
        token = os.getenv('DISCORD_SECRET')
        if token is None:
            raise ValueError("Missing Discord token. Set the DISCORD_SECRET environment variable.")
        intents = discord.Intents.all()
        client = BasicDiscordBot(pipeline, intents=intents)
        client.run(token)
    
if __name__ == '__main__':
    BasicDiscordBot.main()