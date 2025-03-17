import discord
import requests
from ics import Calendar
import asyncio
import os
from github import Github
from io import StringIO

# Get the Discord token and GitHub token from environment variables
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')  # Get Discord Token from environment variables
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')    # Get GitHub Token from environment variables
GITHUB_REPO = 'asellers3rd/Econ-Calendar'   # Replace with your GitHub username/repository

# Forex Factory ICS URL
ICS_URL = 'https://nfs.faireconomy.media/ff_calendar_thisweek.ics?version=a594518ff4aa9b1f49e3afb037dbe3c5'

# Set up the intents
intents = discord.Intents.default()
intents.message_content = True  # You need to enable this to read and send messages

# Function to filter high-priority events
def filter_high_priority_events():
    response = requests.get(ICS_URL)
    calendar = Calendar(response.text)

    high_priority_events = []
    for event in calendar.events:
        if 'High' in event.description or 'High' in event.name:
            high_priority_events.append(event)

    # Sort events by their start date
    sorted_events = sorted(high_priority_events, key=lambda e: e.begin)
    return sorted_events

# Function to upload the filtered ICS file to GitHub
def upload_to_github(file_path, file_name):
    # Initialize GitHub API client
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(GITHUB_REPO)
    
    # Read the file content
    with open(file_path, 'r') as file:
        content = file.read()

    # Get the path to store the file in the repo (e.g., in the root directory)
    try:
        # Try to update the file if it already exists
        repo.update_file(file_name, "Updating filtered Forex calendar", content, repo.get_contents(file_name).sha)
    except:
        # If the file doesn't exist, create a new one
        repo.create_file(file_name, "Adding filtered Forex calendar", content)

# Function to delete previous messages in the channel
async def delete_previous_messages(channel):
    # Fetch the last 100 messages from the channel
    messages = [message async for message in channel.history(limit=100)]
    
    # Delete each message one by one
    for message in messages:
        try:
            await message.delete()
            print(f"Deleted message: {message.content}")
        except discord.errors.Forbidden:
            print("Bot does not have permission to delete messages.")
        except discord.errors.NotFound:
            print("Message not found, might have already been deleted.")

# Set up the Discord bot client with the required intents
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')

    # Wait for a short period to ensure the bot is fully ready
    await asyncio.sleep(3)

    # Get the high-priority events from the .ics file
    high_priority_events = filter_high_priority_events()

    # Replace with the actual channel ID
    channel = client.get_channel(992916288030646383)  # replace with actual channel ID

    if channel is None:
        print("Channel not found or bot does not have access.")
        await client.close()  # Close bot after the error
        return

    # Delete previous messages
    await delete_previous_messages(channel)

    # Split events into chunks of 25
    chunk_size = 25
    for i in range(0, len(high_priority_events), chunk_size):
        # Create a new embed for each chunk
        embed = discord.Embed(title="Major Economic Events for the Week", color=0x00ff00)
        
        for event in high_priority_events[i:i + chunk_size]:
            event_details = f"**Time**: {event.begin.format('YYYY-MM-DD HH:mm')}\n**Description**: {event.description}"
            
            # Check if adding this event exceeds the character limit for a single field
            if len(event_details) > 1024:
                event_details = event_details[:1021] + "..."  # Truncate if too long
            
            embed.add_field(name=event.name, value=event_details, inline=False)

        # Send the embed to the channel
        await channel.send(embed=embed)

    # Save the filtered events to a new .ics file
    filtered_calendar = Calendar()
    for event in high_priority_events:
        filtered_calendar.events.add(event)

    # Save the .ics file locally
    ics_file_path = 'high_priority_forex_factory.ics'
    with open(ics_file_path, 'w') as file:
        file.writelines(filtered_calendar)

    # Upload the .ics file to GitHub
    upload_to_github(ics_file_path, 'high_priority_forex_factory.ics')

    # Close the bot after sending the file
    await client.close()

# Run the bot
client.run(DISCORD_TOKEN)
