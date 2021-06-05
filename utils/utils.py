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
from typing import Union

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

    def days(self, day: Union[str, int]) -> str:
        """
        Humanize the number of days.

        Parameters
        ----------
        day: Union[int, str]
            The number of days passed.

        Returns
        -------
        str
            A formatted string of the number of days passed.
        """
        day = int(day)
        if day == 0:
            return "**today**"
        return f"{day} day ago" if day == 1 else f"{day} days ago"

    @commands.command()
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    async def verifylvl(self, message, action):
        validActions = ('panik', 'extreme', 'kalm', 'high')
        if action not in validActions:
            await message.send('Invalid Args. Usage: `?verifylvl <action> Valid Actions:\n`panik`: Phone Required\n`kalm`: regular settings')
        else:
            if action == 'panik' or action == 'extreme':
                await self.guild.edit(verification_level = discord.VerificationLevel.extreme)
                embed = discord.Embed(
                    title = "Server Verifcation Level Updated",
                    description = (f"{message.author.mention} set server level to EXTREME. (Verified Phone Required)"),
                    color = discord.Color.red()
                )
                embed.set_author(name=f"{message.author} ({message.author.id})")
                await self.logChannel.send(embed = embed)
                #await self.logChannel.send(f'{message.author} ({message.author.id}) set server level to EXTREME. (Verified Phone Required)')
                logger.warning(f"{datetime.now()} WARN | {message.author} ({message.author.id}) Flipped the table in Panik. (Verified Phone Required)")
            else:
                await self.guild.edit(verification_level = discord.VerificationLevel.high)
                embed = discord.Embed(
                    title = "Server Verifcation Level Updated",
                    description = (f"{message.author.mention} set server level to High. (10 min in server and email required)"),
                    color = discord.Color.red()
                )
                embed.set_author(name=f"{message.author} ({message.author.id})")
                await self.logChannel.send(embed = embed)
                #await self.logChannel.send(f'{message.author} ({message.author.id}) set server level to kalm. (10 min in server and email required)')
                logger.warning(f"{datetime.now()} WARN | {message.author} ({message.author.id}) Set the table to kalm. (10 min in server and email required)")

    @commands.command()
    async def checkuser(self, ctx, member: discord.Member = None):
        """Check a server members roles to see if they are allowed to sell on the server.\n\nUsage: `?roleCheck <username or ID>` | Example: `?roleCheck "Mod Mail#4190"` or `?roleCheck 843260310055550986`"""
        if str(ctx.channel.id) == '850623919971106866':    
            curTime = datetime.utcnow()
            eColor = discord.Color.orange()

            if member == None:
                    await ctx.send('Error: No user defined. \nUsage: `?roleCheck <username or ID>` \nExample: `?roleCheck "Mod Mail#4190"` or `?roleCheck 843260310055550986`', delete_after=10)
                    await asyncio.sleep(5)
            else:
                created = str((curTime - member.created_at).days)
                joined = str((curTime - member.joined_at).days)

                hasRoles = ""
                userValid = False
                every1 = True
                sellRoles = ("844023616592674866", "844023797996453908", "844023922722078720", "844023941553979402","844023967190614036")
                for y in member.roles:
                    if every1:
                        every1 = False
                        continue
                    if str(y.id) in sellRoles:
                        userValid = True
                    hasRoles = f"<@&{y.id}> " + hasRoles

                if userValid:
                    if eColor:
                        eColor = discord.Color.green()
                    trustLevel = "✅ can"
                else:
                    eColor = discord.Color.orange()
                    trustLevel = "❌ **CANNOT**"

                if not hasRoles:
                    hasRoles = "None"

                embed = discord.Embed(
                    description = (f"{member.mention} {trustLevel} sell commissions in the server."),
                    color = eColor
                )
                embed.set_author(name=f"{member} ({member.id})", icon_url=str(member.avatar_url))
                embed.add_field(name="Account Created", value=self.days(created),inline=True)
                embed.add_field(name="Joined Server", value=self.days(joined),inline=True)
                embed.add_field(name="Roles", value=hasRoles,inline=False)
                await ctx.send(embed = embed)
        else:
            await ctx.message.delete()
            return await ctx.send(embed = discord.Embed(
                title="Channel Error",
                description="Use this command only in <#850623919971106866>!",
                color=discord.Color.red()
            ), delete_after=5)

def setup(bot):
    bot.add_cog(utils(bot))