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

    async def on_ready(self):
        logger.warning("Setup DB")
        badPhrases = await self.db.find_one({"_id": "badPhrases"})
        scamPhrases = await self.db.find_one({"_id": "scamPhrases"})

        if badPhrases is None:
            await self.db.find_one_and_update({"_id": "badPhrases"}, {"$set": {"badPhrases": dict()}}, upsert=True)
            badPhrases = await self.db.find_one({"_id": "badPhrases"})

        if scamPhrases is None:
            await self.db.find_one_and_update({"_id": "scamPhrases"}, {"$set": {"scamPhrases": dict()}}, upsert=True)
            scamPhrases = await self.db.find_one({"_id": "scamPhrases"})
        
        self.badPhrases = badPhrases.get("badPhrases", dict())["phrases"]
        self.scamPhrases = scamPhrases.get("scamPhrases", dict())["phrases"]
        logger.warning("Setup Complete")

    @commands.Cog.listener()
    async def on_message(self, msg):
        if msg.author.bot: return

        for y in msg.author.roles:
            if y.name in self.excludeRoles:
                return
        uContent = msg.content.lower()

        # Scam Phrase Filter Check
        for phrase in self.scamPhrases:
            if phrase in uContent:
                # Trigger Found
                logger.warning(f"User {msg.author} Triggered Scam Filter")
                try:
                    userObj = await self.bot.fetch_user(int(msg.author.id))
                except Exception:
                    logger.warning(f"User {msg.author} For Kick Not Found")
                    return

                if userObj:
                    await self.guild.kick(userObj, reason="Scam Phrase Filter Triggered")

                    embed = discord.Embed(
                        title = "Scam Filter Triggered",
                        description = (f"Message Deleted | User Kicked"),
                        color = discord.Color.red()
                    )
                    embed.add_field(name="User", value=f"{msg.author.mention} {msg.author.name} ({msg.author.id})", inline=True)
                    embed.add_field(name="Channel", value=f"{msg.channel.mention}", inline=True)
                    embed.add_field(name="Phrase", value=f"{phrase}", inline=True)
                    embed.add_field(name="Content", value=f"{uContent[:900]}", inline=False)
                    embed.add_field(name="Content Cont.", value=f"{uContent[900:1800]}", inline=False)
                    embed.add_field(name="Content Cont..", value=f"{uContent[1800:2700]}", inline=False)

                await msg.delete()
                return await msg.send(embed=embed)

        # Bad Phrase Filter Check
        for phrase in self.badPhrases:
            if phrase in uContent:
                # Trigger Found
                logger.warning(f"User {msg.author} Triggered Phrase Filter")
                await msg.delete()

                embed = discord.Embed(
                    title = "Phrase Filter Triggered",
                    description = (f"Message Deleted"),
                    color = discord.Color.red()
                )
                embed.add_field(name="User", value=f"{msg.author.mention} {msg.author.name} ({msg.author.id})", inline=True)
                embed.add_field(name="Channel", value=f"{msg.channel.mention}", inline=True)
                embed.add_field(name="Phrase", value=f"{phrase}", inline=True)
                embed.add_field(name="Content", value=f"{uContent[:900]}", inline=False)
                embed.add_field(name="Content Cont.", value=f"{uContent[900:1800]}", inline=False)
                embed.add_field(name="Content Cont..", value=f"{uContent[1800:2700]}", inline=False)
                return await msg.send(embed=embed)

    async def cog_command_error(self, ctx, error):
        """Checks errors"""
        error = getattr(error, "original", error)
        if isinstance(error, commands.CheckFailure):
            await ctx.message.delete()
            return await ctx.send("Error: You don't have permission to run this command!", delete_after=5)
        raise error

    @commands.command()
    @checks.has_permissions(PermissionLevel.MODERATOR)
    async def phrasefilter(self, message, action, *, phrase=None):
        validActions = ('add', 'remove', 'list')
        if action not in validActions:
            await message.send('Invalid Args. Usage: `?phraseFilter <action> Valid Actions: `add`, `remove`, `list`')
        else:
            await self._FilterManager(message,action, phrase, self.badPhrases)

    @commands.command()
    @checks.has_permissions(PermissionLevel.MODERATOR)
    async def scamfilter(self, message, action, *, phrase=None):
        validActions = ('add', 'remove', 'list')
        if action not in validActions:
            await message.send('Invalid Args. Usage: `?scamFilter <action> Valid Actions: `add`, `remove`, `list`')
        else:
            await self._FilterManager(message,action, phrase, self.scamPhrases)

    async def _updateDB(self):
        obstoreB = {}
        obstoreS = {}

        obstoreB["phrases"] = self.badPhrases
        obstoreS["phrases"] = self.scamPhrases
        await self.db.find_one_and_update({"_id": "badPhrases"}, {"$set": {"badPhrases": obstoreB}}, upsert=True)
        await self.db.find_one_and_update({"_id": "scamPhrases"}, {"$set": {"scamPhrases": obstoreS}}, upsert=True)
    

    async def _FilterManager(self, message, action, phrase, phraseList):
        if action == 'add':
            if phrase == None:
                await message.send(f"`Missing Arg: `phrase`!")
            if not phrase in phraseList:
                phraseList.append(phrase.lower())
                await message.send(f"Added `{phrase.lower()}` to Filter!")
                await self._updateDB()
            else:
                await message.send(f"`{phrase.lower()}` already exists in filter!")
        elif action == 'remove':
            if not phrase in phraseList:
                await message.send(f"`{phrase.lower()}` not found in Filter!")
            else:
                phraseList.remove(phrase.lower())
                await message.send(f"`{phrase.lower()}` removed from Filter!")
                await self._updateDB()
        else:
            # List out the list
            sendString = "Filtered Phrases: "
            for phrase in phraseList:
                sendString += f"`{phrase}`, "
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