import discord
from discord.ui import Select, View

from DatabaseManager import db_manager

class UpdateConfiguredChannel(View):
    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx
        self.server = ctx.guild
        # ToDo: Handle more that 25 channels with pagination
        channels = ctx.guild.text_channels[:25]

        # Create a Select menu with options populated from the server's text channels
        select = Select(
            placeholder="Choose a channel...",
            options=[
                discord.SelectOption(
                    label=channel.name,
                    value=channel.id
                )
                for channel in channels
            ]
        )

        # Add the Select menu to the view
        select.callback = self.select_callback
        self.add_item(select)

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
        await interaction.response.send_message(f"Channel `{selected_channel_name}` has been selected.", silent=True)
        await self.terminate_ui(interaction)


    # Method to terminate the UI
    async def terminate_ui(self, interaction):
        self.stop()  # Stop the view from listening for interactions
        await interaction.message.delete()  # Delete the original message with the UI