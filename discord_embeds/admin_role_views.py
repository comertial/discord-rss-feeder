import discord
from discord.ui import Select, View

from DatabaseManager import db_manager

class UpdateAdminRole(View):
    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx
        self.server = ctx.guild
        # ToDo: Handle more that 25 roles
        self.roles = ctx.author.roles[:25]

        server_role = db_manager.get_accepted_role(ctx.guild.id)
        server_role = int(server_role[0]['role_id']) if len(server_role) == 1 else None
        self.server_role = server_role

        # Create a Select menu with options populated from the server's text channels
        select = Select(
            placeholder="Choose a role...",
            options=[
                discord.SelectOption(
                    label=role.name,
                    value=role.id
                )
                for role in self.roles
            ]
        )

        # Add the Select menu to the view
        select.callback = self.select_callback
        self.add_item(select)

    async def select_callback(self, interaction: discord.Interaction):
        # Handle the channel selection
        selected_role = int(interaction.data['values'][0])
        role = interaction.guild.get_role(selected_role)
        if role is None:
            await interaction.response.send_message(f"Role with id `{selected_role}` doesn't exist.", ephemeral=True, silent=True)
            return

        # Do something with the selected channel (e.g., save it as the configured channel)
        data = {
            'server_id': self.server.id,
            'role_id': selected_role
        }
        db_manager.update('AcceptedRole', data, f'(server_id = {self.server.id})')

        await interaction.response.send_message(f"Role `{role.name}` has been selected.", silent=True)
        await self.terminate_ui(interaction)


    # Method to terminate the UI
    async def terminate_ui(self, interaction):
        self.stop()  # Stop the view from listening for interactions
        await interaction.message.delete()  # Delete the original message with the UI