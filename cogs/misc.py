import discord
import os
import asyncio
import time
import random
import platform

from discord.ext import commands


class Misc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.has_permissions(manage_messages=True)
    @commands.group(invoke_without_command=True)
    async def say(self, ctx, *, message: str=None):
        """
        Bot replies with the message
        """
        if message is not None:
            await ctx.send(message)

    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    @say.command()
    async def delete(self, ctx, *, message: str=None):
        """
        Bot replies with the message, and deletes the triggering message
        """
        if message is not None:
            try:
                await ctx.message.delete()
                await ctx.send(message)
            except discord.Forbidden:
                await ctx.send('I need permissions to delete messages')

    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    @commands.command()
    async def channel(self, ctx, *, channel: str=None):
        """
        Asks users to go to another channel.
        """
        if channel is None:
            return
        try:
            await ctx.message.delete()
            message = f'Looks like the topic in this discussion ' \
                + f'fits better in {channel}. We would appreciate if '\
                + f'you could move to  {channel} so ' \
                + f'the server is easier to read'
            await ctx.send(message)

        except discord.Forbidden:
            await ctx.send('I need permissions to delete messages')

    @commands.command(name='ping', hidden=True)
    async def _ping(self, ctx):
            start = time.perf_counter()
            message = await ctx.send('Ping...')
            end = time.perf_counter()
            duration = int((end - start) * 1000)
            edit = f'Pong!\nPing: {duration}ms' \
                + f' | websocket: {int(self.bot.latency * 1000)}ms'
            await message.edit(content=edit)

    @commands.command(name='uptime', hidden=True)
    async def _uptime(self, ctx):
        now = time.time()
        diff = int(now - self.bot.uptime)
        days, remainder = divmod(diff, 24 * 60 * 60)
        hours, remainder = divmod(remainder, 60 * 60)
        minutes, seconds = divmod(remainder, 60)
        await ctx.send(f'{days}d {hours}h {minutes}m {seconds}s')


    @commands.command()
    @commands.is_owner()
    async def servers(self, ctx):
        servers = f"{self.bot.user.name} is in:\n"
        for server in self.bot.guilds:
            servers += f"{server.name}\n"
        await ctx.send(servers)

    @commands.has_permissions(manage_messages=True)
    @commands.command()
    async def howto(self, ctx, *, channel: str=None):
        """
        How to use
        """
        avatar = self.bot.user.avatar_url_as(format=None,
                                             static_format='png',
                                             size=1024)
        howto = f'Coming soon'

        embed = discord.Embed(color=0xD9C04D)
        embed.set_author(name=self.bot.user.name, icon_url=avatar)
        embed.set_thumbnail(url=avatar)
        embed.add_field(name="How to use",
                        value=howto, inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    async def info(self, ctx, *, channel: str=None):
        """
        Info om LovherkBot
        """

        avatar = self.bot.user.avatar_url_as(format=None,
                                             static_format='png',
                                             size=1024)
        infotext = f'A bot helping to enforce rules.'

        embed = discord.Embed(color=0xD9C04D)
        embed.set_author(name=self.bot.user.name, icon_url=avatar)
        embed.set_thumbnail(url=avatar)
        embed.add_field(name="What",
                        value=infotext, inline=False)
        embed.add_field(name="How?",
                        value=f"**Python:** [{platform.python_version()}](https://www.python.org/)\n"
                              f"**Discord.py:** [{discord.__version__}](https://github.com/Rapptz/discord.py)",
                        inline=True)
        embed.add_field(name="Sourcecode",
                        value="[Github](https://github.com/Ev-1/lovherk).",
                        inline=True)
        embed.set_footer(icon_url="https://i.imgur.com/dE6JaeT.gif",
                         text="Made by Even :)")
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Misc(bot))
