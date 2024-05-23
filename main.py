import discord
import json
from discord.ext import commands
# import asyncio
from PIL import Image, ImageDraw, ImageFont
import textwrap
import yt_dlp
import asyncio
import os
import glob

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
    await bot.tree.sync()


@bot.command(name='ping', help='Ping bot')
async def ping(ctx):
    await ctx.send(f'{ctx.author.mention} pong!')
    print(f"ping by: {ctx.author.mention}")


@bot.command(name='foo', help='Repeat your message in chat\n\nArguments:\nmessage: message to be repeated')
async def foo(ctx: commands.context, *, message: str):
    await ctx.send(embed=discord.Embed(title=message))
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


@bot.command(name='poll', help='Poll in chat\n\nArguments:\nquestion Question in poll.\noptions Options to be selected (up to five)')
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

    options_text = "\n".join([f"{index + 1}. {option}" for index, option in enumerate(options)])
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


current_file_path = os.path.dirname(os.path.abspath(__file__))
song_dir = os.path.join(current_file_path, 'songs')
os.makedirs(song_dir, exist_ok=True)

queued_tracks = []
currently_playing = None  # Initialize currently_playing to None


@bot.command(name='play', help='Play song in voice chat\n\nArguments:\nurl YouTube URL to video that will be played in voice chat')
@commands.has_any_role('Moderator', 'Admin', 'Music')
async def play(ctx, url):
    global currently_playing  # Declare currently_playing as global
    voice_client = ctx.voice_client
    if not voice_client:
        voice_channel = ctx.author.voice.channel
        if voice_channel is None:
            return await ctx.send("You need to be in a voice channel to play music!")
        await voice_channel.connect()
        voice_client = ctx.voice_client

    # Clear all .m4a files from the songs directory, except the currently playing file
    m4a_files = glob.glob(os.path.join(song_dir, '*.webm'))
    try:
        for m4a_file in m4a_files:
            if currently_playing == m4a_file:
                continue
            os.remove(m4a_file)
    except Exception as e:
        print(f"{e}")

    # Clean up previously downloaded file
    if currently_playing:
        if hasattr(currently_playing, 'filename') and os.path.exists(currently_playing.filename):
            os.remove(currently_playing.filename)
        currently_playing = None

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(song_dir, '%(title)s.%(ext)s'),  # Use a unique filename for each track
        'verbose': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            source = discord.FFmpegPCMAudio(filename)
            if voice_client.is_playing():
                voice_client.stop()
            voice_client.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(
                delete_and_play_next(ctx, voice_client, source), bot.loop))
            await ctx.send(f"Now playing: {info.get('title', url)}")
            currently_playing = source
        except yt_dlp.utils.DownloadError as e:
            print(e)
            await ctx.send(f"Error: {e}")


async def delete_and_play_next(ctx, voice_client, source):
    try:
        if hasattr(source, 'info') and 'title' in source.info:
            filename = os.path.join(song_dir, f"{source.info['title']}.{source.info['ext']}")
            if os.path.exists(filename):
                os.remove(filename)
    except Exception as e:
        print(f"Error deleting file: {e}")
    global currently_playing
    currently_playing = None


@bot.command(name='skip', help='Skip current playing song')
@commands.has_any_role('Moderator', 'Admin', 'Music')
async def skip(ctx):
    print(f"current song skipped by: {ctx.author.mention}")
    voice_client = ctx.voice_client
    if voice_client and voice_client.is_playing():
        voice_client.stop()
        try:
            await play(ctx, voice_client)
        except Exception as e:
            print(f"Error while skipping song: {e}")
            await ctx.send(f"DEBUG: {e}")
    else:
        await ctx.send("No audio is currently playing.")


# Command to ban a member
@bot.command(name='ban', help='Ban user from server\n\nArguments:\nmember Member to be banned\n reason Reason of ban')
@commands.has_any_role('Moderator', 'Admin')
async def ban(ctx, member: discord.Member, *, reason=None):
    try:
        await member.ban(reason=reason)
        await ctx.send(f'Banned: {member.mention}')
    except Exception as e:
        print(f"Error while banning user, error {e}")
        await ctx.send(f'Error while banning user, error {e}')
    except:
        print(f"Error while banning user, error")
        await ctx.send(f'Error while banning user, error')


# Command to mute a member
@bot.command(name='mute', help='Mute user\n\nArguments:\nmember Member to be muted')
@commands.has_any_role('Moderator', 'Admin')
async def mute(ctx, member: discord.Member):
    muted_role = discord.utils.get(ctx.guild.roles, name="Muted")  # Ensure you have a role named "Muted"
    try:
        await member.add_roles(muted_role)
        await ctx.send(f'Muted: {member.mention}')
    except Exception as e:
        print(f"Error while muting user, error {e}")
        await ctx.send(f'Error while muting user, error {e}')
    except:
        print(f"Error while muting user, error")
        await ctx.send(f'Error while muting user, error')


# Command to kick a member
@bot.command(name='kick', help='Kick user from server\n\nArguments:\nmember Member to be kicked\nreason Reason of Kicking')
@commands.has_any_role('Moderator', 'Admin')
async def kick(ctx, member: discord.Member, *, reason=None):
    try:
        await member.kick(reason=reason)
        await ctx.send(f'Kicked: {member.mention}')
    except Exception as e:
        print(f"Error while kicking user, error {e}")
        await ctx.send(f'Error while kicking user, error {e}')
    except:
        print(f"Error while kicking user, error")
        await ctx.send(f'Error while kicking user, error')


# Command to unmute a member
@bot.command(name='unmute', help='Unmute a user\n\nArguments:\nmember Member to be unmuted')
@commands.has_any_role('Moderator', 'Admin')
async def unmute(ctx, member: discord.Member):
    muted_role = discord.utils.get(ctx.guild.roles, name="Muted")  # Ensure you have a role named "Muted"
    try:
        await member.remove_roles(muted_role)
        await ctx.send(f'{member.mention} has been unmuted.')
    except Exception as e:
        print(f"Error while unmuting user, error {e}")
        await ctx.send(f'Error while unmuting user, error {e}')
    except:
        print(f"Error while unmuting user, error")
        await ctx.send(f'Error while unmuting user, error')


# Command to unban a member
@bot.command(name='unban', help='Unban user\n\nArguments:\nmember Member to be unbanned')
@commands.has_any_role('Moderator', 'Admin')
async def unban(ctx, *, member):
    banned_users = await ctx.guild.fetch_bans()
    member_name, member_discriminator = member.split('#')
    try:
        for ban_entry in banned_users:
            user = ban_entry.user

            if (user.name, user.discriminator) == (member_name, member_discriminator):
                await ctx.guild.unban(user)
                await ctx.send(f'{user.mention} has been unbanned.')
                return
    except Exception as e:
        print(f"Error while unbanning user, error {e}")
        await ctx.send(f'Error while unbanning user, error {e}')
    except:
        print(f"Error while unbanning user, error")
        await ctx.send(f'Error while unbanning user, error')

    await ctx.send(f'Could not find {member} in the ban list.')


@bot.command(name='purge', help='Deletes amount of messages from channel\n\nArguments:\namount Amount of messages to be deleted')
@commands.has_permissions(manage_messages=True)
async def purge(ctx, amount: int):
    """Deletes a specified number of messages from the current channel."""
    try:
        deleted = await ctx.channel.purge(limit=amount + 1)
        deleted_messages = len(deleted) - 1  # Exclude the command message
        await ctx.send(f"Deleted {deleted_messages} message(s).", delete_after=5)
    except discord.HTTPException as error:
        if error.code == 50034:
            await ctx.send("Cannot delete messages older than 14 days.", delete_after=5)
        else:
            await ctx.send(f"An error occurred: {error}", delete_after=5)


@purge.error
async def purge_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You do not have permission to use this command.", delete_after=5)
    elif isinstance(error, commands.BadArgument):
        await ctx.send("Please provide a valid number of messages to delete.", delete_after=5)

# run bot
bot.run(config['token'])
