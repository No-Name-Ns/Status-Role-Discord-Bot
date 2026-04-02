"""
MIT License

Copyright (c) 2025 ItsMeRiooooPH

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import os
import discord
from discord.ext import commands
import logging
from typing import Dict, List, Optional

logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


class StatusRoleBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.presences = True
        intents.members = True
        intents.guilds = True
        intents.message_content = True

        super().__init__(
            command_prefix='!',
            intents=intents,
            help_command=None
        )

        self.config = self.load_config()
        self.user_status_cache: Dict[int, str] = {}

    def load_config(self) -> dict:
        config = {
            "bot_token": os.getenv("BOT_TOKEN"),
            "guild_id": os.getenv("GUILD_ID"),
            "log_channel_id": os.getenv("LOG_CHANNEL_ID"),
            "thank_message_channel": os.getenv("THANK_MESSAGE_CHANNEL"),
            "status_roles": [
                {
                    "status_text": os.getenv("STATUS_TEXT", ".gg/detention"),
                    "role_id": os.getenv("ROLE_ID"),
                    "case_sensitive": False
                }
            ]
        }

        for key in ["bot_token", "guild_id", "log_channel_id", "thank_message_channel"]:
            if not config[key]:
                raise ValueError(f"Missing required field: {key}")

        return config

    async def on_ready(self):
        logger.info(f'{self.user} has connected to Discord!')

    def get_member_status_text(self, member: discord.Member) -> Optional[str]:
        if not member.activities:
            return None

        for activity in member.activities:
            if isinstance(activity, discord.CustomActivity) and activity.name:
                return activity.name
        return None

    def status_matches(self, status_text: str, target: str) -> bool:
        return target.lower() in status_text.lower()

    async def send_thank_you(self, member):
        channel = self.get_channel(int(self.config['thank_message_channel']))
        if channel:
            await channel.send(f"{member.mention} thank you for supporting the server!")

    async def on_presence_update(self, before, after):
        if after.bot:
            return

        if after.guild.id != int(self.config['guild_id']):
            return

        role_id = int(self.config['status_roles'][0]['role_id'])
        target_text = self.config['status_roles'][0]['status_text']

        role = after.guild.get_role(role_id)
        if not role:
            return

        status = self.get_member_status_text(after)
        has_role = role in after.roles
        match = status and self.status_matches(status, target_text)

        if match and not has_role:
            await after.add_roles(role)
            await self.send_thank_you(after)
            logger.info(f"Gave role to {after.display_name}")

        elif not match and has_role:
            await after.remove_roles(role)
            logger.info(f"Removed role from {after.display_name}")  # no message sent

bot = StatusRoleBot()

if __name__ == "__main__":
    bot.run(bot.config['bot_token'])
