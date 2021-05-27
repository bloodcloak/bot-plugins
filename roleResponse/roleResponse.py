import discord
from discord.ext import commands
from discord.utils import get

class roleResponse(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    async def giverole(self, ctx, member: discord.Member = None, rolename = None):
        valid_roles = ('map', 'pcmod', 'questmod', 'pcasset', 'questasset', 'trusted')

        if rolename not in valid_roles:
            await ctx.send('Invalid Role. Pick one from: ' + ', '.join(valid_roles))
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
                return await ctx.send('An Error occured when adding role: \'Role name not valid\' ')

            # Role Processing =============================================
            try:
                role = get(member.server.roles, name=nameRole)
                await self.bot.add_roles(member, role)
            except:
                return await ctx.send('An Error occured when adding role: \'Role Not Found\' \nPlease contact an Admin.')

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
                            color=discord.colour.green(),
                        ).set_footer(text="This is an automated message. If you have any questions, DM me to open a ticket!")
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
                            color=discord.colour.green(),
                        ).set_footer(text="This is an automated message. If you have any questions, DM me to open a ticket!")
                    )
            except discord.errors.Forbidden:
                return await ctx.send('Role has been applied. User has not been notified as they do not have DM\'s open.') 

    @commands.command()
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    async def denyrole(self, ctx, member: discord.Member = None, rolename = None, *, reason = None):
        valid_roles = ('map', 'pcmod', 'questmod', 'pcasset', 'questasset', 'trusted')

        if rolename not in valid_roles:
            await ctx.send('Invalid Role. Pick one from: ' + ', '.join(valid_roles))
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

            # Reply Code ==========================================================
            try:

                await member.send(
                    embed=discord.Embed(
                        description=(
                            f"Unfortunately, your application for {nameRole} in the Beat Saber Commissions Center has been declined" 
                            + (f" due to: {reason}\n\n" if reason else ".\n\n"),
                            "If you have any questions or believe this is a mistake, DM me to open a ticket!"
                        ),
                        color=discord.colour.green(),
                    ).set_footer(text="This is an automated message.")
                )

            except discord.errors.Forbidden:
                return await ctx.send('Error: User has not been notified as they do not have DM\'s open.') 

def setup(bot):
    bot.add_cog(roleResponse(bot))