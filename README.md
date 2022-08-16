# Game_Guesser_Bot
Discord bot that records game guesser scores and stores them in a text file. 
Saves user data, resets a daily play key based on time zone set on discord 
server and posts weekly high score every Saturday night.

The key concepts to understand are that the discord.Bot class is a
subclass of discord.Client, meaning that the Bot class can access
all the relevant server and user information in addition to added
functionalities like responding to queries from users. To access
users on a server you have to enable an additional permission
(performed near the top of the code) and also (or maybe alternitvely?)
enable the ability for the bot to access user information within the
discord client settings as well.

Resource that was very helpful for this process:
https://realpython.com/how-to-make-a-discord-bot-python/
