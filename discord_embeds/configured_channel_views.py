import discord
from discord.ui import Select, View, Button

from DatabaseManager import db_manager


class UpdateConfiguredChannel(View):
    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx
        self.server = ctx.guild
        self.all_channels = ctx.guild.text_channels
        self.current_page = 0
        self.items_per_page = 10  # Max 25 items in a select menu, but we'll use 24 to make space for pagination indication
        self.total_pages = (len(self.all_channels) + self.items_per_page - 1) // self.items_per_page  # Ceiling division

        # Initialize the select menu with the first page
        self.select = Select(placeholder=f"Choose a channel... (Page {self.current_page + 1}/{self.total_pages})")
        self.select.callback = self.select_callback
        self.add_item(self.select)

        # Add navigation buttons
        self.prev_button = Button(label="Previous", style=discord.ButtonStyle.primary)
        self.prev_button.callback = self.prev_page
        self.add_item(self.prev_button)

        self.next_button = Button(label="Next", style=discord.ButtonStyle.primary)
        self.next_button.callback = self.next_page
        self.add_item(self.next_button)

        # Update the UI to display the first page
        self.update_select_options()

    def update_select_options(self):
        # Calculate the start and end indices for the current page
        start_idx = self.current_page * self.items_per_page
        end_idx = min(start_idx + self.items_per_page, len(self.all_channels))
        channels_to_display = self.all_channels[start_idx:end_idx]

        # Update select menu placeholder to show current page
        self.select.placeholder = f"Choose a channel... (Page {self.current_page + 1}/{self.total_pages})"

        # Clear and update the options
        self.select.options = [
            discord.SelectOption(
                label=channel.name,
                value=str(channel.id)
            )
            for channel in channels_to_display
        ]

        # Disable/enable navigation buttons as needed
        self.prev_button.disabled = (self.current_page == 0)
        self.next_button.disabled = (self.current_page == self.total_pages - 1)

    async def prev_page(self, interaction: discord.Interaction):
        if self.current_page > 0:
            self.current_page -= 1
            self.update_select_options()
        await interaction.response.edit_message(view=self)

    async def next_page(self, interaction: discord.Interaction):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.update_select_options()
        await interaction.response.edit_message(view=self)

    async def select_callback(self, interaction: discord.Interaction):
        # Handle the channel selection
        selected_channel_id = int(interaction.data['values'][0])

        # Do something with the selected channel (e.g., save it as the configured channel)
        data = {
            'server_id': self.server.id,
            'channel_id': selected_channel_id
        }
        selected_channel_name = self.server.get_channel(selected_channel_id).name
        db_manager.update('MainChannel', data, f'(server_id = {self.server.id})')
        await interaction.response.send_message(f"Channel `{selected_channel_name}` has been selected.", ephemeral=True)
        await self.terminate_ui(interaction)

    # Method to terminate the UI
    async def terminate_ui(self, interaction):
        self.stop()  # Stop the view from listening for interactions
        await interaction.message.delete()  # Delete the original message with the UI
