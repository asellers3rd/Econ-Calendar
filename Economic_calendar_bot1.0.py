import discord
import requests
from ics import Calendar
import asyncio
import os

# Get the Discord token from environment variables
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')  # Get Discord Token from environment variables

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

# Set up the Discord bot client with the required intents
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')

    # Wait for a short period to ensure the bot is fully ready
    await asyncio.sleep(3)

    # Get the high-priority events from the .ics file
    high_priority_events = filter_high_priority_events()

    # Prepare an embed to send to the channel
    embed = discord.Embed(title="Major Economic Events for the Week", color=0x00ff00)

    for event in high_priority_events:
        event_details = f"**Time**: {event.begin.format('YYYY-MM-DD HH:mm')}\n**Description**: {event.description}"
        
        # Check if adding this event exceeds the character limit for a single field
        if len(event_details) > 1024:
            event_details = event_details[:1021] + "..."  # Truncate if too long
        
        embed.add_field(name=event.name, value=event_details, inline=False)

    # Replace with the actual channel ID
    channel = client.get_channel(992916288030646383)  # replace with actual channel ID

    if channel is None:
        print("Channel not found or bot does not have access.")
        await client.close()  # Close bot after the error
        return

    # Send the embed to the channel
    await channel.send(embed=embed)

    # Close the bot after sending the file
    await client.close()

# Run the bot
client.run(DISCORD_TOKEN)
