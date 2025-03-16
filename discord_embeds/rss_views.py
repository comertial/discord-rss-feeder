import discord
from discord.ui import Select, View, Modal, TextInput, Button

from DatabaseManager import db_manager


# Create a class to handle the dropdowns and their interactions
class DropdownRssHandler(View):
    def __init__(self, ctx):
        super().__init__()
        self.rss_action = None
        self.rss_feeds = None
        self.guild = None  # Store the guild object
        self.ctx = ctx

        # Add the dropdowns to the view
        self.add_item(self.RssActionDropdown(self))
        self.add_item(self.RssSelector(self))

    # handle selected interactions
    async def handle_selections(self, interaction):
        # # Make sure to call create_channels_if_needed before processing selections
        # if self.guild:
        #     await self.create_channels_if_needed(self.guild)

        # Change enabled status of variable
        for rss_feed in self.rss_feeds:
            action = None
            if self.rss_action == "Enable":
                action = True
            elif self.rss_action == "Disable":
                action = False

            if action is not None:
                # Save changes
                data = {'enabled': action}
                # ToDo: use the primary key and the db_manager.update_rss_feed
                condition = f'(server_id = {self.ctx.message.guild.id} AND name = \'{rss_feed}\')'
                db_manager.update('RssFeed', data, condition)

        feeds = '\n\t'.join(self.rss_feeds)
        await interaction.response.send_message(f'{self.rss_action} RSS Feeds:\n\t{feeds}', silent=True)
        await self.terminate_ui(interaction)

    # Method to terminate the UI
    async def terminate_ui(self, interaction):
        self.stop()  # Stop the view from listening for interactions
        await interaction.message.delete()  # Delete the original message with the UI

    # Inner class for the first dropdown
    class RssActionDropdown(Select):
        def __init__(self, parent_view):
            self.parent_view = parent_view
            options = [
                discord.SelectOption(label="Enable", description="Enable RSS Feed"),
                discord.SelectOption(label="Disable", description="Disable RSS Feed"),
            ]
            super().__init__(placeholder="Choose an action", min_values=1, max_values=1,
                             options=options)

        async def callback(self, interaction: discord.Interaction):
            self.parent_view.rss_action = self.values[0]
            if self.parent_view.rss_action and self.parent_view.rss_feeds:
                await self.parent_view.handle_selections(interaction)
            else:
                await interaction.response.send_message(
                    f'Action selected {self.parent_view.rss_action}',
                    ephemeral=True,
                    silent=True)

    # Inner class for the second dropdown
    class RssSelector(Select):
        def __init__(self, parent_view):
            self.parent_view = parent_view

            options = []
            rss_channels = db_manager.get_rss_feeds(self.parent_view.ctx.message.guild.id)
            for config in rss_channels:
                feed_server_id = config["server_id"]
                feed_name = config["name"]
                feed_url = config["url"]
                channel_id = config["channel_id"]
                enabled = config["enabled"]
                # if self.parent_view.ctx.message.guild.id != feed_server_id:
                #     continue
                options.append(discord.SelectOption(label=feed_name,
                                                    description=f'{feed_url[:100]} - {"Enabled" if enabled else "Disabled"}'))

            super().__init__(placeholder="Select RSS Feeds", min_values=1, max_values=len(options),
                             options=options)

        async def callback(self, interaction: discord.Interaction):
            self.parent_view.rss_feeds = self.values
            if self.parent_view.rss_action and self.parent_view.rss_feeds:
                await self.parent_view.handle_selections(interaction)
            else:
                feeds = '\n\t'.join(self.parent_view.rss_feeds)
                await interaction.response.send_message(
                    f'RSS Feeds Selected:\n\t{feeds}',
                    ephemeral=True,
                    silent=True)


class AddRssFeed(Modal, title='Add RSS Feed'):
    def __init__(self):
        super().__init__()

        self.name = TextInput(label='Name', placeholder='Enter the RSS name')
        self.url = TextInput(label='URL', placeholder='Enter the RSS URL')
        self.channel = TextInput(label='Channel', placeholder='Enter a channel name for RSS')
        self.enabled = TextInput(label='Enabled', placeholder='Enter Yes or No')

        # Add components to the modal
        self.add_item(self.name)
        self.add_item(self.url)
        self.add_item(self.channel)
        self.add_item(self.enabled)

    async def on_submit(self, interaction: discord.Interaction):
        enabled_bool = str(self.enabled).lower() == 'yes'
        server_id = interaction.guild.id
        guild = interaction.guild
        channel_name = str(self.channel)

        category_name = 'RSS FEEDS'
        category = discord.utils.get(interaction.guild.categories, name=category_name)
        if category is None:
            try:
                category = await interaction.guild.create_category(name=category_name)
                print(f"Created category: {category_name}")
            except Exception as e:
                print(f'Error creating category \'{category_name}\' in server \'{interaction.guild.name}\': {e}')

        channel = discord.utils.get(interaction.guild.text_channels, name=channel_name)

        create_channel = False
        if channel is None:
            channel = await interaction.guild.create_text_channel(name=channel_name, category=category)
            create_channel = True

        feed = {
            'server_id': int(server_id),
            'name': str(self.name),
            'url': str(self.url),
            'channel_name': channel_name,
            'channel_id': int(channel.id),
            'enabled': enabled_bool
        }

        try:
            db_manager.add_rss_feed(**feed)
            await interaction.response.send_message(
                f'RSS Feed added in **{interaction.guild.name}**!\n'
                f'Name: {self.name}\n'
                f'URL: {self.url}\n'
                f'Channel: {channel_name}\n'
                f'Enabled: {enabled_bool}',
                silent=True
            )
        except Exception as error:
            if str(error).startswith('UNIQUE constraint failed'):
                await interaction.response.send_message(f'Feed Source already exists for this server', silent=True)
                if create_channel:
                    await channel.delete()


class AddRssFeedView(View):
    def __init__(self):
        super().__init__()
        # Create and add the button manually
        self.add_rss_button = Button(label="Add RSS", style=discord.ButtonStyle.primary)
        self.add_rss_button.callback = self.open_form_button
        self.add_item(self.add_rss_button)

    async def open_form_button(self, interaction: discord.Interaction):
        await interaction.response.send_modal(AddRssFeed())
        await self.terminate_ui(interaction)

    # Method to terminate the UI
    async def terminate_ui(self, interaction):
        self.stop()  # Stop the view from listening for interactions
        await interaction.message.delete()  # Delete the original message with the UI


class UpdateRssFeedView(View):
    def __init__(self, feeds):
        super().__init__()
        self.feeds = feeds

        # Create and add select menu manually
        self.feed_select = Select(
            placeholder="Select RSS feed to update",
            min_values=1,
            max_values=1,
            options=[discord.SelectOption(
                label=feed['name'],
                value=feed['url'],
                description=f'{feed["url"][:100]} - {"Enabled" if feed["enabled"] else "Disabled"}')
                for feed in feeds]
        )
        self.feed_select.callback = self.on_feed_select
        self.add_item(self.feed_select)

    async def on_feed_select(self, interaction: discord.Interaction):
        server_id = interaction.guild.id
        selected_feed = self.feed_select.values[0]
        await interaction.response.send_modal(UpdateRssFeed(selected_feed, server_id))
        await self.terminate_ui(interaction)

    # Method to terminate the UI
    async def terminate_ui(self, interaction):
        self.stop()  # Stop the view from listening for interactions
        await interaction.message.delete()  # Delete the original message with the UI


class UpdateRssFeed(Modal, title='Update RSS Feed'):
    def __init__(self, feed_url, feed_server_id):
        super().__init__()
        self.old_channel_id = db_manager.select(
            tables=['RssFeed'],
            columns=['channel_id'],
            where_condition=f'url = \'{feed_url}\' AND server_id = {feed_server_id}')
        self.old_channel_id = self.old_channel_id[0]['channel_id']
        self.feed_url = feed_url
        self.feed_server_id = feed_server_id

        self.name = TextInput(label='New Name', placeholder='Enter the new RSS name', required=False)
        self.url = TextInput(label='New URL', placeholder='Enter the new RSS URL', required=False)
        self.channel_name = TextInput(label='New Channel', placeholder='Enter a new channel name', required=False)
        self.enabled = TextInput(label='Enabled', placeholder='Enter Yes or No', required=False)

        # Add components to the modal
        self.add_item(self.name)
        self.add_item(self.url)
        self.add_item(self.channel_name)
        self.add_item(self.enabled)

    async def on_submit(self, interaction: discord.Interaction):
        category_name = 'RSS FEEDS'
        category = discord.utils.get(interaction.guild.categories, name=category_name)

        if category is None:
            try:
                category = await interaction.guild.create_category(name=category_name)
                print(f"Created category: {category_name}")
            except Exception as e:
                print(f'Error creating category \'{category_name}\' in server \'{interaction.guild.name}\': {e}')

        # Fetch or create the appropriate channel
        channel = None
        if self.channel_name.value:  # Ensure this checks the value, not the TextInput object itself
            channel = discord.utils.get(interaction.guild.text_channels, name=str(self.channel_name.value))
        else:
            channel = await interaction.guild.fetch_channel(self.old_channel_id)

        if channel is None and self.channel_name.value:
            channel = await interaction.guild.create_text_channel(name=str(self.channel_name.value), category=category)

        # Collect updates
        updates = {}
        if self.name.value:
            updates['name'] = str(self.name.value)
        if self.url.value:
            updates['url'] = str(self.url.value)
        if self.channel_name.value:
            updates['channel_name'] = str(self.channel_name.value)
            updates['channel_id'] = int(channel.id)
        if self.enabled.value:
            updates['enabled'] = self.enabled.value.lower() == 'yes'

        # Update the RSS feed in your database
        db_manager.update_rss_feed(server_id=self.feed_server_id, url=self.feed_url, data=updates)

        if 'channel_id' in updates:
            channel = await interaction.guild.fetch_channel(updates['channel_id'])
            updates['channel_name'] = channel.name
            del updates['channel_id']

        await interaction.response.send_message(
            f'RSS Feed updated!\n\t' +
            '\n\t'.join(f'{k}: {v}' for k, v in updates.items()),
            silent=True
        )

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await interaction.response.send_message(f'Oops! Something went wrong: {error}', ephemeral=True, silent=True)


class DeleteRssFeedView(View):
    def __init__(self, feeds):
        super().__init__()
        self.feeds = feeds

        # Create and add select menu manually
        self.feed_select = Select(
            placeholder="Select RSS feed to delete",
            min_values=1,
            max_values=len(feeds),
            options=[discord.SelectOption(
                label=feed['name'],
                value=feed['url'],
                description=f'{feed["url"][:100]} - {"Enabled" if feed["enabled"] else "Disabled"}')
                for feed in feeds]
        )
        self.feed_select.callback = self.on_feed_select
        self.add_item(self.feed_select)

    async def on_feed_select(self, interaction: discord.Interaction):
        server_id = interaction.guild.id
        urls = self.feed_select.values

        urls_str = "', '".join(urls)
        condition = f'(server_id = {server_id} AND url IN (\'{urls_str}\'))'
        db_manager.delete('RssFeed', condition)

        deleted_names = [feed['name'] for feed in self.feeds if feed['url'] in urls]
        await interaction.response.send_message(f'RSS Feeds deleted!\n\t' +
                                                '\n\t'.join(deleted_names), silent=True)
        await self.terminate_ui(interaction)

    # Method to terminate the UI
    async def terminate_ui(self, interaction):
        self.stop()  # Stop the view from listening for interactions
        await interaction.message.delete()  # Delete the original message with the UI
