import discord
import json
from discord.ext import commands
# import asyncio
from PIL import Image, ImageDraw, ImageFont
import textwrap
import yt_dlp
import asyncio
import os
# import yt_dlp


# config
file = open('config.json', 'r')
config = json.load(file)
intents = discord.Intents.all()
intents.messages = True
bot = commands.Bot(config['prefix'], intents=intents)


@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')


@bot.command(name='ping')
async def ping(ctx):
    await ctx.send(f'{ctx.author.mention} pong!')
    print(f"ping by: {ctx.author.mention}")


@bot.command(name='foo')
async def foo(ctx: commands.context):
    await ctx.send(embed=discord.Embed(title=f'{ctx.message.content}'))
    print(f"foo by: {ctx.author.mention}")


@bot.event
async def on_member_join(member):
    welcome_message = """Welcome, {username}!"""
    text = "Welcome, {username}.   Enjoy your stay!".format(username=member.name)

    for channel in member.guild.channels:
        if str(channel) == "welcome":
            # Send the welcome message
            await channel.send(welcome_message.format(username=member.mention))
            # Open the background image
            background_image = Image.open("background.jpg")
            # Resize the background image to fit the desired dimensions
            background_image = background_image.resize((900, 400))
            # Create a new image with the background image
            image = Image.new("RGB", background_image.size)
            image.paste(background_image)
            draw = ImageDraw.Draw(image)
            # Choose a font and size
            font = ImageFont.truetype("PoetsenOne-Regular.ttf", 65)
            # Wrap the text to fit within the image dimensions
            lines = textwrap.wrap(text, width=20)
            # Calculate the total height of the text
            total_height = sum(draw.textbbox((0, 0), line, font=font)[3] for line in lines)
            # Center the text vertically
            y_text = (image.height - total_height) // 2
            # Draw the wrapped text on the image
            for line in lines:
                text_width, text_height = draw.textbbox((0, 0), line, font=font)[2:4]
                x_text = (image.width - text_width) // 2
                draw.text((x_text, y_text), line, font=font, fill="white")
                y_text += text_height
            # Save the image
            image_path = "genimgtest.png"
            image.save(image_path)
            # Send the image to the Discord channel
            await channel.send(file=discord.File(image_path))
            print(f"genimgtest by: {member.mention}")
            break
    print(f"welcomed user")


@bot.command(name='poll')
async def poll(ctx, question, *options):
    if len(options) < 2:
        error_msg2 = await ctx.send("You need to provide at least two options.")
        await asyncio.sleep(5)  # Wait for 5 seconds
        await error_msg2.delete()
        await ctx.message.delete()  # Delete the original command message
        return
    
    if len(options) > 5:
        error_msg5 = await ctx.send("You can provide up to five options.")
        await asyncio.sleep(5)
        await error_msg5.delete()
        await ctx.message.delete
        return

    options_text = "\n".join([f"{index+1}. {option}" for index, option in enumerate(options)])
    poll_message = await ctx.send(f"{question}\n{options_text}")
    print(f"poll by: {ctx.author.mention}")
    emojis = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣']
    for emoji, option in zip(emojis, options):
        await poll_message.add_reaction(emoji)


@bot.command(name='genimgtest')
async def generate_image(ctx, *, text):
    # Open the background image
    background_image = Image.open("background.jpg")
    
    # Resize the background image to fit the desired dimensions
    background_image = background_image.resize((900, 400))
    
    # Create a new image with the background image
    image = Image.new("RGB", background_image.size)
    image.paste(background_image)
    draw = ImageDraw.Draw(image)

    # Choose a font and size
    font = ImageFont.truetype("PoetsenOne-Regular.ttf", 65)

    # Wrap the text to fit within the image dimensions
    lines = textwrap.wrap(text, width=20)

    # Calculate the total height of the text
    total_height = sum(draw.textbbox((0, 0), line, font=font)[3] for line in lines)

    # Center the text vertically
    y_text = (image.height - total_height) // 2

    # Draw the wrapped text on the image
    for line in lines:
        text_width, text_height = draw.textbbox((0, 0), line, font=font)[2:4]
        x_text = (image.width - text_width) // 2
        draw.text((x_text, y_text), line, font=font, fill="white")
        y_text += text_height

    # Save the image
    image_path = "genimgtest.png"
    image.save(image_path)

    # Send the image to the Discord channel
    await ctx.send(file=discord.File(image_path))
    print(f"genimgtest by: {ctx.author.mention}")


queued_tracks = []
currently_playing = None  # Initialize currently_playing to None


@bot.command(name='play')
async def play(ctx, url):
    global currently_playing  # Declare currently_playing as global
    voice_client = ctx.voice_client
    if not voice_client:
        voice_channel = ctx.author.voice.channel
        if voice_channel is None:
            return await ctx.send("You need to be in a voice channel to play music!")
        await voice_channel.connect()
        voice_client = ctx.voice_client

    # Clean up previously downloaded file
    if currently_playing:
        if hasattr(currently_playing, 'filename') and os.path.exists(currently_playing.filename):
            os.remove(currently_playing.filename)
        currently_playing = None
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': '%(title)s.%(ext)s',  # Use a unique filename for each track
        'verbose': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            source = discord.FFmpegPCMAudio(filename)
            if voice_client.is_playing():
                voice_client.stop()
            voice_client.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(delete_and_play_next(ctx, voice_client, source), bot.loop))
            await ctx.send(f"Now playing: {info.get('title', url)}")
            currently_playing = source
        except yt_dlp.utils.DownloadError as e:
            print(e)
            await ctx.send(f"Error: {e}")


async def delete_and_play_next(ctx, voice_client, source):
    try:
        os.remove(source.filename)
    except Exception as e:
        print(f"Error deleting file: {e}")
    global currently_playing  # Declare currently_playing as global
    currently_playing = None


@bot.command(name='skip')
async def skip(ctx):
    voice_client = ctx.voice_client
    if voice_client and voice_client.is_playing():
        voice_client.stop()
        await play(ctx, voice_client)
    else:
        await ctx.send("No audio is currently playing.")
# run bot
bot.run(config['token'])
