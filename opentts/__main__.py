from .bot import bot
import os
from dotenv import load_dotenv

load_dotenv()

bot.run(os.getenv("DISCORD_TOKEN"))