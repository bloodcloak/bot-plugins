import discord
from discord.ext import commands, tasks
from discord.utils import get
from core import checks
from core.models import PermissionLevel
from datetime import datetime, timedelta
import logging

logger = logging.getLogger("Modmail")

class listingPing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.pingChannel = None
        self.guild = None
        self.db = bot.api.get_plugin_partition(self)
        self.timeDelta = timedelta(minutes=1)
        self.msgQueue = dict()

        self.monitorChannels = ('842969358355529728', '842933135654387732', '846142270881005668', '842933105996070953', '842933116213002272', '842933126296895519', '842933147209170975', '842933075826704394', '842933044494336011', '842933058221899787', '842933067500617728', '842933083707932703')

    async def _updateDB(self):
        await self.db.find_one_and_update(
            {"_id": "msgQueue"}, {"$set": {"msgQueue": self.msgQueue}}, upsert=True
        )

    @tasks.loop(seconds=30) #@tasks.loop(minutes=5)
    async def handleQueue(self):
        currTime = datetime.now().timestamp()
        for msgID, obj in self.msgQueue.items():
            if obj["rmTime"] > currTime:
                # Time not elapsed, skip to next item
                continue
            # MSG Due for Ping
            
            ## Determine which role to ping
            pingRole = None
            chanIdx = self.monitorChannels.index(obj["chanID"])

            if chanIdx == 0:
                pingRole = "Map Seller"
            elif chanIdx == 1:
                pingRole = "PC Mod Seller"
            elif chanIdx >= 2 and chanIdx <= 6:
                pingRole = "PC Asset Seller"
            elif chanIdx == 7:
                pingRole = "Quest Mod Seller"
            elif chanIdx >= 8 and chanIdx <= 11:
                pingRole = "Quest Asset Seller"
            else:
                logger.error("Invalid Indexing Occured")
                continue

            ## Process and Ping
            role = get(self.guild.roles, name=pingRole)
            user = self.bot.fetch_user(int(obj["usrID"]))
            channel = self.bot.get_channel(int(obj["chanID"]))
            self.pingChannel.send(f"{role.mention} \n{user} posted a listing in {channel.mention}!\nLink: https://discord.com/channels/842915739111653376/{channel.id}/{msgID}")

            # Pop the entry out
            res = self.msgQueue.pop(str(msgID), None)
            await self._updateDB()
            logger.info("Ping Occured for:", msgID, "\nUser: ", user, "\nResult: \n", res)

    @handleQueue.before_loop
    async def _setDB(self):
        await self.bot.wait_until_ready()
        self.pingChannel = self.bot.get_channel(int('847687831823974440'))
        self.guild = self.bot.get_guild(int('842915739111653376'))
        msgQueue = await self.db.find_one({"_id": "msgQueue"})

        if msgQueue is None:
            await self.db.find_one_and_update(
                {"_id": "msgQueue"}, {"$set": {"msgQueue": dict()}}, upsert=True
            )

            msgQueue = await self.db.find_one({"_id": "msgQueue"})
        
        self.msgQueue = msgQueue.get("msgQueue", dict())

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
                    logger.info("Message Failed Store: ", lowCase)

            if validMsg:
                # Register message for time delay queue
                rmTimeCal = datetime.now() + self.timeDelta

                obStore = {}
                obStore["usrID"] = int(ctx.author.id)
                obStore["msgID"] = int(ctx.id)
                obStore["chanID"] = int(ctx.channel.id)
                obStore["rmTime"] = rmTimeCal.timestamp()
                self.msgQueue[str(ctx.message.id)] = obStore
                await self._updateDB()
                logger.info("Message Triggered Store: \n", obStore)
                return
            
    @commands.Cog.listener()
    async def on_message_delete(self, ctx):
        if ctx.author.bot: return
        
        if str(ctx.channel.id) in self.monitorChannels:
            # Remove from the queue if exists
            res = self.msgQueue.pop(str(ctx.id), None)
            await self._updateDB()
            logger.info("Message Deleted: \n", ctx.id, "\nResult: \n", res)
        
    async def cog_command_error(self, ctx, error):
        """Checks errors"""
        error = getattr(error, "original", error)
        if isinstance(error, commands.CheckFailure):
            await ctx.message.delete()
            return await ctx.send("Error: You don't have permission to run this command!", delete_after=5)
        raise error
        

def setup(bot):
    bot.add_cog(listingPing(bot))