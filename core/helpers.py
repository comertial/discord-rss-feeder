import asyncio
import re
from discord.ext import commands
from datetime import datetime, timedelta

from DatabaseManager import db_manager
from core.constants import MESSAGES


def update_rss_feeds():
    return db_manager.select(
        tables=['RssFeed'],
        # columns=['RssFeed.server', 'RssFeed.url', 'RssHistory.timestamp'],
        # join_conditions=['RssFeed.server = RssHistory.server AND RssFeed.url = RssHistory.url'],
        # where_condition='RssFeed.enabled == 1',
        # order_by=['RssHistory.timestamp DESC', 'RssFeed.server ASC']
    )


async def is_valid_user(ctx):
    server_role = db_manager.get_accepted_role(ctx.guild.id)
    server_role = int(server_role[0]['role_id']) if len(server_role) == 1 else None

    # If no server role is configured, return True
    if server_role is None:
        return True

    # Check if the server role exists in the guild's roles
    guild_roles = ctx.guild.roles
    if not any(role.id == server_role for role in guild_roles):
        # If the server role is not found in the guild's roles, return True
        return True

    # Check if the user has the server role
    author_roles = ctx.author.roles
    if any(server_role == role.id for role in author_roles):
        return True
    else:
        await ctx.send(MESSAGES['NoPermissions'], silent=True)
        return False



async def wait_until_next_execution():
    now = datetime.now()
    # target_time = now.replace(second=0, microsecond=0)
    target_time = now.replace(minute=0, second=0, microsecond=0)
    if now > target_time:
        # target_time += timedelta(minutes=1)
        target_time += timedelta(hours=1)
    await asyncio.sleep((target_time - now).total_seconds())


async def delete_old_history():
    while True:
        await wait_until_next_execution()
        # print(f"This function runs at 0 seconds of every minute: {datetime.now()}")
        db_manager.scheduled_delete_rss_history()