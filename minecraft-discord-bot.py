import config
import discord
import os
from discord.ext import tasks
from datetime import datetime
from mctools import RCONClient
from mctools import QUERYClient
import re

server_ip = os.environ.get('SERVER_IP')
discord_app_token = os.environ.get('DISCORD_APP_TOKEN')
server_rcon_password = os.environ.get('RCON_PASSWORD')
refresh_frequency = config.refresh_frequency
discord_bot_embed_color = config.embed_color

def embed_message(title: str = '', description: str = '', fields: dict = {}, color: discord.Colour = discord.Colour(0xFFFFFF)):
    embed = discord.Embed(title=title,description=description,color=color,timestamp=datetime.now())
    if fields:
        for key in fields:
            embed.add_field(name=key,value=fields[key], inline=False)
    return embed

def rcon_say(announcment: str):
    with RCONClient(server_ip) as mcr:
        if mcr.login(server_rcon_password):
            resp = mcr.command(f"/say {announcment}")

def mob_griefing_on():
    with RCONClient(server_ip) as mcr:
        if mcr.login(server_rcon_password):
            resp = mcr.command("/gamerule mobGriefing")
    return False if 'false' in resp.lower() else True

def set_mob_griefing(setting: bool):
    if setting:
        setting = 'true'
    else:
        setting = 'false'
    with RCONClient(server_ip) as mcr:
        if mcr.login(server_rcon_password):
            resp = mcr.command(f"/gamerule mobGriefing {setting}")
    return resp

def remove_escape_mc_response(response: str):
    return response.replace("\x1b[0m",'')

def query_full_stats():
    try:
        with QUERYClient(server_ip) as query:
            full_stats = query.get_full_stats()
        return full_stats
    except:
        raise Exception

def get_str_list_of_online_players(full_stats_query):
    online_players = ', '.join([remove_escape_mc_response(player_name) for player_name in full_stats_query['players']])
    if len(online_players) == 0:
        return 'No one online'
    else:
        return online_players
        
def get_player_fraction(full_stats_query):
    return f"{full_stats_query['numplayers']}/{full_stats_query['maxplayers']}"

def get_server_version(full_stats_query):
    return full_stats_query['version']


bot = discord.Bot()


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    get_server_status.start()

@tasks.loop(seconds=refresh_frequency)
async def get_server_status():
    try:
        full_stats = query_full_stats()
        await bot.change_presence(status=discord.Status.online,activity=discord.Activity(name=get_player_fraction(full_stats), type=discord.ActivityType.playing))
        print(f"{get_player_fraction(full_stats)} online")
    except:
        print(f'Could not query {server_ip}')
        await bot.change_presence(status=discord.Status.do_not_disturb,activity=discord.Activity(name='Server offline', type=discord.ActivityType.playing))

@bot.slash_command(description=f'Players online for minecraft server at {server_ip}')
async def status(ctx):
    try:
        full_stats = query_full_stats()
        online_players = get_str_list_of_online_players(full_stats)
        embeded_message = embed_message(
            title=f"Minecraft Server: {server_ip}",
            fields={
                f"{get_player_fraction(full_stats)} online:": online_players,
                "Server version: ": f"{get_server_version(full_stats)}"
            },
            color = discord.Colour(discord_bot_embed_color)
        )
        await ctx.respond(embed=embeded_message)
    except:
        await ctx.respond("Error getting server status")

@bot.slash_command(description=f'Toggle mobGriefing')
async def togglemobgriefing(ctx):
    resp = set_mob_griefing(not mob_griefing_on())
    rcon_say(f"Discord User {ctx.author} invoked: {remove_escape_mc_response(resp)}")
    await ctx.respond(remove_escape_mc_response(resp))

@bot.slash_command(description=f'Check if gamerule mobGriefing is true/false')
async def ismobgriefingon(ctx):
    with RCONClient(server_ip) as mcr:
        if mcr.login(server_rcon_password):
            resp = mcr.command("/gamerule mobGriefing")
    await ctx.respond(remove_escape_mc_response(resp))

bot.run(discord_app_token)