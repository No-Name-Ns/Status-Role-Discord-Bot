# Status Role Discord Bot

A Discord bot that monitors user statuses, activities, and display names and automatically assigns roles based on configured text patterns.

## Features

- **Automatic Role Assignment**: Assigns roles to users when their profile contains specific text
- **Multi-Source Monitoring**: Monitors custom statuses, activity details, and display names
- **Real-time Monitoring**: Monitors profile changes in real-time
- **Configurable Patterns**: Support for multiple text patterns and corresponding roles
- **Logging**: Sends messages to a configured channel when roles are assigned/removed
- **Admin Commands**: Commands for checking profile text and reloading configuration

## Development & Support

Need help or want to contribute?
Join our Development/Support Server: [https://discord.gg/3bwYgqQsQp](https://discord.gg/3bwYgqQsQp)

## What It Monitors

The bot checks for text patterns in:
- **Custom Status Messages**: User's custom status text
- **Activity Details**: Details from activities like games, Spotify, etc.
- **Display Names**: Server nicknames and global display names
- **Activity Names**: Names of activities and rich presence data

*Note: Discord bios are not accessible via the bot API, but the bot monitors all other available text sources.*

## Setup

### Prerequisites

- Python 3.8 or higher
- A Discord bot token
- Administrator permissions in your Discord server

### Installation

1. Clone this repository:
   ```bash
   git clone <repository-url>
   cd Status-Role-Discord-Bot
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure the bot by editing `config.json`:
   ```json
   {
     "bot_token": "YOUR_BOT_TOKEN_HERE",
     "guild_id": "YOUR_GUILD_ID_HERE",
     "log_channel_id": "YOUR_LOG_CHANNEL_ID_HERE",
     "status_roles": [
       {
         "status_text": "discord.gg/maharlika",
         "role_id": "YOUR_ROLE_ID_HERE",
         "case_sensitive": false
       }
     ]
   }
   ```

### Configuration

#### Required Settings

- `bot_token`: Your Discord bot token
- `guild_id`: The ID of the Discord server to monitor
- `log_channel_id`: Channel ID where the bot will send role assignment messages
- `status_roles`: Array of status pattern configurations

#### Status Role Configuration

Each entry in `status_roles` should have:
- `status_text`: The text to look for in user statuses
- `role_id`: The Discord role ID to assign
- `case_sensitive`: Whether the text matching should be case-sensitive (default: false)

### Getting Discord IDs

1. Enable Developer Mode in Discord (User Settings > Advanced > Developer Mode)
2. Right-click on servers, channels, or roles to copy their IDs

### Running the Bot

```bash
python bot.py
```

## How It Works

1. **Profile Monitoring**: The bot monitors all members' presence updates and profile changes
2. **Pattern Matching**: When any monitored text changes, it checks if the new text contains any configured patterns
3. **Role Assignment**: If a match is found in any available text source, the corresponding role is assigned
4. **Role Removal**: If a user removes the required text from all monitored sources, the role is removed
5. **Logging**: All role changes are logged to the configured channel with details about where the match was found

## Example

If configured with:
```json
{
  "status_text": "discord.gg/maharlika",
  "role_id": "123456789012345678",
  "case_sensitive": false
}
```

**Scenarios:**
- User sets custom status to "Join our server! discord.gg/maharlika" → Gets the role
- User sets their nickname to "John - discord.gg/maharlika" → Gets the role
- User has a game activity with "discord.gg/maharlika" in details → Gets the role
- User removes text from all monitored sources → Loses the role

Bot sends messages to the log channel for all actions, showing where the match was found.

## Bot Permissions

The bot requires the following permissions:
- View Channels
- Send Messages
- Manage Roles
- Read Message History

## Troubleshooting

1. **Bot not responding**: Check that the bot token is correct and the bot is online
2. **Role not assigned**: Ensure the bot has permission to manage the target role
3. **No log messages**: Verify the log channel ID is correct and the bot can send messages there
4. **Status not detected**: Make sure the bot has the "Presence Intent" enabled in the Discord Developer Portal

## License

This project is licensed under the MIT License - see the LICENSE file for details.
