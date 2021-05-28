import discord
from discord.ext import commands
from discord.utils import get
from core import checks
from core.models import PermissionLevel

class listingPing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.pingChannel = self.bot.get_channel(int('847687831823974440'))
        self.db = bot.api.get_plugin_partition(self)

        self.monitorChannels = ('842969358355529728', '842933135654387732', '846142270881005668', '842933105996070953', '842933116213002272', '842933126296895519', '842933147209170975', '842933075826704394', '842933044494336011', '842933058221899787', '842933067500617728', '842933083707932703')

    # self.bot.get_channel(int(self.pingChannel))

    @commands.Cog.listener()
    async def on_message(self, ctx):
        if ctx.author.bot: return
        
        if str(ctx.channel.id) in self.monitorChannels:
            # Register message for time delay queue
            obStore = {}
            obStore["msgID"] = int(ctx.message.id)
            obStore["chanID"] = int(ctx.channel.id)
            
    @commands.Cog.listener()
    async def on_message_delete(self, ctx):
        if ctx.author.bot: return
        
        if str(ctx.channel.id) in self.monitorChannels:
            # Check and remove from the queue

    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    @commands.command()
    async def setPingChannel(self, ctx, channel: discord.TextChannel):
        """Sets the media log channel"""
        await self.db.find_one_and_update({'_id': 'config'}, {'$set': {'log_channel': str(channel.id), 'monitored_channels': []}}, upsert=True)
        await ctx.send('Success')

    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    @commands.command()
    async def setMonitor(self, ctx, channel: discord.TextChannel, rolename = None):
        """Sets the channel to monitor for pings"""
        if await self.is_monitored(channel):
            await self.db.find_one_and_update({'_id': 'config'}, {'$pull': {'monitored_channels': str(channel.id)}}, upsert=True)
            await ctx.send('Removed Channel From Monitor')
        else:
            await self.db.find_one_and_update({'_id': 'config'}, {'$addToSet': {'monitored_channels': str(channel.id)}}, upsert=True)
            await ctx.send('Added Channel To Monitor')
        
    async def cog_command_error(self, ctx, error):
        """Checks errors"""
        error = getattr(error, "original", error)
        if isinstance(error, commands.CheckFailure):
            await ctx.message.delete()
            return await ctx.send("Error: You don't have permission to run this command!", delete_after=5)
        raise error
        