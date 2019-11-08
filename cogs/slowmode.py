import discord
import os
import asyncio
import typing

from discord.ext import commands
from discord.ext.commands import BucketType


class SlowMode(commands.Cog):
    SAKTEMODUS = 'Kanalen er nå i saktemodus på '

    def __init__(self, bot):
        self.bot = bot

    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    @commands.cooldown(1, 5, BucketType.guild)
    @commands.command(name="slowmode")
    async def _slowmode(self,
                        ctx,
                        enable: typing.Union[int, str]="on",
                        seconds: int=30):

        if isinstance(enable, int):
            seconds = enable
            enable = 'on'

        if seconds == 0:
            enable = 'off'

        if seconds < 0 or seconds > 21600:
            await ctx.send("Max slowmode is 6 hours(21600 sec).")
            return
        if enable.lower() == 'på':
            await ctx.channel.edit(slowmode_delay=seconds)
            if seconds == 1:
                await ctx.send(self.SAKTEMODUS + f'{seconds} second.')
            else:
                await ctx.send(self.SAKTEMODUS + f'{seconds} seconds.')
        if enable.lower() == 'av':
            await ctx.channel.edit(slowmode_delay=0)
            await ctx.send(f'Slowmode is off.')

    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    @commands.cooldown(1, 20, BucketType.guild)
    @commands.command(name="lockdown")
    async def _lockdown(self,
                        ctx,
                        enable: str="on"):
        if enable == "on":
            for channel in ctx.guild.text_channels:
                if ctx.guild.me.permissions_in(channel).manage_channels:
                    if channel.slowmode_delay == 0:
                        await channel.edit(slowmode_delay=120)
            await ctx.send(f"Locked")
        else:
            for channel in ctx.guild.text_channels:
                if ctx.guild.me.permissions_in(channel).manage_messages:
                    if channel.slowmode_delay == 120:
                        await channel.edit(slowmode_delay=0)
            await ctx.send(f"Unlocked")


def setup(bot):
    bot.add_cog(SlowMode(bot))
