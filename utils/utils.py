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

class utils(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.guild = bot.get_guild(int('842915739111653376'))
        self.logChannel = bot.get_channel(int('842940696485822475'))

    async def cog_command_error(self, ctx, error):
        """Checks errors"""
        error = getattr(error, "original", error)
        if isinstance(error, commands.CheckFailure):
            await ctx.message.delete()
            return await ctx.send("Error: You don't have permission to run this command!", delete_after=5)
        raise error


    @commands.command()
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    async def srvflip(self, message, action):
        validActions = ('panik', 'kalm')
        if action not in validActions:
            await message.send('Invalid Args. Usage: `?srvFlip <action> Valid Actions:\n`panik`: Phone Required\n`kalm`: regular settings')
        else:
            if action == 'panik':
                self.guild.verification_level = discord.VerificationLevel.extreme
                await self.logChannel.send(f'{message.author} ({message.author.id}) Flipped the table in Panik. (Verified Phone Required)')
                logger.warning(f"{datetime.now()} WARN | {message.author} ({message.author.id}) Flipped the table in Panik. (Verified Phone Required)")
            else:
                self.guild.verification_level = discord.VerificationLevel.high
                await self.logChannel.send(f'{message.author} ({message.author.id}) Set to kalm. (10 min in server and email required)')
                logger.warning(f"{datetime.now()} WARN | {message.author} ({message.author.id}) Set the table to kalm. (10 min in server and email required)")

    @commands.command()
    async def rolecheck(self, ctx, member: discord.Member = None):
        """Check a server members roles to see if they are allowed to sell on the server.\nUsage: `?roleCheck <userID>` | Example: `?roleCheck 843260310055550986`"""
        
        if member == None:
                await ctx.send('Error: No user defined. \nUsage: `?roleCheck <userID>` | Example: `?roleCheck 843260310055550986`')
                await asyncio.sleep(5)
        else:
            hasRoles = ""
            userValid = False
            every1 = True
            sellRoles = ("844023616592674866", "844023797996453908", "844023922722078720", "844023941553979402","844023967190614036")
            for y in member.roles:
                if every1:
                    every1 = False
                    continue
                if y.id in sellRoles:
                    userValid = True
                hasRoles = f"<@&{y.id}> " + hasRoles

            if userValid:
                eColor = discord.Color.green()
                trustLevel = "sell"
            elif "844023915830968350" in hasRoles:
                eColor = discord.Color.blue()
                trustLevel = "sell"
            else:
                eColor = discord.Color.orange()
                trustLevel = "**NOT** sell"

            embed = discord.Embed(
                description = (f"Seller Check: <@!{member.id}> can {trustLevel} in the server."),
                color = eColor
            )
            embed.set_author(name=f"{member} ({member.id})", icon_url=str(member.avatar_url))
            embed.add_field(name="Roles", value=hasRoles)

            await ctx.send(embed = embed)

def setup(bot):
    bot.add_cog(utils(bot))