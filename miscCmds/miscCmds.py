import asyncio
import discord
from discord import guild
from discord.enums import VerificationLevel
from discord.ext import commands, tasks
from discord.utils import get
from core import checks
from core.models import PermissionLevel
from datetime import datetime, timedelta
import logging

logger = logging.getLogger()

class miscCmds(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
        self.guild = bot.get_guild(int('842915739111653376'))
        self.welcomeChan = str('842915739111653379')
        self.pingChannel = bot.get_channel(int('842940696485822475'))
        self.timeDelta = timedelta(seconds=45)
        self.pingCooldown = False
        self.rmCooldown = datetime.now().timestamp()

        self.welQueue = dict()
        self.checkQueue.start()

    async def cog_command_error(self, ctx, error):
        """Checks errors"""
        error = getattr(error, "original", error)
        if isinstance(error, commands.CheckFailure):
            await ctx.message.delete()
            return await ctx.send("Error: You don't have permission to run this command!", delete_after=5)
        raise error

    '''
    @commands.command()
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    async def raidPanic(self, ctx):
        await self.bot.edit(VerificationLevel)
    '''

    @tasks.loop(minutes=1)
    async def checkQueue(self):
        currTime = datetime.now().timestamp()
        welCopy = self.welQueue.copy()

        if self.pingCooldown:
            if self.rmCooldown.timestamp() < currTime:
                self.pingCooldown = False
                logger.warning(f"+++++ Ping Cooldown Reset!")

        if len(welCopy) >= 5:
            logger.warning(f"+++++ Unusual Join Activity Detected +++++++")
            if self.pingCooldown:
                logger.warning(f"+++++ | Ping In Cooldown | +++++++")
            else:
                await self.pingChannel.send("<@842916395519574037> Unusual Join Activity Detected")
                self.pingCooldown = True
                self.rmCooldown = datetime.now() + timedelta(minutes=5)
                logger.warning(f"+++++ | Ping Sent | +++++++")
            

        for storeKey, obj in welCopy.items():
            if obj["rmTime"] > currTime:
                # Time not elapsed, skip to next item
                continue

            # Pop Entry from database
            res = self.welQueue.pop(storeKey, None)
            await asyncio.sleep(0.1)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        # add to queue
        rmTimeCal = datetime.now() + self.timeDelta
        obStore = {}
        obStore["rmTime"] = rmTimeCal.timestamp()
        obStore["usrNM"] = str(member)
        self.welQueue[str(member.id)] = obStore
        logger.info(f"New member joined {str(member)}")

    @commands.command()
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    async def stopwel(self,ctx):
        self.checkQueue.cancel()
        logger.warning(f"Welcome Channel Check Stopped by {ctx.author}")
        await ctx.send("Stopped!")

    @commands.command()
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    async def startwel(self,ctx):
        self.checkQueue.start()
        logger.warning(f"Welcome Channel Check Started by {ctx.author}")
        await ctx.send("Started!")

def setup(bot):
    bot.add_cog(miscCmds(bot))

def cog_unload(self):
    self.checkQueue.cancel()