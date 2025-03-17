import discord
from discord import app_commands
import requests
import os
import json
from github import Github
from ics import Calendar

# Get the Discord token and GitHub token from environment variables
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')  # Get Discord Token from environment variables
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')    # Get GitHub Token from environment variables
GITHUB_REPO = 'asellers3rd/RTA'   # Replace with your GitHub username/repository

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
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(GITHUB_REPO)
    
    with open(file_path, 'r') as file:
        content = file.read()

    try:
        repo.update_file(file_name, "Updating filtered Forex calendar", content, repo.get_contents(file_name).sha)
    except:
        repo.create_file(file_name, "Adding filtered Forex calendar", content)

# Load config data from the JSON file
def load_config():
    try:
        with open("config.json", "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"channel_id": None}

# Save config data to the JSON file
def save_config(data):
    with open("config.json", "w") as file:
        json.dump(data, file, indent=4)

# Create the bot with the necessary intents
class MyClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        # Register slash commands with Discord
        await self.tree.sync()

    async def on_ready(self):
        print(f'Logged in as {self.user}')

client = MyClient(intents=intents)

# Slash command to set the channel dynamically
@client.tree.command(name="setchannel", description="Set the channel to receive Forex updates")
@app_commands.checks.has_permissions(administrator=True)
async def set_channel(interaction: discord.Interaction, channel: discord.TextChannel):
    # Save the channel ID to config.json
    config = load_config()
    config["channel_id"] = channel.id
    save_config(config)

    await interaction.response.send_message(f"Channel has been set to <#{channel.id}>")

# Command to send the Forex calendar
@client.tree.command(name="sendforex", description="Send major Forex events to the set channel")
async def send_forex(interaction: discord.Interaction):
    config = load_config()
    channel_id = config.get("channel_id")

    if channel_id is None:
        await interaction.response.send_message("No channel set. Use `/setchannel` to set a channel.")
        return

    channel = client.get_channel(channel_id)
    if channel is None:
        await interaction.response.send_message("The channel is not found.")
        return

    # Fetch high-priority events
    high_priority_events = filter_high_priority_events()

    # Prepare an embed for the Discord message
    embed = discord.Embed(title="Major Economic Events for the Week", color=0x00ff00)
    for event in high_priority_events:
        event_details = f"**Time**: {event.begin.format('YYYY-MM-DD HH:mm')}\n**Description**: {event.description}"
        embed.add_field(name=event.name, value=event_details, inline=False)

    await channel.send(embed=embed)
    await interaction.response.send_message(f"Sent Forex events to <#{channel.id}>.")

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

# Run the bot
client.run(DISCORD_TOKEN)
