import discord
import re
import asyncio
import typing
import os
import codecs
import json
from datetime import datetime
from cogs.utils.rulemanager import RuleManager
from discord.ext import commands


class Rules(commands.Cog):

    DATA_PATH = 'data/rules/'
#    EMOJI_PATH = DATA_PATH + 'react_emoji.json'
    REACT_MSGS = DATA_PATH + 'react_msg_id.json'
    SERVERS_PATH = DATA_PATH + 'servers/'

    def __init__(self, bot):
        if not os.path.exists(self.DATA_PATH):
            os.makedirs(self.DATA_PATH)

        if not os.path.isfile(self.REACT_MSGS):
            with codecs.open(self.REACT_MSGS, "w+", encoding='utf8') as f:
                # "0"-id because empty lists makes json angry
                json.dump([111111111111111111], f, indent=4)

        with codecs.open(self.REACT_MSGS, "r", encoding='utf8') as f:
            self._react_messages = json.load(f)

        self.bot = bot
        self.emoji = '\N{INCOMING ENVELOPE}'

    @commands.guild_only()
    @commands.command(name="rule")
    async def rules(self, ctx,
                    lov: typing.Union[int, str]=None, *, num: str=None):
        """
        Show the rules
        """

        rules = RuleManager(ctx.guild.id, self.SERVERS_PATH)

        if isinstance(lov, int):
            if num is None:
                num = str(lov)
            else:
                num = str(lov) + " " + num
            lov = rules.get_settings("default_rule")

        rule_text, date = rules.get_rule_text(lov)

        if rule_text is None:
            await ctx.send('**List of rules:**\n' +
                           f'{rules.get_rules_formatted()}')
            return

        if rule_text == "":
            await ctx.send("This rule is empty.")
            return

        # Get only specified rules
        if num is not None:
            await ctx.message.delete()
            partial_rules = ""

            no_dupes = remove_duplicates(num.split())

            for rule in no_dupes:
                ruleregex = r"(§ *" + re.escape(rule) + r"[a-z]?: [\S ]*)"
                m = re.search(ruleregex, rule_text)
                if m is not None:
                    partial_rules += m.groups()[0] + "\n"

            if partial_rules == "":
                await ctx.send(f'Didn\'t find that rule')
            else:
                if lov != rules.get_settings("default_rule"):
                    partial_rules = f'**In the rules for {lov}:**\n' \
                        + partial_rules
                await ctx.send(partial_rules)
        else:
            embed = await self._create_embed(rule_text, date)
            await ctx.send(embed=embed)

    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    @commands.group(name="set_rule")
    async def _rule_settings(self, ctx):
        """
        Settings for rules
        """
        if ctx.invoked_subcommand is None:
            await ctx.invoke(self.bot.get_command('help'),
                             ctx.command.qualified_name)

    @_rule_settings.command(name="new")
    async def newrules(self, ctx, lov, *, newrule: str=None):
        """
        Legger til et nytt sett med regler i lovherket.
        """
        rules = RuleManager(ctx.guild.id, self.SERVERS_PATH)
        added = rules.add_rule(lov, newrule)

        if not added:
            await ctx.send("There is no rules with that name.")
        else:
            await ctx.send("Rules stored")

    @_rule_settings.command(name="plaintext")
    async def plaintext(self, ctx, lov):
        """
        Sends the rules so they can be presented with formatting
        """
        rules = RuleManager(ctx.guild.id, self.SERVERS_PATH)
        rule_text, date = rules.get_rule_text(lov)

        if rule_text is None:
            await ctx.send("Sjekk at du skrev riktig.")
        else:
            await ctx.send("```\n" + rule_text + "\n```")

    @_rule_settings.command(name="remove")
    async def removerules(self, ctx, lov):
        """
        Removes rules
        """
        rules = RuleManager(ctx.guild.id, self.SERVERS_PATH)
        await self._remove_reactions(ctx, lov)
        removed = rules.remove_rule(lov)

        if removed:
            await ctx.send("Rule removed")
        else:
            await ctx.send("The rule you typed doesnt exist")

    @_rule_settings.command(name="update")
    async def updaterules(self, ctx, lov, *, newrule):
        """
        Update rules.
        """
        rules = RuleManager(ctx.guild.id, self.SERVERS_PATH)
        edited = rules.edit_rule(lov, newrule)
        if edited:
            await ctx.send("Oppdaterer meldinger")
            await self._update_messages(ctx, lov)
            await ctx.send("Regler oppdatert")
        else:
            await ctx.send("Sjekk at du skrev riktig.")

    @_rule_settings.command(name="default")
    async def set_default_rule(self, ctx, lov):
        """
        Sets default
        """
        rules = RuleManager(ctx.guild.id, self.SERVERS_PATH)
        rule_text, date = rules.get_rule_text(lov)

        if rule_text is None:
            await ctx.send(f'This rule does not exist.\n\n' +
                            '**Rules:**\n' +
                            f'{rules.get_rules_formatted()}')
            return

        rules.change_setting("default_rule", lov.lower())
        await ctx.send(f'{lov} is now the servers default rule')

    """
    Auto rules
    """

    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    @commands.group(name="autoset")
    async def _auto_settings(self, ctx):
        """
        Settings for automatic rule-updates
        """
        if ctx.invoked_subcommand is None:
            await ctx.invoke(self.bot.get_command('help'),
                             ctx.command.qualified_name)

    @_auto_settings.command(name="post")
    async def postauto(self, ctx, lov):
        """
        Sends a message that auto-updates when rules updates
        """
        rules = RuleManager(ctx.guild.id, self.SERVERS_PATH)
        rule_text, date = rules.get_rule_text(lov)

        if rule_text is None:
            await ctx.send('Check that the rule exist.\n' +
                           '**Rules:**\n' +
                           f'{rules.get_rules_formatted()}')
            return

        if rule_text == "":
            await ctx.send("This rule is empty.")
            return

        embed = await self._create_embed(rule_text, date)
        msg = await ctx.send(embed=embed)
        added = rules.add_link_setting('auto_update',
                                       lov,
                                       f'{self._format_message_link(msg)}')

        conf_msg = await ctx.send("Message is now updating")
        await asyncio.sleep(5)
        await conf_msg.delete()

    @_auto_settings.command(name="add")
    async def autorules(self, ctx, lov, link):
        """
        Makes an old message automatically update
        """
        msg = await self._get_linked_message(ctx, link)
        if msg is None:
            await ctx.send("Didnt find the message")
            return
        if msg.author != self.bot.user:
            await ctx.send("Ensure the message is one of this bots messages")
            return

        rules = RuleManager(ctx.guild.id, self.SERVERS_PATH)
        added = rules.add_link_setting('auto_update',
                                       lov,
                                       f'{self._format_message_link(msg)}')

        if added == -1:
            await ctx.send("Message already set to update")
        elif added:
            await ctx.send("Message set to update")
        else:
            await ctx.send("The rule doesnt exist")

        await ctx.send("Updating messages")
        await self._update_messages(ctx, lov)
        await ctx.send("Updated")

    @_auto_settings.command(name="list")
    async def _auto_list(self, ctx):
        """
        Lists auto-updating messages
        """
        rules = RuleManager(ctx.guild.id, self.SERVERS_PATH)
        auto_update_messages = rules.get_settings('auto_update')

        list_message = '**Messages that are auto-updating:**\n'

        if len(auto_update_messages) == 0:
            await ctx.send("No message is set to auto-update")
            return

        for message in auto_update_messages:
            list_message += f'{message["name"]}: {message["link"]}\n'

        await ctx.send(list_message)

    @_auto_settings.command(name="remove")
    async def remove_auto(self, ctx, link):
        """
        Removes an auto-updating message from the list
        """
        rules = RuleManager(ctx.guild.id, self.SERVERS_PATH)
        removed = rules.remove_link_setting("auto_update", "link", link)
        if removed:
            await ctx.send("auto-update removed")
        else:
            await ctx.send("Check the link with §auto list")

    @_auto_settings.command(name="fix")
    async def fixauto(self, ctx):
        """
        Runs a manual update on auto-updating messagges
        """
        await ctx.send("Updating messages")
        await self._update_messages(ctx)
        await ctx.send("Updated")

    """
    React rules
    """
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    @commands.group(name="reactset")
    async def _react_settings(self, ctx):
        """
        Settings for react-rules.
        """
        if ctx.invoked_subcommand is None:
            await ctx.invoke(self.bot.get_command('help'),
                             ctx.command.qualified_name)

    @_react_settings.command(name="update")
    async def edit_alternate(self, ctx, lov, *, newrule):
        """
        Updates react-rules
        """
        rules = RuleManager(ctx.guild.id, self.SERVERS_PATH)
        edited = rules.edit_rule(lov, newrule, alternate=True)
        if edited:
            await ctx.send("Alternate rules updated")
        else:
            await ctx.send("Ensure you typed the correct rule.")

    @_react_settings.command(name="remove")
    async def remove_alternate(self, ctx, lov):
        """
        Removes rect-rules
        """
        rules = RuleManager(ctx.guild.id, self.SERVERS_PATH)
        removed = rules.remove_rule(lov, alternate=True)
        if removed:
            await ctx.send("Alternate rules removed")
        else:
            await ctx.send("The rule doesnt exist")

    @_react_settings.command(name="show")
    async def show_alternate(self, ctx, lov: str=None):
        """
        Shows react-rules
        """
        rules = RuleManager(ctx.guild.id, self.SERVERS_PATH)
        rule_text, date = rules.get_rule_text(lov, alternate=True)
        if rule_text is not None:
            await ctx.send("```\n" + rule_text + "\n```")
        else:
            await ctx.send('**Lists react-rules:**\n' +
                           f'{rules.get_rules_formatted(alternate=True)}')

    @_react_settings.command(name="liste")
    async def _react_list(self, ctx):
        """
        Lists auto-updating react-rules
        """
        rules = RuleManager(ctx.guild.id, self.SERVERS_PATH)
        react_messages = rules.get_settings('react_rules')

        list_message = '**Messages with react-rules:**\n'

        if len(react_messages) == 0:
            await ctx.send("No meassage is setup with react-rules")
            return

        for message in react_messages:
            list_message += f'{message["name"]}: {message["link"]}\n'

        await ctx.send(list_message)

    @_react_settings.command(name="link")
    async def link_alternate(self, ctx, lov, link):
        """
        Converts an old message to updates with alternate rules
        """
        msg = await self._get_linked_message(ctx, link)
        if msg is None:
            await ctx.send("Didnt find the message")
            return

        rules = RuleManager(ctx.guild.id, self.SERVERS_PATH)
        added = rules.add_link_setting('react_rules',
                                       lov,
                                       f'{self._format_message_link(msg)}')

        self._react_messages.append(msg.id)
        with codecs.open(self.REACT_MSGS, "w+", encoding='utf8') as f:
            json.dump(self._react_messages, f, indent=4)

        if added == -1:
            await ctx.send("Message already set up for reactions")
        elif added:
            try:
                await msg.clear_reactions()
                await asyncio.sleep(1)
                await msg.add_reaction(self.emoji)
                await ctx.send("react-rules added")
            except:
                await ctx.send("I dont have permission to react")
        else:
            await ctx.send("Rule doesnt exist")

    @_react_settings.command(name="unlink")
    async def unlink_alternate(self, ctx, message_link):
        """
        Removes a ract rule for react-rules
        """

        rules = RuleManager(ctx.guild.id, self.SERVERS_PATH)

        msg = await self._get_linked_message(ctx, message_link)
        if msg is None:
            await ctx.send("Ensure the link is valid")
            return
        link = self._format_message_link(msg)

        await self._remove_reactions(ctx, link)
        removed = rules.remove_link_setting("react_rules", "link", link)
        if removed:
            await ctx.send("React-rules removed")
        else:
            await ctx.send("Message wasnt set up as  react-rule")

    """
    Events
    """
    # Call rules without using commands
    @commands.Cog.listener()
    async def on_message(self, message):

        if message.author.id == self.bot.user.id:
            return

        if not isinstance(message.channel, discord.TextChannel):
            return

        content = message.content

        if content is '' or content[0] is not "§":  # hardcoded atm
            return

        split = content.split('§')
        num = split[1]

        if num is '':
            return

        # crap way to avoid running when a command runs
        try:
            int(num.split()[0])
        except:
            return

        rules = RuleManager(message.guild.id, self.SERVERS_PATH)

        lov = rules.get_settings("default_rule")
        rule_text, date = rules.get_rule_text(lov)

        context = message.channel

        if rule_text is None:
            await context.send('**You need to set up a default rule first\n' +
                               'Rules:**\n' +
                               f'{rules.get_rules_formatted()}')
            return

        if rule_text == "":
            await context.send("Denne regelen er helt tom.")
            return

        # Get only specified rules
        partial_rules = ""
        no_dupes = remove_duplicates(num.split())
        for rule in no_dupes:
            ruleregex = r"(§ *" + re.escape(rule) + r"[a-z]?: [\S ]*)"
            m = re.search(ruleregex, rule_text)
            if m is not None:
                partial_rules += m.groups()[0] + "\n"

        if partial_rules is '':
            return
        await context.send(partial_rules)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        await self.react_action(payload, True)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        await self.react_action(payload, False)

    @commands.Cog.listener()
    async def on_raw_reaction_clear(self, payload):
        if payload.message_id not in self._react_messages:
            return
        channel = self.bot.get_channel(payload.channel_id)
        msg = await channel.fetch_message(payload.message_id)
        await asyncio.sleep(1)
        await msg.add_reaction(self.emoji)

    async def react_action(self, payload, added):

        if payload.guild_id is None:
            return

        if payload.message_id not in self._react_messages:
            return

        if str(payload.emoji) == self.emoji:
            if not added and payload.user_id == self.bot.user.id:
                channel = self.bot.get_channel(payload.channel_id)
                msg = await channel.fetch_message(payload.message_id)
                await msg.add_reaction(self.emoji)

            if added and payload.user_id != self.bot.user.id:
                channel = self.bot.get_channel(payload.channel_id)
                msg = await channel.fetch_message(payload.message_id)
                user = self.bot.get_user(payload.user_id)
                try:
                    await msg.remove_reaction(self.emoji, user)
                except:
                    await channel.send("Tell a mod to fix my perms" +
                                       f"{user.mention}")
                await self._dm_rules(user, msg)
        else:
            if added and payload.user_id != self.bot.user.id:
                channel = self.bot.get_channel(payload.channel_id)
                msg = await channel.fetch_message(payload.message_id)
                await msg.clear_reactions()

        if str(payload.emoji) == self.emoji:
            rules = RuleManager

    """
    Non commands functions
    """

    def _format_message_link(sef, msg):
        message_link = f'https://discordapp.com/channels/' \
            + f'{msg.guild.id}/{msg.channel.id}/{msg.id}'
        return message_link

    async def _get_linked_message(self, ctx, message_link):
        try:
            message_split = message_link.split("/")
            message_id = int(message_split[-1])
            channel_id = int(message_split[-2])
            guild_id = int(message_split[-3])
        except:
            return None

        if ctx.guild.id != int(guild_id):
            return None

        channel = ctx.guild.get_channel(channel_id)
        if channel is None:
            return None

        try:
            msg = await channel.fetch_message(message_id)
            return msg
        except:
            return None

    async def _remove_reactions(self, ctx, to_match):
        rules = RuleManager(ctx.guild.id, self.SERVERS_PATH)
        react_rules = rules.get_settings("react_rules")
        for rule in react_rules:
            if rule["name"] == to_match or rule["link"] == to_match:
                msg = await self._get_linked_message(ctx, rule["link"])
                if msg is None:
                    await ctx.send('Får ikke fjernet reaksjonen fra ' +
                                   f'følgende melding:\n{message["link"]}\n' +
                                   'Sjekk om den er tilgjengelig for botten' +
                                   ' eller slett reaksjonen manuelt')
                    continue

                await msg.remove_reaction(self.emoji, self.bot.user)

                self._react_messages.remove(msg.id)
                with codecs.open(self.REACT_MSGS, "w+", encoding='utf8') as f:
                    json.dump(self._react_messages, f, indent=4)

                await asyncio.sleep(2)

    async def _dm_rules(self, user, msg):

        rules = RuleManager(msg.guild.id, self.SERVERS_PATH)
        react_rules = rules.get_settings("react_rules")
        msg_link = self._format_message_link(msg)
        rule_name = None
        for rule in react_rules:
            if rule["link"] == msg_link:
                rule_name = rule["name"]

        if rule_name is None:
            return

        rule_text, date = rules.get_rule_text(rule_name, alternate=True)
        try:
            embed = await self._create_embed(rule_text, date)
            await user.send(embed=embed)
        except discord.Forbidden:
            await msg.channel.send(f"I can't send you messages {user.mention}")

    async def _update_messages(self, ctx, name=None):
        rules = RuleManager(ctx.guild.id, self.SERVERS_PATH)
        auto_update_messages = rules.get_settings('auto_update')

        for message in auto_update_messages:
            if message["name"] == name or name is None:
                msg = await self._get_linked_message(ctx, message["link"])
                if msg is None:
                    await ctx.send('Klarer ikke finne følgende melding:\n' +
                                   f'{message["link"]}\nSjekk om den finnes,' +
                                   ' hvis ikke fjern den med `§auto fjern`')
                    continue

                updated_text, date = rules.get_rule_text(message["name"])
                if updated_text is None:
                    await ctx.send('Didnt find a rule with this name:\n' +
                                   f'{message["name"]}.')
                    continue

                await asyncio.sleep(2)
                embed = await self._create_embed(updated_text, date)
                await msg.edit(content=None, embed=embed)

    async def _create_embed(self, text, date):
        avatar = self.bot.user.avatar_url_as(format=None,
                                             static_format='png',
                                             size=1024)

        embed = discord.Embed(color=0xD9C04D)
        embed.set_author(name=self.bot.user.name, icon_url=avatar)
        embed.description = text
        embed.set_footer(text='Sist oppdatert')
        embed.timestamp = datetime.strptime(date, '%Y-%m-%d %H:%M:%S.%f')

        return embed


def remove_duplicates(dupe_list):
    seen = {}
    result = []
    for item in dupe_list:
        if item in seen:
            continue
        seen[item] = 1
        result.append(item)
    return result


def setup(bot):
    bot.add_cog(Rules(bot))
