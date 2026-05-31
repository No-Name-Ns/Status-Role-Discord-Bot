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
                    "status_text": os.getenv("STATUS_TEXT", ".gg/thangout"),
                    "role_id": os.getenv("ROLE_ID"),
                    "case_sensitive": False
                }
            ]
        }

        for key in ["bot_token", "guild_id", "log_channel_id", "thank_message_channel"]:
            if not config[key]:
                raise ValueError(f"Missing required field: {key}")

        if not config["status_roles"][0]["role_id"]:
            raise ValueError("Missing required field: ROLE_ID")

        return config

    async def on_ready(self):
        logger.info(f'{self.user} has connected to Discord!')

        guild = self.get_guild(int(self.config['guild_id']))
        if not guild:
            logger.error(f"Guild with ID {self.config['guild_id']} not found!")
            return

        logger.info(f"Bot is monitoring guild: {guild.name}")

    def get_member_status_text(self, member: discord.Member) -> Optional[str]:
        if not member.activities:
            return None

        for activity in member.activities:
            if isinstance(activity, discord.CustomActivity) and activity.name:
                return activity.name
            elif hasattr(activity, 'state') and activity.state:
                return activity.state

        return None

    def get_member_all_text(self, member: discord.Member) -> List[str]:
        texts = []

        if member.activities:
            for activity in member.activities:
                if isinstance(activity, discord.CustomActivity) and activity.name:
                    texts.append(activity.name)
                elif hasattr(activity, 'state') and activity.state:
                    texts.append(activity.state)
                elif hasattr(activity, 'details') and activity.details:
                    texts.append(activity.details)
                elif hasattr(activity, 'name') and activity.name:
                    texts.append(activity.name)

        if member.display_name and member.display_name != member.name:
            texts.append(member.display_name)

        texts.append(member.name)
        return texts

    def check_member_text_match(self, member: discord.Member, status_config: dict) -> bool:
        all_texts = self.get_member_all_text(member)
        for text in all_texts:
            if text and self.status_matches(text, status_config):
                return True
        return False

    def status_matches(self, status_text: str, status_config: dict) -> bool:
        target_text = status_config['status_text']
        case_sensitive = status_config.get('case_sensitive', False)

        if not case_sensitive:
            return target_text.lower() in status_text.lower()
        return target_text in status_text

    async def send_log_message(self, message: str):
        try:
            channel = self.get_channel(int(self.config['log_channel_id']))
            if channel:
                await channel.send(message)
            else:
                logger.error("Log channel not found!")
        except Exception as e:
            logger.error(f"Error sending log message: {e}")

    async def on_presence_update(self, before: discord.Member, after: discord.Member):
        if after.bot:
            return

        guild = after.guild
        if guild.id != int(self.config['guild_id']):
            return

        current_status = self.get_member_status_text(after)
        previous_status = self.user_status_cache.get(after.id)

        if current_status:
            self.user_status_cache[after.id] = current_status
        elif after.id in self.user_status_cache:
            del self.user_status_cache[after.id]

        for status_config in self.config['status_roles']:
            role = guild.get_role(int(status_config['role_id']))
            if not role:
                logger.error(f"Role with ID {status_config['role_id']} not found!")
                continue

            has_role = role in after.roles
            should_have_role = self.check_member_text_match(after, status_config)

            if should_have_role and not has_role:
                try:
                    await after.add_roles(role)

                    await self.send_log_message(
                        f"✅ **{after.display_name}** set their status/activity/profile to contain `{status_config['status_text']}` and received the **{role.name}** role!"
                    )

                    logger.info(f"Added role {role.name} to {after.display_name}")

                except discord.Forbidden:
                    logger.error(f"No permission to add role {role.name} to {after.display_name}")
                except Exception as e:
                    logger.error(f"Error adding role to {after.display_name}: {e}")

            elif not should_have_role and has_role:
                try:
                    await after.remove_roles(role)
                    logger.info(f"Removed role {role.name} from {after.display_name}")
                except discord.Forbidden:
                    logger.error(f"No permission to remove role {role.name} from {after.display_name}")
                except Exception as e:
                    logger.error(f"Error removing role from {after.display_name}: {e}")

    async def on_member_update(self, before: discord.Member, after: discord.Member):
        if after.bot:
            return

        guild = after.guild
        if guild.id != int(self.config['guild_id']):
            return

        for status_config in self.config['status_roles']:
            role = guild.get_role(int(status_config['role_id']))
            if not role:
                continue

            has_role = role in after.roles
            should_have_role = self.check_member_text_match(after, status_config)

            if should_have_role and not has_role:
                try:
                    await after.add_roles(role)

                    await self.send_log_message(
                        f"✅ **{after.display_name}** updated their profile to contain `{status_config['status_text']}` and received the **{role.name}** role!"
                    )

                    logger.info(f"Added role {role.name} to {after.display_name} (profile update)")

                except discord.Forbidden:
                    logger.error(f"No permission to add role {role.name} to {after.display_name}")
                except Exception as e:
                    logger.error(f"Error adding role to {after.display_name}: {e}")

            elif not should_have_role and has_role:
                try:
                    await after.remove_roles(role)
                    logger.info(f"Removed role {role.name} from {after.display_name} (profile update)")
                except discord.Forbidden:
                    logger.error(f"No permission to remove role {role.name} from {after.display_name}")
                except Exception as e:
                    logger.error(f"Error removing role from {after.display_name}: {e}")

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return


bot = StatusRoleBot()

if __name__ == "__main__":
    bot.run(bot.config['bot_token'])
