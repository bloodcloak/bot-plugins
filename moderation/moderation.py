import asyncio
import discord
from discord import guild
from discord import embeds
from discord.enums import VerificationLevel
from discord.ext import commands, tasks
from discord.utils import get
from core import checks
from core.models import PermissionLevel
from datetime import datetime
import logging

logger = logging.getLogger()

class moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.guild = bot.get_guild(int('842915739111653376'))
        self.logChannel = bot.get_channel(int('842940696485822475'))
        self.db = bot.api.get_plugin_partition(self)

        self.excludeRoles = ("Admin", "Staff", "Moderator")
        self.badPhrases = []
        self.scamPhrases = []
        self._dbStartup()

    async def _dbStartup(self):
        logger.warning("Setup DB")
        await self.bot.wait_until_ready()
        badPhrases = await self.db.find_one({"_id": "badPhrases"})
        scamPhrases = await self.db.find_one({"_id": "scamPhrases"})

        if badPhrases is None:
            await self.db.find_one_and_update({"_id": "badPhrases"}, {"$set": {"badPhrases": list()}}, upsert=True)
            badPhrases = await self.db.find_one({"_id": "badPhrases"})

        if scamPhrases is None:
            await self.db.find_one_and_update({"_id": "scamPhrases"}, {"$set": {"scamPhrases": list()}}, upsert=True)
            scamPhrases = await self.db.find_one({"_id": "scamPhrases"})
        
        self.badPhrases = badPhrases.get("badPhrases", list())
        self.scamPhrases = scamPhrases.get("scamPhrases", list())
        logger.warning("Setup Complete")

    @commands.Cog.listener()
    async def on_message(self, msg):
        if msg.author.bot: return

        for y in msg.author.roles:
            if y in self.excludeRoles:
                return

        # Bad Phrase Filter Check
        uContent = msg.content
        for phrase in self.badPhrases:
            if uContent.find(phrase) == -1:
                continue
            else:
                # Trigger Found
                logger.warning(f"User {msg.author} Triggered Phrase Filter")
                await msg.message.delete()

                embed = discord.Embed(
                    title = "Phrase Filter Triggered",
                    description = (f"Message Deleted"),
                    color = discord.Color.red()
                )
                embed.set_field(name="User", value=f"{msg.author.mention} {msg.author.name} ({msg.author.id})", inline=True)
                embed.set_field(name="Channel", value=f"{msg.channel.mention}", inline=True)
                embed.set_field(name="Phrase", value=f"{phrase}", inline=True)
                embed.set_field(name="Content", value=f"{uContent[:900]}", inline=False)
                embed.set_field(name="Content Cont.", value=f"{uContent[900:1800]}", inline=False)
                embed.set_field(name="Content Cont..", value=f"{uContent[1800:2700]}", inline=False)
        
        # Scam Phrase Filter Check
        uContent = msg.content
        for phrase in self.scamPhrases:
            if uContent.find(phrase) == -1:
                continue
            else:
                # Trigger Found
                logger.warning(f"User {msg.author} Triggered Scam Filter")
                try:
                    userObj = await self.bot.fetch_user(int(msg.author.id))
                except Exception:
                    logger.warning(f"User {msg.author} For Kick Not Found")
                    return

                if userObj:
                    await userObj.kick(reason="Scam Phrase Filter Triggered")

                    embed = discord.Embed(
                        title = "Scam Filter Triggered",
                        description = (f"Message Deleted | User Kicked"),
                        color = discord.Color.red()
                    )
                    embed.set_field(name="User", value=f"{msg.author.mention} {msg.author.name} ({msg.author.id})", inline=True)
                    embed.set_field(name="Channel", value=f"{msg.channel.mention}", inline=True)
                    embed.set_field(name="Phrase", value=f"{phrase}", inline=True)
                    embed.set_field(name="Content", value=f"{uContent[:900]}", inline=False)
                    embed.set_field(name="Content Cont.", value=f"{uContent[900:1800]}", inline=False)
                    embed.set_field(name="Content Cont..", value=f"{uContent[1800:2700]}", inline=False)

                await msg.message.delete()

    async def cog_command_error(self, ctx, error):
        """Checks errors"""
        error = getattr(error, "original", error)
        if isinstance(error, commands.CheckFailure):
            await ctx.message.delete()
            return await ctx.send("Error: You don't have permission to run this command!", delete_after=5)
        raise error

    @commands.command()
    @checks.has_permissions(PermissionLevel.MODERATOR)
    async def phrasefilter(self, message, action, phrase):
        validActions = ('add', 'remove', 'list')
        if action not in validActions:
            await message.send('Invalid Args. Usage: `?phraseFilter <action> Valid Actions: `add`, `remove`, `list`')
        else:
            self._FilterManager(message,action, phrase, self.badPhrases)

    @commands.command()
    @checks.has_permissions(PermissionLevel.MODERATOR)
    async def scamfilter(self, message, action, phrase):
        validActions = ('add', 'remove', 'list')
        if action not in validActions:
            await message.send('Invalid Args. Usage: `?scamFilter <action> Valid Actions: `add`, `remove`, `list`')
        else:
            self._FilterManager(message,action, phrase, self.scamPhrases)

    async def _updateDB(self):
        await self.db.find_one_and_update({"_id": "badPhrases"}, {"$set": {"badPhrases": self.badPhrases}}, upsert=True)
        await self.db.find_one_and_update({"_id": "scamPhrases"}, {"$set": {"scamPhrases": self.scamPhrases}}, upsert=True)
    

    async def _FilterManager(self, message, action, phrase, phraseList):
        if action == 'add':
            if phraseList.find(phrase) == -1:
                phraseList.append(phrase)
                await message.send(f"Added `{phrase} to Phrase Filter!")
                self._updateDB()
            else:
                await message.send(f"`{phrase} already exists in filter!")
        elif action == 'remove':
            if phraseList.find(phrase) == -1:
                await message.send(f"`{phrase} not found in Phrase Filter!")
            else:
                phraseList.remove(phrase)
                await message.send(f"`{phrase} removed from Phrase Filter!")
                self._updateDB()
        else:
            # List out the list
            sendString = " ".join(phraseList)
            strLen = len(sendString)
            if strLen > 1900:
                txtCount = 0
                while (txtCount*1900) < strLen:
                    currIter = txtCount*1900
                    await message.send(sendString[currIter:currIter+1900])
                    txtCount += 1
                    logger.warning(f"Phrase Listing Iteration {txtCount}")
            else:
                await message.send(sendString)

def setup(bot):
    bot.add_cog(moderation(bot))