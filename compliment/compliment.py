import discord
from discord.ext import commands
from .utils.dataIO import fileIO
from random import choice as randchoice
import os


class Compliment:

    """Airenkun's Insult Cog"""
    def __init__(self, bot):
        self.bot = bot
        self.compliments = fileIO("data/compliment/compliment.json", "load")

    @commands.command(pass_context=True, no_pm=True, aliases=["cpl"])
    async def compliment(self, ctx, user : discord.Member=None):
        """Compliment the user"""

        msg = ' '
        if user != None:

            if user.id == self.bot.user.id:
                user = ctx.message.author
                msg = [" Hey I appreciate the compliment! :smile:", "No ***YOU'RE*** awesome! :smile:"]
                await self.bot.say(user.mention + randchoice(msg))

            else:
                await self.bot.say(user.mention + msg + randchoice(self.compliments))
        else:
            await self.bot.say(ctx.message.author.mention + msg + randchoice(self.compliments))


def check_folders():
    folders = ("data", "data/compliment/")
    for folder in folders:
        if not os.path.exists(folder):
            print("Creating " + folder + " folder...")
            os.makedirs(folder)


def check_files():
    """Moves the file from cogs to the data directory. Important -> Also changes the name to insults.json"""
    insults = {"You ugly as hell damn. Probably why most of your friends are online right?"}

    if not os.path.isfile("data/compliment/compliment.json"):
        print("creating default compliment.json...")
        fileIO("data/compliment/compliment.json", "save", insults)


def setup(bot):
    check_folders()
    check_files()
    n = Compliment(bot)
    bot.add_cog(n)
