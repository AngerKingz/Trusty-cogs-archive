import discord
from discord.ext import commands
import aiohttp
import os
from PIL import Image
from PIL import ImageColor
from PIL import ImageFont
from PIL import ImageDraw
from PIL import ImageSequence
from barcode import generate
from barcode.writer import ImageWriter
from redbot.core.data_manager import bundled_data_path
from redbot.core import Config
from io import BytesIO
from .templates import blank_template
from .badge_entry import Badge
import sys
import functools
import asyncio

class Badges:

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, 1545487348434)
        default_guild = {"badges":[]}
        default_global = {"badges": blank_template}
        self.config.register_global(**default_global)
        self.config.register_guild(**default_guild)
        self.session = aiohttp.ClientSession(loop=self.bot.loop)

    def remove_white_barcode(self, img):
        """https://stackoverflow.com/questions/765736/using-pil-to-make-all-white-pixels-transparent"""
        img = img.convert("RGBA")
        datas = img.getdata()

        newData = []
        for item in datas:
            if item[0] == 255 and item[1] == 255 and item[2] == 255:
                newData.append((255, 255, 255, 0))
            else:
                newData.append(item)

        img.putdata(newData)
        return img

    def invert_barcode(self, img):
        """https://stackoverflow.com/questions/765736/using-pil-to-make-all-white-pixels-transparent"""
        img = img.convert("RGBA")
        datas = img.getdata()

        newData = []
        for item in datas:
            if item[0] == 0 and item[1] == 0 and item[2] == 0:
                newData.append((255, 255, 255))
            else:
                newData.append(item)

        img.putdata(newData)
        return img

    async def dl_image(self, url):
        async with self.session.get(url) as resp:
            test = await resp.read()
            return BytesIO(test)

    def make_template(self, user, badge):
        username = user.display_name
        userid = user.id
        department = "GENERAL SUPPORT" if user.top_role.name == "@everyone" else user.top_role.name.upper()
        status = user.status
        if str(user.status) == "online":
            status = "ACTIVE"
        if str(user.status) == "offline":
            status = "COMPLETING TASK"
        if str(user.status) == "idle":
            status = "AWAITING INSTRUCTIONS"
        if str(user.status) == "dnd":
            status = "MIA"
        barcode = BytesIO()
        temp_barcode = generate("code39", str(userid), writer=ImageWriter(), output=barcode)
        barcode = Image.open(barcode)
        barcode = self.remove_white_barcode(barcode)
        fill = (0, 0, 0) # text colour fill
        if badge.is_inverted:
            fill = (255, 255, 255)
            barcode = self.invert_barcode(barcode)
        template = Image.open(str(bundled_data_path(self))+ "/" + badge.file_name)
        template = template.convert("RGBA")        
        barcode = barcode.convert("RGBA")
        barcode = barcode.resize((555,125), Image.ANTIALIAS)
        template.paste(barcode, (400,520), barcode)
        # font for user information
        font_loc = str(bundled_data_path(self)/"arial.ttf") 
        try:
            font1 = ImageFont.truetype(font_loc, 30)
            font2 = ImageFont.truetype(font_loc, 24)
        except Exception as e:
            print(e)
            font1 = None
            font2 = None
        # font for extra information
        
        draw = ImageDraw.Draw(template)
        # adds username
        draw.text((225, 330), str(username), fill=fill, font=font1)
        # adds ID Class
        draw.text((225, 400), badge.code + "-" + str(user).split("#")[1], fill=fill, font=font1)
        # adds user id
        draw.text((250, 115), str(userid), fill=fill, font=font2)
        # adds user status
        draw.text((250, 175), status, fill=fill, font=font2)
        # adds department from top role
        draw.text((250, 235), department, fill=fill, font=font2)
        # adds user level
        draw.text((420, 475), "LEVEL " + str(len(user.roles)), fill="red", font=font1)
        # adds user level
        if badge.badge_name != "discord":
          draw.text((60, 585), str(user.joined_at), fill=fill, font=font2)
        else:
          draw.text((60, 585), str(user.created_at), fill=fill, font=font2)
        return template

    def make_animated_gif(self, template, avatar):
        gif_list = [frame.copy() for frame in ImageSequence.Iterator(avatar)]
        img_list = []
        num = 0
        for frame in gif_list:
            temp2 = template.copy()
            watermark = frame.copy()
            watermark = watermark.convert("RGBA")
            watermark = watermark.resize((100,100))
            watermark.putalpha(128)
            id_image = frame.resize((165, 165))
            temp2.paste(watermark, (845,45, 945,145), watermark)
            temp2.paste(id_image, (60,95, 225, 260))
            temp2.thumbnail((500, 339), Image.ANTIALIAS)
            img_list.append(temp2)
            num += 1
            temp = BytesIO()

            temp2.save(temp, format="GIF", save_all=True, append_images=img_list, duration=0, loop=0)
            temp.name = "temp.gif"
            if sys.getsizeof(temp) > 7000000 and sys.getsizeof(temp) < 8000000:
                break
        return temp

    def make_badge(self, template, avatar):
        watermark = avatar.convert("RGBA")
        watermark.putalpha(128)
        watermark = watermark.resize((100,100))
        id_image = avatar.resize((165, 165))
        template.paste(watermark, (845,45, 945,145), watermark)
        template.paste(id_image, (60,95, 225, 260))
        temp = BytesIO()
        template.save(temp, format="PNG")
        temp.name = "temp.gif"
        return temp

    async def create_badge(self, user, badge):
        task = functools.partial(self.make_template, user=user, badge=badge)
        task = self.bot.loop.run_in_executor(None, task)
        try:
            template = await asyncio.wait_for(task, timeout=60)
        except asyncio.TimeoutError:
            return
        if user.is_avatar_animated():
            avatar = Image.open(await self.dl_image(user.avatar_url_as(format="gif")))
            task = functools.partial(self.make_animated_gif, template=template, avatar=avatar)
            task = self.bot.loop.run_in_executor(None, task)
            try:
                temp = await asyncio.wait_for(task, timeout=60)
            except asyncio.TimeoutError:
                return
            
        else:
            avatar = Image.open(await self.dl_image(user.avatar_url_as(format="png")))
            task = functools.partial(self.make_badge, template=template, avatar=avatar)
            task = self.bot.loop.run_in_executor(None, task)
            try:
                temp = await asyncio.wait_for(task, timeout=60)
            except asyncio.TimeoutError:
                return
            
        temp.seek(0)
        return temp

    async def get_badge(self, badge_name, guild=None):
        if guild is None:
            guild_badges = []
        else:
            guild_badges = await self.config.guild(guild).badges()
        all_badges = await self.config.badges() + guild_badges
        to_return = None
        for badge in all_badges:
            if badge_name.lower() in badge["badge_name"].lower():
                to_return = await Badge.from_json(badge)
        return to_return

    @commands.group(aliases=["badge"])
    async def badges(self, ctx, *, badge):
        """Creates a badge for [cia, nsa, fbi, dop, ioi]"""
        guild = ctx.message.guild
        user = ctx.message.author
        if badge.lower() == "list":
            await ctx.invoke(self.listbadges)
            return
        badge = await self.get_badge(badge, guild)
        if badge is None:
            await ctx.send_help()
            return
        async with ctx.channel.typing():
            badge_img = await self.create_badge(user, badge)
            if badge_img is None:
                await ctx.send("Something went wrong sorry!")
                return
            image = discord.File(badge_img)
            await ctx.send(file=image)


    @commands.command(pass_context=True)
    async def listbadges(self, ctx):
        guild = ctx.message.guild
        global_badges = await self.config.badges()
        guild_badges =  await self.config.guild(guild).badges()
        msg = ", ".join(badge["badge_name"] for badge in global_badges)
        em = discord.Embed()
        #for badge in await self.config.badges():
        em.add_field(name="Global Badges", value=msg)
        if guild_badges != []:
            em.add_field(name="Global Badges", value=", ".join(badge["badge_name"] for badge in guild_badges))
        await ctx.send(embed=em)
    
    
