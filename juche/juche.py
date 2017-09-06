import discord
from discord.ext import commands
from .utils.chat_formatting import *
from .utils.dataIO import dataIO
from .utils.dataIO import fileIO
from cogs.utils import checks
from random import choice
from binascii import unhexlify
import time
import random
import hashlib
import aiohttp
import asyncio
import string
import re

class Juche:

    def __init__(self, bot):
        self.bot = bot
    
    async def check_date(self, message):
        for i in range(1912, 2100):
            if str(i) in message.split(" ") and "http" not in message:
                message = message.replace(str(i), "Juche " + str(i-1912+1))
                message = "I think you mean Juche " + str(i-1912+1) + "."
                return message

        return None

    async def on_message(self, message):
        msg = message.content
        server = message.server
        channel = message.channel

        if server.id in ["304436539482701825", "321105104931389440"]:
            juche = await self.check_date(msg)
            if juche != None:
                await self.bot.send_message(channel, juche)

def setup(bot):
    n = Juche(bot)
    bot.add_cog(n)