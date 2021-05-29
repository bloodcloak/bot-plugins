import asyncio
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
        self.timeDelta = timedelta(minutes=4) # How long until users get the ping

        self.msgQueue = dict()
        self.pingdMsgs = dict()
        self.handleQueue.start()

        self.monitorChannels = ('842969358355529728', '842933135654387732', '846142270881005668', '842933105996070953', '842933116213002272', '842933126296895519', '842933147209170975', '842933075826704394', '842933044494336011', '842933058221899787', '842933067500617728', '842933083707932703')
        self.eColor = (0x28b808, 0xad0dec, 0x1ecfc5, 0xc00995, 0x3498db)
        self.keywords = ('status:', 'payment:', 'budget:')

    async def cog_command_error(self, ctx, error):
        """Checks errors"""
        error = getattr(error, "original", error)
        if isinstance(error, commands.CheckFailure):
            await ctx.message.delete()
            return await ctx.send("Error: You don't have permission to run this command!", delete_after=5)
        raise error

    async def _updateDB(self):
        await self.db.find_one_and_update({"_id": "msgQueue"}, {"$set": {"msgQueue": self.msgQueue}}, upsert=True)
    
    async def _updatePingDB(self):
        await self.db.find_one_and_update({"_id": "pingdMsgs"}, {"$set": {"pingdMsgs": self.pingdMsgs}}, upsert=True)

    @tasks.loop(hours=24)
    async def handlePingd(self):
        logger.warning("Starting Cleanup")
        currTime = datetime.now().timestamp()
        pingdCopy = self.pingdMsgs.copy()
        
        for storeKey, obj in pingdCopy.items():
            if obj["rmTime"] > currTime:
                # Time not elapsed, skip to next item
                continue
            
            # Pop the entry out
            res = self.pingdMsgs.pop(storeKey, None)
            logger.warning(f"Removed Ping Record for: {storeKey}")
        
        await self._updatePingDB()
        logger.warning("Cleanup Complete")

    @tasks.loop(minutes=2)
    async def handleQueue(self):
        logger.info("Starting Check")
        currTime = datetime.now().timestamp()
        queueCopy = self.msgQueue.copy()

        for msgID, obj in queueCopy.items():
            if obj["rmTime"] > currTime:
                # Time not elapsed, skip to next item
                continue
            # MSG Due for Ping
            
            ## Determine which role to ping
            pingRole = None
            barColor = None
            chanIDstr = str(obj["chanID"])

            if chanIDstr in self.monitorChannels[0]:
                pingRole = "Map Seller"
                barColor = self.eColor[0]
            elif chanIDstr in self.monitorChannels[1]:
                pingRole = "PC Mod Seller"
                barColor = self.eColor[1]
            elif chanIDstr in self.monitorChannels[2:7]:
                pingRole = "PC Asset Seller"
                barColor = self.eColor[2]
            elif chanIDstr in self.monitorChannels[7]:
                pingRole = "Quest Mod Seller"
                barColor = self.eColor[3]
            elif chanIDstr in self.monitorChannels[8:12]:
                pingRole = "Quest Asset Seller"
                barColor = self.eColor[4]
            else:
                logger.error(f"Invalid Indexing Occured: {chanIDstr}")
                continue

            ## Process and Ping
            role = get(self.guild.roles, name=pingRole)
            user = await self.bot.fetch_user(int(obj["usrID"]))
            channel = self.bot.get_channel(int(obj["chanID"]))
            embed = discord.Embed()
            embed.color = barColor
            embed.description = (f"{user} posted a listing in {channel.mention}!\n[Direct Link to Listing](https://discord.com/channels/842915739111653376/{channel.id}/{msgID})")
            await self.pingChannel.send(f"{role.mention}", embed = embed)

            # Pop the entry to ping record
            res = self.msgQueue.pop(str(obj["msgID"]), None)

            rmTimeCal = datetime.now() + timedelta(days=30)
            storeKey = f"{user.id}-{channel.id}_{msgID}"
            obStore = {}
            obStore["usrNM"] = str(f"{user}")
            obStore["pingTime"] = str(datetime.now())
            obStore["rmTime"] = rmTimeCal.timestamp()
            self.pingdMsgs[storeKey] = obStore

            await self._updateDB()
            await self._updatePingDB()
            logger.warning(f"Ping Occured for: {msgID} User: {user}")
            await asyncio.sleep(0.1)

        logger.info("Check Complete")

    @handleQueue.before_loop
    async def _setDB(self):
        logger.warning("Setup DB")
        await self.bot.wait_until_ready()
        msgQueue = await self.db.find_one({"_id": "msgQueue"})
        pingdMsgs = await self.db.find_one({"_id": "pingdMsgs"})

        if msgQueue is None:
            await self.db.find_one_and_update({"_id": "msgQueue"}, {"$set": {"msgQueue": dict()}}, upsert=True)
            msgQueue = await self.db.find_one({"_id": "msgQueue"})

        if pingdMsgs is None:
            await self.db.find_one_and_update({"_id": "pingdMsgs"}, {"$set": {"pingdMsgs": dict()}}, upsert=True)
            pingdMsgs = await self.db.find_one({"_id": "pingdMsgs"})
        
        self.msgQueue = msgQueue.get("msgQueue", dict())
        self.pingdMsgs = pingdMsgs.get("pingdMsgs", dict())
        self.handlePingd.start()
        logger.warning("Setup Complete")

    @commands.Cog.listener()
    async def on_message(self, ctx):
        if ctx.author.bot: return
        
        if str(ctx.channel.id) in self.monitorChannels:
            lowCase = ctx.content.lower()

            for keyword in self.keywords:
                if lowCase.find(keyword) == -1:
                    logger.warning(f"Message Failed Store: {lowCase}")
                    return

            # Register message for time delay queue
            rmTimeCal = datetime.now() + self.timeDelta

            obStore = {}
            obStore["usrID"] = int(ctx.author.id)
            obStore["msgID"] = int(ctx.id)
            obStore["chanID"] = int(ctx.channel.id)
            obStore["rmTime"] = rmTimeCal.timestamp()
            self.msgQueue[str(ctx.id)] = obStore
            await self._updateDB()
            logger.warning(f"Message Triggered Store: {ctx.channel.id} {ctx.id}")
            return
            
    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot: return

        if str(after.channel.id) in self.monitorChannels:
            lowCase = after.content.lower()
            validMsg = True
            
            for keyword in self.keywords:
                if lowCase.find(keyword) == -1:
                    validMsg = False

            if str(after.id) in self.msgQueue:
                if validMsg:
                    # Note valid edit
                    logger.warning(f"Valid Message Passed Edit Check: {after.id}")
                    return
                else:
                    # Remove from the queue if exists
                    res = self.msgQueue.pop(str(after.id), None)
                    await self._updateDB()
                    logger.warning(f"Valid Message Failed Edit Check: {after.id} \nResult: {res}")
                    return
            else:
                if validMsg:
                    # Check if the message already had a ping
                    storeKey = f"{after.author.id}-{after.channel.id}_{after.id}"
                    if storeKey in self.pingdMsgs: return # Already did the ping
                    
                    # Register message for time delay queue
                    rmTimeCal = datetime.now() + self.timeDelta

                    obStore = {}
                    obStore["usrID"] = int(after.author.id)
                    obStore["msgID"] = int(after.id)
                    obStore["chanID"] = int(after.channel.id)
                    obStore["rmTime"] = rmTimeCal.timestamp()
                    self.msgQueue[str(after.id)] = obStore
                    await self._updateDB()
                    logger.warning(f"Failed Message Edit Triggered Store: {after.channel.id} {after.id}")
                    return
                else:
                    logger.warning(f"Failed Message Failed Edit Check: {after.id}")
                    return


    @commands.Cog.listener()
    async def on_message_delete(self, ctx):
        if ctx.author.bot: return
        
        if str(ctx.channel.id) in self.monitorChannels:
            # Remove from the queue if exists
            res = self.msgQueue.pop(str(ctx.id), None)
            await self._updateDB()
            logger.warning(f"Message Deleted: {ctx.id} \nResult: {res}")
        
    @commands.command()
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    async def resetcheck(self,ctx):
        self.handleQueue.cancel()
        self.handlePingd.cancel()
        self.handleQueue.start()
        self.handlePingd.start()
        logger.warning(f"Check Reset by {ctx.author}")
        await ctx.send("Reset!")
    
    @commands.command()
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    async def stopcheck(self,ctx):
        self.handleQueue.cancel()
        self.handlePingd.cancel()
        logger.warning(f"Check Stopped by {ctx.author}")
        await ctx.send("Stopped!")

    @commands.command()
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    async def startcheck(self,ctx):
        self.handleQueue.start()
        self.handlePingd.start()
        logger.warning(f"Check Started by {ctx.author}")
        await ctx.send("Started!")

def setup(bot):
    bot.add_cog(listingPing(bot))

def cog_unload(self):
    self.handleQueue.cancel()