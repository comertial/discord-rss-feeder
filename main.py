import asyncio
import traceback
from datetime import datetime, timedelta

import dateutil.parser as dt_parser
import feedparser
from dateutil.relativedelta import relativedelta
from discord.ext import commands, tasks
from discord.ui import Button

from core.constants import MESSAGES, TOKEN
from core.helpers import (update_rss_feeds, is_valid_user, delete_old_history)
from discord_embeds.admin_role_views import *
from discord_embeds.configured_channel_views import *
from discord_embeds.rss_views import *

RSS_CHANNELS = update_rss_feeds()


def main():
    # Define bot intents (including message content)
    intents = discord.Intents.default()
    intents.message_content = True
    intents.reactions = True
    intents.members = True
    # intents.guilds = True
    # intents.guild_messages = True

    # Create a bot instance
    bot = commands.Bot(command_prefix="!", intents=intents)

    @bot.event
    async def on_ready():
        print(f'Bot connected as {bot.user}')

        await bot.change_presence(activity=discord.Game(name="Use !help"))

        for guild in bot.guilds:
            # Save the guild information in the database
            try:
                # add system channel
                db_manager.add_main_channel(guild.id, guild.system_channel.id)
            except Exception as error:
                # handle missing system_channel by adding a random channel
                if str(error).startswith("'NoneType' object has no attribute 'id'"):
                    data = {
                        'channel_id': guild.text_channels[0].id
                    }
                    db_manager.update_main_channel(guild.id, data)
                elif not str(error).startswith('UNIQUE constraint failed'):
                    print(traceback.format_exc())

            try:
                role = discord.utils.get(guild.roles, name='@everyone')
                db_manager.add_accepted_role(guild.id, role.id)
            except Exception as error:
                if not str(error).startswith('UNIQUE constraint failed'):
                    print(traceback.format_exc())

        # Check if the task is already running
        if not fetch_rss_feeds.is_running():
            fetch_rss_feeds.start()
        else:
            print("Task 'fetch_rss_feeds' is already running.")

        # Check if the task is already running
        if not check_connection.is_running():
            check_connection.start()
        else:
            print("Task 'check_connection' is already running.")

        # Start scheduler task
        await asyncio.create_task(delete_old_history())

    @bot.event
    async def on_disconnect():
        print('Bot has disconnected from Discord.')
        # handle restart with systemd service in case of disconnects
        # sys.exit(1)

    @bot.event
    async def on_connect():
        print('Bot has reconnected to Discord.')

    @bot.event
    async def on_guild_join(guild):
        # Send a welcome message to the server's default channel (usually the first text channel)
        if guild.system_channel is not None:
            await guild.system_channel.send(MESSAGES['WelcomeMessage'])

        # Save the guild information in the database
        try:
            # add system channel
            db_manager.add_main_channel(guild.id, guild.system_channel.id)
        except Exception as error:
            # handle missing system_channel by adding a random channel
            if str(error).startswith("'NoneType' object has no attribute 'id'"):
                data = {
                    'channel_id': guild.text_channels[0].id
                }
                db_manager.update_main_channel(guild.id, data)
            elif not str(error).startswith('UNIQUE constraint failed'):
                print(traceback.format_exc())

        try:
            role = discord.utils.get(guild.roles, name='@everyone')
            db_manager.add_accepted_role(guild.id, role.id)
        except Exception as error:
            if not str(error).startswith('UNIQUE constraint failed'):
                print(traceback.format_exc())

    @bot.command(name='ping', description='Ping Pong!')
    async def ping(ctx):
        # if await is_valid_user(ctx):
        print(f'Pong!')
        await ctx.send('Pong!', silent=True)

    @bot.command(name='greet', description='Greet the input user')
    async def greet(ctx, name: str = 'stranger'):
        # if await is_valid_user(ctx):
        await ctx.send(f'Hello, {name}!', silent=True)

    @bot.command(name='welcome', description='Output the welcome message')
    async def welcome(ctx):
        if await is_valid_user(ctx):
            await ctx.send(MESSAGES['WelcomeMessage'])

    @bot.command(name='server_name', description='Print the current server name')
    async def server_name(ctx):
        # if await is_valid_user(ctx):
        channel_id = db_manager.get_main_channel(ctx.guild.id)
        channel_id = channel_id[0]['channel_id']
        try:
            channel = await bot.fetch_channel(channel_id)
        except Exception:
            channel = channel_id
        if ctx.channel.id == channel_id:
            await ctx.send(f'The current server is `{ctx.message.guild.name}` with id `{ctx.message.guild.id}`.', silent=True)
        elif channel == channel_id:
            await ctx.send(f"Unknown Main Channel with id `{channel_id}`.\nUse `!update_main_channel` to configure a new main channel for the server.",
                           silent=True)
        else:
            await ctx.send(f"This command can only be used in the main configured channel `{channel.name}`.", silent=True)
            return

    @bot.command(name='get_main_channel', description='Get The configured channel')
    async def get_main_channel(ctx):
        # if await is_valid_user(ctx):
        channel_id = db_manager.get_main_channel(ctx.guild.id)
        channel_id = channel_id[0]['channel_id']
        try:
            channel = await bot.fetch_channel(channel_id)
        except Exception:
            channel = channel_id
        if channel == channel_id:
            await ctx.send(f"Unknown Main Channel with id `{channel_id}`.\nUse `!update_main_channel` to configure a new main channel for the server.",
                           silent=True)
            return
        await ctx.send(f'Main Channel configured is `{channel.name}`', silent=True)

    @bot.command(name='update_main_channel', description='Update The configured channel')
    async def update_main_channel(ctx):
        if await is_valid_user(ctx):
            await ctx.send(f'Update the configured channel', view=UpdateConfiguredChannel(ctx), silent=True)

    @bot.command(name='update_admin_role', description='Update the required admin role')
    async def update_admin_role(ctx):
        if await is_valid_user(ctx):
            await ctx.send(f'Update the admin role', view=UpdateAdminRole(ctx), silent=True)

    @bot.command(name='get_admin_role', description='Get The admin role')
    async def get_admin_role(ctx):
        role_id = db_manager.get_accepted_role(ctx.guild.id)
        role_id = role_id[0]['role_id']

        # Check if the role is the @everyone role
        if role_id == ctx.guild.id:
            role = ctx.guild.default_role
        else:
            role = ctx.guild.get_role(role_id)

        if role is None:
            await ctx.send(
                f"Unknown Admin Role with id `{role_id}`.\nUse `!update_admin_role` to configure a new admin role for the server.",
                silent=True
            )
            return

        await ctx.send(f'Admin Role configured is `{role.name}`', silent=True)

    @bot.command(name='add_rss_feed', description='Add a new RSS Feed')
    async def add_rss_feed(ctx):
        if await is_valid_user(ctx):
            await ctx.send("Click the button to add a new RSS Feed:", view=AddRssFeedView(), silent=True)

    @bot.command(name='update_rss_feed', description='Update an existing RSS Feed')
    async def update_rss_feed(ctx):
        if await is_valid_user(ctx):
            feeds = db_manager.get_rss_feeds(ctx.message.guild.id)
            if not feeds:
                await ctx.send(f"```markdown\n{MESSAGES['NoRssFound']}```", silent=True)
                return

            await ctx.send("Select the RSS feed you want to update:", view=UpdateRssFeedViewSelect(feeds), silent=True)

    @bot.command(name='delete_rss_feeds', description='Delete one or multiple RSS feeds')
    async def delete_rss_feeds(ctx):
        if await is_valid_user(ctx):
            # Fetch the list of RSS feeds for this server from your database
            # feeds = db_manager.select(
            #     tables=['RssFeed'],
            #     where_condition=f'server = \'{ctx.message.guild.name}\''
            # )
            feeds = db_manager.get_rss_feeds(ctx.message.guild.id)
            if not feeds:
                await ctx.send(f"```markdown\n{MESSAGES['NoRssFound']}```", silent=True)
                return

            await ctx.send("Select the RSS feeds you want to delete:", view=DeleteRssFeedViewSelect(feeds), silent=True)

    @bot.command(name='get_rss_feeds', description='Get Server RSS Feeds')
    async def get_rss_feeds(ctx):
        feeds = db_manager.get_rss_feeds(ctx.message.guild.id)
        if not feeds:
            await ctx.send(f"```markdown\n# {MESSAGES['NoRssFound']}```", silent=True)
            return

        async def find_channel_name(feed):
            feed['channel'] = await bot.fetch_channel(feed['channel_id'])
            if feed['channel'] is None:
                feed['channel'] = 'Unknown Channel'
            return feed

        feeds = await asyncio.gather(*map(find_channel_name, feeds))

        # Split feeds into pages with 5 feeds per page
        feeds_per_page = 5
        pages = [feeds[i:i + feeds_per_page] for i in range(0, len(feeds), feeds_per_page)]

        # Function to create embed for a specific page
        def create_embed(page_number):
            embed = discord.Embed(
                title=f"RSS Feeds for {ctx.message.guild.name} (Page {page_number + 1}/{len(pages)})",
                color=discord.Color.blue()
            )
            for feed in pages[page_number]:
                name = feed['name']
                url = feed['url']
                channel = feed['channel']
                enabled = 'Yes' if feed['enabled'] else 'No'
                embed.add_field(
                    name=f"__**{name}**__",
                    value=f"**URL:** {url}\n**Channel:** {channel}\n**Enabled:** {enabled}",
                    inline=False
                )
            return embed

        # Initialize first embed
        current_page = 0
        embed = create_embed(current_page)

        # Create buttons
        class PaginatorView(View):
            def __init__(self):
                super().__init__()
                self.current_page = 0
                # Initialize buttons with correct disabled states
                self.update_buttons()

            # Method to update the buttons' disabled states based on current page
            def update_buttons(self):
                # Disable 'Previous' if on the first page
                self.children[0].disabled = self.current_page == 0
                # Disable 'Next' if on the last page
                self.children[1].disabled = self.current_page == len(pages) - 1

            # Next button
            @discord.ui.button(label='Previous', style=discord.ButtonStyle.primary)
            async def previous_button(self, interaction: discord.Interaction, button: Button):
                if self.current_page > 0:
                    self.current_page -= 1
                    self.update_buttons()  # Update button states
                    await interaction.response.edit_message(embed=create_embed(self.current_page), view=self)

            # Previous button
            @discord.ui.button(label='Next', style=discord.ButtonStyle.primary)
            async def next_button(self, interaction: discord.Interaction, button: Button):
                if self.current_page < len(pages) - 1:
                    self.current_page += 1
                    self.update_buttons()  # Update button states
                    await interaction.response.edit_message(embed=create_embed(self.current_page), view=self)

        # Send the initial message with the first embed and the paginator view
        await ctx.send(embed=embed, view=PaginatorView(), silent=True)

    # Command to send the dropdown menu
    @bot.command(name='configure_rss_feeds', description='Enable or Disable existing RSS Feeds')
    async def configure_rss_feeds(ctx):
        if await is_valid_user(ctx):
            global RSS_CHANNELS
            RSS_CHANNELS = update_rss_feeds()
            if len(RSS_CHANNELS) == 0:
                await ctx.send(f"```markdown\n{MESSAGES['NoRssFound']}```", silent=True)
                return
            server_feeds = [feed['server_id'] for feed in RSS_CHANNELS if feed['server_id'] == ctx.message.guild.id]
            if len(server_feeds) == 0:
                await ctx.send(f"```markdown\n{MESSAGES['NoRssFound']}```", silent=True)
                return

            view = DropdownRssHandler(ctx)
            await ctx.send("Configuring RSS Feeds", view=view, silent=True)


    # Regular task that runs to check for connectivity issues
    @tasks.loop(seconds=60)
    async def check_connection():
        try:
            await bot.http.get_gateway()
        except Exception as e:
            # print("Connection lost, attempting to reconnect...")
            # await reconnect()
            print('Connection Lost...')
            print(traceback.format_exc())
            # sys.exit(1)

    @check_connection.before_loop
    async def before_check_connection():
        await bot.wait_until_ready()

        now = datetime.now()
        target_time = now.replace(second=0, microsecond=0)

        if now > target_time:
            target_time += timedelta(minutes=1)

        await asyncio.sleep((target_time - now).total_seconds())

    @tasks.loop(minutes=1)  # Set the interval to fetch the RSS feeds
    async def fetch_rss_feeds():
        print("Sending RSS Feeds...")

        global RSS_CHANNELS
        feed_history = db_manager.select(
            tables=['RssFeed', 'RssHistory'],
            columns=['RssFeed.server_id', 'RssFeed.url',
                     'max(RssHistory.timestamp) AS timestamp'],
            join_conditions=[
                'RssFeed.server_id = RssHistory.server_id AND RssFeed.url = RssHistory.url'],
            group_by=['RssFeed.server_id', 'RssFeed.url'],
            order_by=['RssHistory.timestamp DESC'])

        RSS_CHANNELS = update_rss_feeds()

        for rss_channel in RSS_CHANNELS:
            feed_name = rss_channel['name']
            server_id = rss_channel['server_id']
            feed_url = rss_channel['url']
            channel_name = rss_channel['channel_name']
            channel_id = rss_channel['channel_id']
            enabled = rss_channel['enabled']
            if not enabled:
                continue

            # Fetch and parse the RSS feed in a thread
            try:
                feed = await asyncio.to_thread(feedparser.parse, feed_url)
            except Exception as e:
                print(f"Failed to fetch RSS feeds:")
                print(traceback.format_exc())
                continue

            # Handle Discord guilds and channels
            category_name = 'RSS FEEDS'
            channels = []
            for guild in bot.guilds:
                if guild.id != server_id:
                    continue

                category = discord.utils.get(guild.categories, name=category_name)
                if category is None:
                    try:
                        category = await guild.create_category(name=category_name)
                        print(f"Created category: {category_name}")
                    except Exception as e:
                        print(f'Error creating category \'{category_name}\' in server \'{guild.name}\':')
                        print(traceback.format_exc())

                existing_channels = {channel.id for channel in guild.text_channels}
                if channel_id not in existing_channels:
                    try:
                        existing_channel = discord.utils.get(guild.text_channels, name=channel_name)
                        if existing_channel is not None:
                            channel_id = existing_channel.id
                            db_manager.update_rss_feed(server_id, feed_url, {'channel_id': channel_id})
                        else:
                            new_channel = await guild.create_text_channel(name=channel_name, category=category)
                            if new_channel is not None:
                                channel_id = new_channel.id
                                db_manager.update_rss_feed(server_id, feed_url, {'channel_id': channel_id})
                            print(f"Created channel: {channel_name} in category {category_name}")
                    except Exception as e:
                        print(f'Error creating channel \'{channel_name}\' in server \'{guild.name}\':')
                        print(traceback.format_exc())

                for ch in guild.text_channels:
                    if ch.id == channel_id:
                        channels.append(ch)

            if not channels:
                print(f"Channel for feed {feed_name} not found!")
                continue

            # Fetch the latest RSS entries from the feed
            rss_entry = [entries for entries in feed_history if
                         entries['server_id'] == server_id and entries['url'] == feed_url]
            if not rss_entry:
                rss_entry = {"server_id": server_id, "url": feed_url, "timestamp": datetime.now() - relativedelta(months=1)}
            else:
                rss_entry = rss_entry[0]
                rss_entry['timestamp'] = dt_parser.parse(rss_entry["timestamp"])

            if feed:
                feed.entries.reverse()
                # Check for new entries and send them to Discord channels
                for entry in feed.entries:
                    entry_time = datetime(*entry.published_parsed[:6])
                    if entry_time > rss_entry["timestamp"]:
                        rss_entry['timestamp'] = entry_time
                        rss_entry['title'] = entry.title
                        for channel in channels:
                            try:
                                await channel.send(f"**{feed.feed.title}**\n{entry.link}\n", silent=True)
                                db_manager.add_rss_history(**rss_entry)
                            except Exception as error:
                                if not str(error).startswith('UNIQUE constraint failed'):
                                    print(f"Error sending the RSS feed:")
                                    print(traceback.format_exc())
                                else:
                                    server_id = rss_entry['server_id']
                                    url = rss_entry['url']
                                    title = rss_entry['title']
                                    data = {
                                        'timestamp': rss_entry['timestamp']
                                    }
                                    db_manager.update_rss_history(server_id=server_id, url=url, title=title, data=data)
                                    # print(f'Error sending the RSS Feed \'{feed.feed.title}\' from url \'{entry.link}\' to channel \'{channel.name}\': {error}')

    @fetch_rss_feeds.before_loop
    async def before_fetch_rss_feeds():
        await bot.wait_until_ready()

        now = datetime.now()
        target_time = now.replace(second=0, microsecond=0)

        if now > target_time:
            target_time += timedelta(minutes=1)

        await asyncio.sleep((target_time - now).total_seconds())

    async def run_bot():
        while True:
            try:
                async with bot:
                    await bot.start(TOKEN)
            except Exception as e:
                print(f"Bot crashed:")
                print(traceback.format_exc())
                # sys.exit(1)
                # print("Reconnecting in 60 seconds...")
                # await asyncio.sleep(60)
    #
    # loop = asyncio.get_event_loop()
    # loop.create_task(run_bot())
    # loop.run_forever()

    # # Run the bot
    asyncio.run(run_bot())
    # bot.run(TOKEN)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(traceback.format_exc())
