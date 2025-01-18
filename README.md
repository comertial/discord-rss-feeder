# 🤖 Discord RSS Feeder Bot

A user-friendly Discord bot for managing and distributing RSS feeds in your server. It supports adding, updating, deleting, and viewing RSS feeds, as well as automatically fetching and posting new feed items to specified channels.

## Table of Contents
- [Features](#features)
- [Installation](#installation)
- [Configuration](#configuration)
- [Commands](#commands)
- [Manually Running the Bot](#manually-running-the-bot)
- [Contributing](#contributing)
- [License](#license)

## Features
- 🚀 **Automatic RSS Feed Fetching and Posting**  
  Checks RSS feeds every minute and posts new items to designated channels.
- ✅ **Easy Feed Management**  
  Simple commands to add, update, and delete RSS feeds.
- 🛠️ **Intuitive Configuration**  
  Straightforward setup for channels and user roles.
- 👋 **Built-in User Commands**  
  Includes handy commands like greeting and server info.

## Installation
1. **Clone the repository**:  
   ```bash
   git clone https://github.com/comertial/discord-rss-feeder.git
   cd discord-rss-feeder
   ```

2. **Set up a virtual environment**:  
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install the dependencies**:  
   ```bash
   pip install -r requirements.txt
   ```

## Configuration
1. **Create a Discord Application Bot**  
   - Go to the [Discord Developer Portal](https://discord.com/developers/applications) and create a new application.  
   - Under **Installation** at the bottom of the page, add the `bot` scope in **Guild Install**.  
   - For **Permissions**, select **Administrator** (this may be refined later to just what is required).  
   - Under **Bot** in the **Privileged Gateway Intents** section, enable all the intents needed (this too may be refined in the future).  
   - On the same page, under **Token**, click **Reset Token** and copy the displayed token for use in the next steps.  
   - Copy your **Install Link** (found under **Installation**) and open it in your browser.  
   - Choose the server where you want to add the bot, click **Continue**, then **Authorize**.  
   - You should now see your bot in your Discord server.

2. **Create a `.env` file** in the project root to store your bot token:
   ```dotenv
   TOKEN=your_discord_bot_token
   ```

3. **(Optional) Create a systemd service** for stability:
   ```bash
   vi /etc/systemd/system/discord-rss-feeder.service
   ```
   Example service file (change directories and names as needed):
   ```text
   [Unit]
   Description=Discord RSS Feeder Bot
   After=network.target
        
   [Service]
   User=ubuntu
   Group=ubuntu
   WorkingDirectory=/home/ubuntu/discord-rss-feeder
   ExecStart=/home/ubuntu/discord-rss-feeder/venv/bin/python -u /home/ubuntu/discord-rss-feeder/main.py
   Restart=always
   RestartSec=30
   Environment="PATH=/home/ubuntu/discord-rss-feeder/venv/bin"
        
   [Install]
   WantedBy=multi-user.target
   ```

4. **Apply the systemd changes**:
   ```bash
   systemctl daemon-reload
   systemctl enable discord-rss-feeder
   systemctl start discord-rss-feeder
   ```

## Commands
| Command                  | Syntax                  | Description                                                                 |
|--------------------------|-------------------------|-----------------------------------------------------------------------------|
| **Ping**                 | `!ping`                 | Responds with "Pong!".                                                      |
| **Greet**                | `!greet [name]`         | Greets the user with the provided name.                                     |
| **Welcome**              | `!welcome`              | Outputs the configured welcome message.                                     |
| **Get Server Name**      | `!server_name`          | Returns the current server’s name and ID.                                   |
| **Get Main Channel**     | `!get_main_channel`     | Returns the current server’s main channel.                                  |
| **Update Main Channel**  | `!update_main_channel`  | Updates the current server's main channel.                                  |
| **Update Admin Role**    | `!update_admin_role`    | Updates the current server's admin role.                                    |
| **Get Admin Role**       | `!get_admin_role`       | Returns the current server's admin role.                                    |
| **Add RSS Feed**         | `!add_rss_feed`         | Prompts the user to enter a new RSS feed.                                   |
| **Update RSS Feed**      | `!update_rss_feed`      | Updates an existing RSS feed.                                               |
| **Delete RSS Feeds**     | `!delete_rss_feeds`     | Deletes one or more RSS feeds from the server.                              |
| **Get RSS Feeds**        | `!get_rss_feeds`        | Lists all configured RSS feeds for the server.                              |
| **Configure RSS Feeds**  | `!configure_rss_feeds`  | Enables or disables existing feeds.                                         |

> **Note**: An admin role is required for commands that add or update content. Commands that retrieve information can be used by anyone.

## Manually Running the Bot
To manually run the bot, simply execute:

```bash
venv/bin/python main.py
```

Ensure your `.env` file is set up with the correct bot token before running this command.

## Contributing
We ❤️ contributions and welcome everyone to help improve this project! Whether it’s fixing bugs, suggesting new features, or tackling some of the open issues, we’d love to have your input.

If you're interested in contributing, here’s how you can get started:

### How to Contribute
1. **Report Issues**: Found a bug or have a feature request? Open an issue in the GitHub repository to let us know!  
2. **Submit Changes**: Want to fix bugs, add features, or improve documentation? Fork the repository, make your changes, and create a pull request (PR).  
3. **Discuss Ideas**: Not sure where to start? Join the discussion in the issues section to share your ideas or ask for guidance.

### Submitting your Contribution
Contributions follow the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) specification for commit messages. It is required for all the commits to follow this convention in order to be accepted.

When submitting a pull request:  
1. **Keep It Simple**: Focus on a single feature, bug fix, or improvement. If you want to make multiple changes, consider separating them into different PRs.  
2. **Add Details**: Provide a clear description of your changes in the PR description. Include any relevant context to help understand your contribution.  
3. **Be Consistent**: Follow the structure and style outlined in the codebase to keep things clean and maintainable.

### Keeping the Changelog Fresh
We use **git-cliff** to automatically update the `CHANGELOG.md` file with a summary of new changes:  
1. Install `git-cliff`:  
   ```bash
   pip install git-cliff==2.7.0
   ```
2. Add the following script as a Git `pre-commit` hook to automatically refresh the changelog before pushing changes. Create a file at `.git/hooks/pre-commit` and paste:  
   ```shell
   #!/bin/sh
   
   # Check if git-cliff is installed
   if ! command -v git-cliff >/dev/null 2>&1; then
       echo "Warning: git-cliff is not installed, skipping changelog generation"
       exit 0
   fi
   
   # Generate the changelog
   git cliff -o CHANGELOG.md || {
       echo "Error: Failed to generate changelog"
       exit 1
   }
   
   # Check if the changelog was modified
   if git diff --quiet CHANGELOG.md; then
       # No changes to changelog
       exit 0
   else
       # Changelog was modified, add it to the commit
       git add CHANGELOG.md || {
           echo "Error: Failed to add CHANGELOG.md to the commit"
           exit 1
       }
   fi
   ```

This script ensures that the changelog always stays up-to-date, so you don’t have to worry about forgetting to include your changes.

### Need Help?
If you encounter any problems or have questions while contributing, feel free to open an issue or reach out. We’re happy to help!

## License
This project is licensed under the [MIT License](LICENSE). Feel free to use and modify it for your own needs.