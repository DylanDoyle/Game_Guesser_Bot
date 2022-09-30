# ---DONE---
# The bot should recognize game guesser results posted to the chat and give them a score
# based on the image of red/green blocks
# The score should be assigned to the user who posted the link
# The bot should only take one score input per user per day
# THIS CAN BE CONTROLLED WITH THE TIME ZONE ROLES
# The bot should keep track of each users lifetime and weekly scores
# The bot should post on Saturday night the high scorers of the week

# ---WIP---
# The bot should operate on a raspberry pi
# The bot should backup the game data once a week

# The bot should respond to requests for score info from users
# Generate fun message for high score or hot streaks
# Track medals, assign prestige

# User scores have the 1. username, 2. lifetime points, 3. weekly points, 4. score flag
# Maybe add hot streak flag or medal tracking later


import os
import random
import emoji
import aiocron
from dotenv import load_dotenv
import discord
from discord.ext import commands, tasks


load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')

intents = discord.Intents.default()
intents.members = True
# intents.message_content = True This line is needed on the rasperry Pi for some reason. Maybe on all setups after 8/31/22 when they change permisions
bot = commands.Bot(command_prefix='!', intents=intents) # This is needed for the bot to access the list of users on the server

target_channel_id = 1006957133616660491

users = []
file_name = 'user_scores.txt'
eastern_time = 'Eastern Time'
central_time = 'Central Time'
mountain_time = 'Mountain Time'
pacific_time = 'Pacific Time'
cant_gain_points = "You can't earn any more points today!"

def add_new_user(user_id, score, file_name):
    """Function to add a new user to the file keeping track"""
    # Add to the end of the file the username, total score, weekly score, 
    # and lock out of more points till reset
    with open(file_name, 'a') as file:
        file.write(" " + str(user_id) + " " + str(score) + " " + str(score) + " " + 'N')

def check_for_user_id(user_id, contents):
    """Function to check for the user id"""
    for item in contents:
        if item == user_id:
            return True

def update_score(user_id, score, contents, file_name):
    """Function that updates the total and weekly scores 
    as well as disabling the play key until reset time"""
    index = 3 # ADD WEEKLY SCORE INCREASE AS WELL
    for user_name, total_score, weekly_score, play_key in zip(contents,
        contents[1:], contents[2:], contents[3:]):
        if user_name == user_id: # If we found the user ID...
            new_total_score = str(int(total_score) + score)
            contents[index-2] = new_total_score # Update the total score
            new_weekly_score = str(int(weekly_score) + score)
            contents[index-1] = new_weekly_score # Update the weekly score
            contents[index] = 'N' # Disable the play key
        index +=1
    write_formatted_contents(contents, file_name)
    
    return new_total_score, new_weekly_score

def reset_play_key(reset_list, file_name):
    """Function that contains all the functions needed to update the play key"""
    contents = get_user_score_contents()
    contents = update_play_key(contents, reset_list)
    write_formatted_contents(contents, file_name)

def update_play_key(contents, reset_list):
    """Function called by reset_play_key"""
    # Iterate through the list we just populated and make the change for each entry present
    for user_name_to_reset in reset_list:
        # Update contents with all the relevant changes before restoring it
        index = 3
        for username, play_token in zip(contents, contents[3:]):
            if username == user_name_to_reset:
                contents[index] = 'Y' # Change the token to true
            index += 1
    return contents

def get_user_score_contents():
    """Function to retrieve the contents of the user score file"""
    with open(file_name, 'r') as file:
        contents = file.read().split() # Store the contents of the user score file
        return contents

def write_formatted_contents(contents, file_name):
    """Function to write the correctly spaced contents back to the user_scores file"""
    spaced_contents = " ".join(contents)
    with open(file_name, 'w') as file:
        file.write(spaced_contents)

def generate_reset_list(time_zone):
    """Function to generate the list of names to reset at this hour"""
    # Generate the list of names to be reset but perform reset elsewhere
    reset_list = []
    for person in bot.guilds[0].members: # This is the readable python version for babies
        for this_role in person.roles:   # I am a python baby
            if time_zone in this_role.name:
                reset_list.append(person.name)
    return reset_list

def check_can_gain_points(message):
    """Function to check if the user can gain points"""
    contents = get_user_score_contents() # Get the contents to see if play token == Y/N
    index = 3
    for username, play_token in zip(contents, contents[3:]):
        if username == message.author.name:
            if contents[index] == 'Y': # Check if the message can be scored
                return True
            else:
                return False
        index += 1 

def list_to_string(list):
    """Function to convert an input list to an output string"""
    index = 0
    string = ""
    for item in list:
        string += item
        if index != len(list) - 1:
            string += ", "
        index += 1
    return string

@bot.listen()
async def on_message(message):
    msg = message.content.lower()
    message_user_name = message.author.name
    user_nickname = message.author.display_name
    guessthegame = '#guessthegame' # or could be a sentence or phrase (ie 'these words')
    red_square = '🟥'
    scoreboard_command = "!weekly_scoreboard"

    if scoreboard_command in msg:
        weekly_scoreboard()
    elif guessthegame in msg:
        # First check if the player is able to gain points
        score = 6
        for word in msg:
            if word == red_square:
                score -= 1

        contents = get_user_score_contents()

        if check_for_user_id(message_user_name, contents): # Existing user
            if check_can_gain_points(message):
                total_points, weekly_points = update_score(message_user_name, score, contents, file_name)
                existing_user = (
                    user_nickname + " earned " + str(score) + 
                    " more points for a total of " + str(total_points) + "\n" +
                    "Their score this week is " + str(weekly_points) + "!"
                )
                await message.channel.send(existing_user)
            else:
                await message.channel.send(cant_gain_points)
        else: # User not found
            add_new_user(message_user_name, score, file_name)
            new_user = ("This is " + user_nickname + 
            "'s first time playing!\n" + "Their starting score is " +
            str(score) + " points"
            )
            await message.channel.send(new_user)

async def weekly_scoreboard():
    """Function to share the current weekly scores for all users"""
    contents = get_user_score_contents()
    
    # Use this week's scores to generate a message
    weekly_scoreboard_message = ("Here are this week's current standings:" + "\n\n")
    for (player_id, weekly_score) in zip(contents, contents[2:]):
        if weekly_score > 0:
            weekly_scoreboard_message += "\t\t" + player_id + " - " + weekly_score + "\n"
    channel = bot.get_channel(target_channel_id)
    await channel.send(weekly_scoreboard_message)

@aiocron.crontab('0 23 * * 6')
async def weekly_winner():
    """Function to share the top five weekly scores and reset the weekly points for all users"""
    contents = get_user_score_contents()
    
    first_place_score = 0
    second_place_score = 0
    third_place_score = 0
    first_place_winners = []
    second_place_winners = []
    third_place_winners = []
    
    # First establish what the top three scores are
    # Afterwards establish which players have those scores and add them to the correct placement list
    index = 4
    for (player_id, weekly_score) in zip(contents, contents[2:]):
        if index % 4 != 0:
            index += 1
        elif weekly_score != '0':
            index += 1
            weekly_score_int = int(weekly_score) # Cast to int for comparisons
            if first_place_score == 0: # First entry
                first_place_score = weekly_score_int
            elif weekly_score_int > first_place_score: # Weekly score > 1st
                if second_place_score == 0: # If we haven't scored a second place yet
                    second_place_score = first_place_score # Move first down to second

                    first_place_score = weekly_score_int # Update first place
                else: # If we already have a 2nd place, then bump previous 2nd to third place
                    third_place_score = second_place_score

                    second_place_score = first_place_score

                    first_place_score = weekly_score_int
            elif (weekly_score_int > second_place_score) and (weekly_score_int != first_place_score): # Weekly score > 2nd and Weekly score < 1st
                third_place_score = second_place_score

                second_place_score = weekly_score_int
            elif (weekly_score_int > third_place_score) and (weekly_score_int != first_place_score) and (weekly_score_int != second_place_score): # Weekly score > 3rd and Weekly score < 2st
                third_place_score = weekly_score_int
        else:    
            index += 1

    # Check for ties!
    index = 4
    for (player_id, weekly_score) in zip(contents, contents[2:]):
        if index % 4 != 0:
            index += 1
        elif weekly_score != '0':
            index += 1
            weekly_score_int = int(weekly_score) # Cast to int for comparisons
            if weekly_score_int == first_place_score:
                first_place_winners.append(player_id)
            elif weekly_score_int == second_place_score:
                second_place_winners.append(player_id)
            elif weekly_score_int == third_place_score:
                third_place_winners.append(player_id)
        else:    
            index += 1

    # Sort the winners alphabetically
    first_place_winners.sort()
    second_place_winners.sort()
    third_place_winners.sort()

    # Convert to printable string
    first_place_string = list_to_string(first_place_winners)
    second_place_string = list_to_string(second_place_winners)
    third_place_string = list_to_string(third_place_winners)

    # Clear the weekly scores from all users
    # Update contents to have 0 in every weekly score field then write contents
    contents = get_user_score_contents()
    index = 4
    for entry in contents[2:]:
        if index % 4 == 0:
            contents[index-2] = '0'
        index += 1
        
    write_formatted_contents(contents, file_name)

    # Use the established winners to generate a message
    weekly_winner_message = (":fireworks:HERE ARE THIS WEEKS HIGH SCORERS:fireworks:" + "\n\n" + 
    "\t\t:first_place:" + first_place_string + " - " + str(first_place_score) + ":first_place:" + "\n" +
    "\t\t:second_place:" + second_place_string + " - " + str(second_place_score) + ":second_place:" + "\n" +
    "\t\t:third_place:" + third_place_string + " - " + str(third_place_score) + ":third_place:" + "\n"
    )
    channel = bot.get_channel(target_channel_id)
    await channel.send(weekly_winner_message)

@aiocron.crontab('0 23 * * *')
async def reset_game_key_et():
    """Function to reset the Eastern Time player keys"""
    reset_list = generate_reset_list(eastern_time)
    reset_play_key(reset_list, file_name)

@aiocron.crontab('0 0 * * *')
async def reset_game_key_ct():
    """Function to reset the Central Time player keys"""
    reset_list = generate_reset_list(central_time)
    reset_play_key(reset_list, file_name)

@aiocron.crontab('0 1 * * *')
async def reset_game_key_mt():
    """Function to reset the Mountain Time player keys"""
    reset_list = generate_reset_list(mountain_time)
    reset_play_key(reset_list, file_name)

@aiocron.crontab('0 2 * * *')
async def reset_game_key_pt():
    """Function to reset the Pacific Time player keys"""
    reset_list = generate_reset_list(pacific_time)
    reset_play_key(reset_list, file_name)

# Run the bot that runs this code
# At first this will run on my desktop but I want to move the setup over to a raspberry pi asap
bot.run(TOKEN) 