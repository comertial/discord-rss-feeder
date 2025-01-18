import os
from dotenv import load_dotenv

load_dotenv()

MESSAGES = {
    'NoRssFound': 'No RSS feeds found for this server.',
    'NoScoresFound': 'No scores found for this server.',
    'NoUsersSelected': 'No users selected.',
    'WelcomeMessage': '@everyone Get ready to be fed with RSS!',
    'NoPermissions': 'You do not have permissions to execute this command.',
    'InvalidInput': 'Your input is not valid.'
}

TOKEN = os.getenv('TOKEN')
