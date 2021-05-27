import discord
from discord.ext import commands
from discord.utils import get
from core import checks
from core.models import PermissionLevel

class roleResponse(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logChannel = None
        self.db = bot.api.get_plugin_partition(self)

    async def cog_command_error(self, ctx, error):
        """Checks errors"""
        error = getattr(error, "original", error)
        if isinstance(error, commands.CheckFailure):
            await ctx.message.delete()
            return await ctx.send("Error: You don't have permission to run this command!", delete_after=5)
        raise error

    @commands.command()
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    async def giverole(self, ctx, member: discord.Member = None, rolename = None):
        valid_roles = ('map', 'pcmod', 'questmod', 'pcasset', 'questasset', 'trusted')

        if rolename not in valid_roles:
            await ctx.send('Invalid Args. Usage: `?giverole <member> <rolename>` \nValid Rolenames: ' + ', '.join(valid_roles))
        else:
            if member == None:
                await ctx.send('Error: No user defined')

            # Role SwitchCase =================================================
            role_name = rolename.lower()
            nameRole = None

            if role_name == 'map':
                nameRole = "Map Seller"
                infoChannel = "<#842968453194186763>"

            elif role_name == 'pcasset':
                nameRole = "PC Asset Seller"
                infoChannel = "<#842968541368156181>"
            elif role_name == 'questasset':
                nameRole = "Quest Asset Seller"
                infoChannel = "<#842968541368156181>"

            elif role_name == 'pcmod':
                nameRole = "PC Mod Seller"
                infoChannel = "<#842968799439224853>"
            elif role_name == 'questmod':
                nameRole = "Quest Mod Seller"
                infoChannel = "<#842968799439224853>"
            
            elif role_name == 'trusted':
                nameRole = "Trusted Seller"
                infoChannel = "<#843007832767856650>"

            else:
                return await ctx.send('An Error occured when adding role: `Role name not valid` ')

            # Role Processing =============================================
            try:
                role = get(ctx.guild.roles, name=nameRole)
                await member.add_roles(role)
            except:
                return await ctx.send('An Error occured when adding role: `Role Not Found` \nPlease contact an Admin.')

            try:
                if role_name != 'trusted':
                    await member.send(
                        embed=discord.Embed(
                            description=(
                                f"Congratulations, your application for {nameRole} in the Beat Saber Commissions Center has been accepted!\n\n"
                                "You've been given the following permissions:\n"
                                "- The ability to let people commission you through the Beat Saber Commissions Center\n"
                                "- Access to <#843007803706048543> and <#843551411571785778>\n"
                                f"- Permission to talk in {infoChannel} so you can post your commission info\n\n"
                                "Make sure to double check the rules in <#842919779357556766> before posting your info! If you have any questions, <#843007803706048543> will be happy to answer."
                            ),
                            color=discord.Colour.green(),
                        ).set_footer(text="This is an automated message. If you want to contact staff, DM me to open a ticket!")
                    )
                else:
                    await member.send(
                        embed=discord.Embed(
                            description=(
                                f"Congratulations, your application for {nameRole} in the Beat Saber Commissions Center has been accepted!\n\n"
                                "You've been given the following permissions:\n"
                                f"- Access to {infoChannel}\n"
                                "- The Trusted Seller role\n"
                            ),
                            color=discord.Colour.green(),
                        ).set_footer(text="This is an automated message. If you want to contact staff, DM me to open a ticket!")
                    )
            except discord.errors.Forbidden:
                await self.log(
                    guild=ctx.guild,
                    embed=discord.Embed(
                        title=f"{member} ({member.id})",
                        description=f"{member.mention}'s application for {role.mention} was accepted by {ctx.author.mention}. \n An error occured in sending confirmation to user.",
                        color=discord.Colour.gold(),
                    ),
                )
                return await ctx.send('Role has been applied. User has not been notified as they do not have DM\'s open.')

            await self.log(
                guild=ctx.guild,
                embed=discord.Embed(
                    title=f"{member} ({member.id})",
                    description=f"{member.mention}'s application for {role.mention} was accepted by {ctx.author.mention}",
                    color=discord.Colour.green(),
                ),
            )

    @commands.command()
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    async def denyrole(self, ctx, member: discord.Member = None, rolename = None, *, reason = None):
        valid_roles = ('map', 'pcmod', 'questmod', 'pcasset', 'questasset', 'trusted')

        if rolename not in valid_roles:
            await ctx.send('Invalid Args. Usage: `?denyrole <member> <rolename> [reason]` \nValid Rolenames: ' + ', '.join(valid_roles))
        else:
            if member == None:
                await ctx.send('Error: No user defined')

            # Role SwitchCase =================================================
            role_name = rolename.lower()
            nameRole = None

            if role_name == 'map':
                nameRole = "Map Seller"

            elif role_name == 'pcasset':
                nameRole = "PC Asset Seller"
            elif role_name == 'questasset':
                nameRole = "Quest Asset Seller"

            elif role_name == 'pcmod':
                nameRole = "PC Mod Seller"
            elif role_name == 'questmod':
                nameRole = "Quest Mod Seller"
            
            elif role_name == 'trusted':
                nameRole = "Trusted Seller"
            
            else:
                return await ctx.send('An Error occured: \'Role name not valid\' ')


            role = get(ctx.guild.roles, name=nameRole)

            # Reply Code ==========================================================
            try:

                await member.send(
                    embed=discord.Embed(
                        description=(
                            f"Unfortunately, your application for {nameRole} in the Beat Saber Commissions Center has been declined" 
                            + (f" due to: \n```{reason}```\n" if reason else ".\n\n")
                            + "If you have any questions or believe this is a mistake, DM me to open a ticket!"
                        ),
                        color=discord.Colour.dark_orange(),
                    ).set_footer(text="This is an automated message.")
                )

            except discord.errors.Forbidden:
                await self.log(
                    guild=ctx.guild,
                    embed=discord.Embed(
                        title=f"{member} ({member.id})",
                        description=f"{member.mention}'s application for {role.mention} was declined by {ctx.author.mention}"
                        + (f" for: \n```{reason}```" if reason else ".")
                        + "\nAn error occured in sending confirmation to user.",
                        color=discord.Colour.dark_gold(),
                    ),
                )
                return await ctx.send('Error: User has not been notified as they do not have DM\'s open.') 

            await self.log(
                guild=ctx.guild,
                embed=discord.Embed(
                    title=f"{member} ({member.id})",
                    description=f"{member.mention}'s application for {role.mention} was declined by {ctx.author.mention}"
                    + (f" for: \n```{reason}```" if reason else "."),
                    color=discord.Colour.dark_orange(),
                ),
            )


    @commands.command(usage="<channel>")
    @checks.has_permissions(PermissionLevel.OWNER)
    async def setlog(self, ctx, channel: discord.TextChannel = None):
        """Sets up a log channel."""
        if channel == None:
            return await ctx.send_help(ctx.command)

        try:
            await channel.send(
                embed=discord.Embed(
                    description=(
                        "This channel has been set up to log role actions."
                    ),
                    color=self.bot.main_color,
                )
            )
        except discord.errors.Forbidden:
            await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description="I don't have enough permissions to write in that channel.",
                    color=discord.Color.red(),
                ).set_footer(text="Please fix the permissions.")
            )
        else:
            await self.db.find_one_and_update(
                {"_id": "logging"},
                {"$set": {str(ctx.guild.id): channel.id}},
                upsert=True,
            )
            await ctx.send(
                embed=discord.Embed(
                    title="Success",
                    description=f"{channel.mention} has been set up as log channel.",
                    color=self.bot.main_color,
                )
            )
    
    async def log(self, guild: discord.Guild, embed: discord.Embed):
        """Sends logs to the log channel."""
        channel = await self.db.find_one({"_id": "logging"})
        if channel == None:
            return
        if not str(guild.id) in channel:
            return
        channel = self.bot.get_channel(channel[str(guild.id)])
        if channel == None:
            return
        return await channel.send(embed=embed)

def setup(bot):
    bot.add_cog(roleResponse(bot))