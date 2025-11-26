import os
import yt_dlp
import discord
from discord import app_commands
from discord.ext import commands

TOKEN = "" # Paste your token here

intents = discord.Intents.all()
bot = commands.Bot(command_prefix = "!", intents = intents)
role_map = {
    "🟥": 0000000000000000000, # Paste Role IDs here
    "🟦": 0000000000000000000
}

@bot.event
async def on_ready():
    await bot.change_presence(status = discord.Status.online)
    print(f"Logged as {bot.user}")

    await bot.tree.sync()

    channel = bot.get_channel(0000000000000000000) # Paste the embed channel ID
    await channel.purge(limit = None)

    embed = discord.Embed(title = "Title", description = "Description.")
    embed.add_field(name = "Roles:", value = f"<@&{role_map['🟥']}> <@&{role_map['🟦']}>", inline = False)
    embed.add_field(name = "Server ID:", value = str(channel.guild.id), inline = True)
    embed.set_image(url = "attachment://image.png")
    embed.set_footer(text = "Select a role:")
    file = discord.File("images/image.png", filename = "image.png")
    message = await channel.send(embed = embed, file = file, silent = True)

    for emoji in role_map:
        await message.add_reaction(emoji)

    bot.embed_id = message.id

@bot.tree.command(name = "ping", description = "Checks for connection")
async def ping_command(interaction: discord.Interaction):
    await interaction.response.send_message("Pong")

@bot.event
async def on_raw_reaction_add(payload):
    if payload.message_id != getattr(bot, "embed_id", None):
        return
    
    guild = bot.get_guild(payload.guild_id)
    channel = await bot.fetch_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)
    member = guild.get_member(payload.user_id)
    emoji = str(payload.emoji)
    role = guild.get_role(role_map[emoji])

    if member.bot:
        return

    if emoji not in role_map:
        return

    await member.remove_roles(*[guild.get_role(r) for r in role_map.values()])

    for reaction in message.reactions:
        async for user in reaction.users():
            if user.id != bot.user.id:
                await reaction.remove(user)

    await member.add_roles(role)

@bot.event
async def on_raw_reaction_remove(payload):
    if payload.message_id != getattr(bot, "embed_id", None):
        return

    guild = bot.get_guild(payload.guild_id)
    member = guild.get_member(payload.user_id)
    emoji = str(payload.emoji)
    role = guild.get_role(role_map[emoji])

    if emoji not in role_map:
        return

    await member.remove_roles(role)

@bot.tree.command(name = "send", description = "Sends a message")
@app_commands.describe(
    text = "Sends a text message",
    url = "Sends a video from a link",
    reply_id = "ID of the message that will be replied to",
    file_name = "Name of the video file"
)
async def send_command(interaction: discord.Interaction, text: str = "", url: str = None, reply_id: str = None, file_name: str = "video"):
    await interaction.response.defer(ephemeral = True)

    if text == None and url == None:
        return await interaction.followup.send("No input", ephemeral = True)

    filename = f"{file_name}.mp4"

    if reply_id:
        reply = await interaction.channel.fetch_message(int(reply_id))
    else:
        reply = None

    ydl_opts = {
        "outtmpl": filename, 
        "cookiefile": "cookies.txt",
        "format": "best[ext=mp4]",
        "merge_output_format": "mp4"
    }

    if url != None:
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            await interaction.channel.send(
                content = f"{text} <{url}>",
                file = discord.File(filename),
                reference = reply
            )

            os.remove(filename)

        except Exception as e:
            await interaction.channel.send(
            content = f"Failed to download video: `{e}`"
        )

    else:
        await interaction.channel.send(
        content = f"{text}",
        reference = reply
    )

    await interaction.followup.send("Done", ephemeral = True)

bot.run(TOKEN)