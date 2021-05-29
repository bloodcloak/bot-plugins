import discord
from discord.ext import commands, tasks
from discord.utils import get
from core import checks
from core.models import PermissionLevel
from datetime import datetime, timedelta
import logging

logger = logging.getLogger()

class listingPing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.pingChannel = bot.get_channel(int('847687831823974440'))
        self.guild = bot.get_guild(int('842915739111653376'))
        self.db = bot.api.get_plugin_partition(self)
        self.timeDelta = timedelta(minutes=1)
        self.msgQueue = dict()
        self.handleQueue.start()

        self.monitorChannels = ('842969358355529728', '842933135654387732', '846142270881005668', '842933105996070953', '842933116213002272', '842933126296895519', '842933147209170975', '842933075826704394', '842933044494336011', '842933058221899787', '842933067500617728', '842933083707932703')

    async def cog_command_error(self, ctx, error):
        """Checks errors"""
        error = getattr(error, "original", error)
        if isinstance(error, commands.CheckFailure):
            await ctx.message.delete()
            return await ctx.send("Error: You don't have permission to run this command!", delete_after=5)
        raise error

    async def _updateDB(self):
        await self.db.find_one_and_update(
            {"_id": "msgQueue"}, {"$set": {"msgQueue": self.msgQueue}}, upsert=True
        )

    @tasks.loop(seconds=30) #@tasks.loop(minutes=5)
    async def handleQueue(self):
        logger.warning("Starting Check")
        currTime = datetime.now().timestamp()
        queueCopy = self.msgQueue.copy()

        for msgID, obj in queueCopy.items():
            if obj["rmTime"] > currTime:
                # Time not elapsed, skip to next item
                continue
            # MSG Due for Ping
            
            ## Determine which role to ping
            pingRole = None

            chanIDstr = str(obj["chanID"])

            if chanIDstr in self.monitorChannels[0]:
                pingRole = "Map Seller"
            elif chanIDstr in self.monitorChannels[1]:
                pingRole = "PC Mod Seller"
            elif chanIDstr in self.monitorChannels[2:7]:
                pingRole = "PC Asset Seller"
            elif chanIDstr in self.monitorChannels[8]:
                pingRole = "Quest Mod Seller"
            elif chanIDstr in self.monitorChannels[9:12]:
                pingRole = "Quest Asset Seller"
            else:
                logger.error("Invalid Indexing Occured")
                continue

            ## Process and Ping
            role = get(self.guild.roles, name=pingRole)
            user = await self.bot.fetch_user(int(obj["usrID"]))
            channel = self.bot.get_channel(int(obj["chanID"]))
            await self.pingChannel.send(f"{role.mention} {user} posted a listing in {channel.mention}!\nLink: https://discord.com/channels/842915739111653376/{channel.id}/{msgID}")

            # Pop the entry out
            res = self.msgQueue.pop(str(obj["msgID"]), None)
            await self._updateDB()
            logger.warning("Ping Occured for:", msgID, "\nUser: ", user, "\nResult: \n", res)
        logger.warning("Check Complete")

    @handleQueue.before_loop
    async def _setDB(self):
        logger.warning("Setup DB")
        await self.bot.wait_until_ready()
        msgQueue = await self.db.find_one({"_id": "msgQueue"})

        if msgQueue is None:
            await self.db.find_one_and_update(
                {"_id": "msgQueue"}, {"$set": {"msgQueue": dict()}}, upsert=True
            )

            msgQueue = await self.db.find_one({"_id": "msgQueue"})
        
        self.msgQueue = msgQueue.get("msgQueue", dict())
        logger.warning("Setup Complete")

    @commands.Cog.listener()
    async def on_message(self, ctx):
        if ctx.author.bot: return
        
        if str(ctx.channel.id) in self.monitorChannels:
            validMsg = True
            keywords = ('status:', 'payment:', 'budget:')
            lowCase = ctx.content.lower()

            for keyword in keywords:
                if lowCase.find(keyword) == -1:
                    validMsg = False
                    logger.warning("Message Failed Store: ", lowCase)

            if validMsg:
                # Register message for time delay queue
                rmTimeCal = datetime.now() + self.timeDelta

                obStore = {}
                obStore["usrID"] = int(ctx.author.id)
                obStore["msgID"] = int(ctx.id)
                obStore["chanID"] = int(ctx.channel.id)
                obStore["rmTime"] = rmTimeCal.timestamp()
                self.msgQueue[str(ctx.id)] = obStore
                await self._updateDB()
                logger.warning("Message Triggered Store: \n", obStore)
                return
            
    @commands.Cog.listener()
    async def on_message_delete(self, ctx):
        if ctx.author.bot: return
        
        if str(ctx.channel.id) in self.monitorChannels:
            # Remove from the queue if exists
            res = self.msgQueue.pop(str(ctx.id), None)
            await self._updateDB()
            logger.warning("Message Deleted: \n", ctx.id, "\nResult: \n", res)
        
    @commands.command()
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    async def resetcheck(self,ctx):
        self.handleQueue.cancel()
        self.handleQueue.start()
        await ctx.send("Reset!")
    
    @commands.command()
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    async def stopcheck(self,ctx):
        self.handleQueue.cancel()
        await ctx.send("Stopped!")

    @commands.command()
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    async def startcheck(self,ctx):
        self.handleQueue.start()
        await ctx.send("Started!")

def setup(bot):
    bot.add_cog(listingPing(bot))

def cog_unload(self):
        self.handleQueue.cancel()