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

import discord
from discord.ext import commands
import json
import asyncio
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
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
            required_fields = ['bot_token', 'guild_id', 'log_channel_id', 'status_roles']
            for field in required_fields:
                if field not in config:
                    raise ValueError(f"Missing required field: {field}")
            if not config['status_roles']:
                raise ValueError("status_roles cannot be empty")
            return config
        except FileNotFoundError:
            logger.error("config.json not found!")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config.json: {e}")
            raise
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            raise
    async def on_ready(self):
        logger.info(f'{self.user} has connected to Discord!')
        guild = self.get_guild(int(self.config['guild_id']))
        if not guild:
            logger.error(f"Guild with ID {self.config['guild_id']} not found!")
            return
        channel = guild.get_channel(int(self.config['log_channel_id']))
        if not channel:
            logger.error(f"Channel with ID {self.config['log_channel_id']} not found!")
            return
        logger.info(f"Bot is monitoring guild: {guild.name}")
        logger.info(f"Log channel: #{channel.name}")
        await self.initial_status_scan(guild)
    async def initial_status_scan(self, guild: discord.Guild):
        logger.info("Performing initial status and text scan...")
        for member in guild.members:
            if member.bot:
                continue
            current_status = self.get_member_status_text(member)
            if current_status:
                self.user_status_cache[member.id] = current_status
            for status_config in self.config['status_roles']:
                if self.check_member_text_match(member, status_config):
                    role = guild.get_role(int(status_config['role_id']))
                    if role and role not in member.roles:
                        try:
                            await member.add_roles(role)
                            logger.info(f"Added role {role.name} to {member.display_name} during initial scan")
                        except discord.Forbidden:
                            logger.error(f"No permission to add role {role.name} to {member.display_name}")
                        except Exception as e:
                            logger.error(f"Error adding role to {member.display_name}: {e}")
        logger.info("Initial status and text scan completed")
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
        else:
            return target_text in status_text
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
                had_required_status = previous_status and self.status_matches(previous_status, status_config)
                if had_required_status:
                    try:
                        await after.remove_roles(role)
                        await self.send_log_message(
                            f"❌ **{after.display_name}** removed `{status_config['status_text']}` from their profile and lost the **{role.name}** role!"
                        )
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
                    await self.send_log_message(
                        f"❌ **{after.display_name}** removed `{status_config['status_text']}` from their profile and lost the **{role.name}** role!"
                    )
                    logger.info(f"Removed role {role.name} from {after.display_name} (profile update)")
                except discord.Forbidden:
                    logger.error(f"No permission to remove role {role.name} from {after.display_name}")
                except Exception as e:
                    logger.error(f"Error removing role from {after.display_name}: {e}")
    async def send_log_message(self, message: str):
        try:
            channel = self.get_channel(int(self.config['log_channel_id']))
            if channel:
                await channel.send(message)
            else:
                logger.error("Log channel not found!")
        except Exception as e:
            logger.error(f"Error sending log message: {e}")
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return  # Suppress CommandNotFound errors completely
        # Suppress all other errors as well (no output, no log)
bot = StatusRoleBot()
if __name__ == "__main__":
    try:
        bot.run(bot.config['bot_token'])
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
