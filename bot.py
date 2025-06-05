import discord
from discord.ext import commands
import subprocess
import json
import os
import asyncio

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='/', intents=intents)

TOKEN = ""
ADMIN_ID = "1159037240622723092"

# File paths
USER_DATA = 'vps_data.json'
SHARED = 'share.json'
TEXTS = 'texts.json'

# Ensure data files exist
for file in [USER_DATA, ADMINS, SHARED, TEXTS]:
    if not os.path.exists(file):
        with open(file, 'w') as f:
            json.dump({} if file != ADMINS else [], f)

def load_json(path):
    with open(path, 'r') as f:
        return json.load(f)

def save_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=4)

def is_admin(user_id):
    return str(user_id) in load_json(ADMINS)

@bot.event
async def on_ready():
    print(f'✅ Bot online as {bot.user}')

@bot.command()
async def ping(ctx):
    await ctx.send("🏓 Pong!")

@bot.command()
async def adminadd(ctx, user_id: str):
    if not is_admin(ctx.author.id):
        return await ctx.send("❌ Only admins can add admins.")
    admins = load_json(ADMINS)
    if user_id not in admins:
        admins.append(user_id)
        save_json(ADMINS, admins)
    await ctx.send(f"✅ {user_id} is now admin.")

@bot.command()
async def role(ctx, user_id: str):
    await ctx.send(f"🔰 Role set for user {user_id}. Only 1 VPS allowed unless admin.")

@bot.command()
async def create_vps(ctx):
    await ctx.send("⚙️ Creating Your VPS...")
    uid = str(ctx.author.id)
    data = load_json(USER_DATA)

    if not is_admin(uid) and uid in data:
        return await ctx.send("❌ You can only create 1 VPS.")

    try:
        proc = await asyncio.create_subprocess_shell("tmate -F", stdout=asyncio.subprocess.PIPE)
        stdout, _ = await proc.communicate()
        ssh_line = next((line for line in stdout.decode().splitlines() if line.startswith("ssh")), None)

        if ssh_line:
            data[uid] = {
                "ssh": ssh_line,
                "os": "Ubuntu 22.04",
                "password": "root",
                "ram": "2GB",
                "cpu": "1 Core",
                "disk": "10GB",
                "location": "in"
            }
            save_json(USER_DATA, data)
            await ctx.author.send(f"✅ VPS Created\nSSH: `{ssh_line}`\nOS: Ubuntu 22.04\nPassword: root")
            await ctx.send("✅ VPS details sent to your DM.")
        else:
            await ctx.send("❌ SSH not found.")
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

@bot.command()
async def myvps(ctx):
    data = load_json(USER_DATA).get(str(ctx.author.id))
    if not data:
        return await ctx.send("❌ You have no VPS.")
    msg = f"🔐 **Your VPS**\nSSH: `{data['ssh']}`\nRAM: {data['ram']}\nCPU: {data['cpu']}\nDisk: {data['disk']}\nOS: {data['os']}"
    await ctx.send(msg)

@bot.command()
async def list(ctx):
    if not is_admin(ctx.author.id):
        return await ctx.send("❌ Admins only.")
    data = load_json(USER_DATA)
    msg = "\\n".join([f"<@{uid}> - {v.get('location', 'unknown')}" for uid, v in data.items()])
    await ctx.send(f"📄 Users:\n{msg}")

@bot.command()
async def node(ctx):
    await ctx.send("📍 Location: in 🇮🇳\nRAM: 2GB\nCPU: 1 Core\nDisk: 10GB\nMade by: Gamerzhacker")

@bot.command()
async def nodeadmin(ctx):
    if not is_admin(ctx.author.id):
        return await ctx.send("❌ Admins only.")
    data = load_json(USER_DATA)
    msg = ""
    for uid, v in data.items():
        msg += f"<@{uid}> - {v['ssh']} - {v['location']}\\n"
    await ctx.send(f"🧾 All VPS:\n{msg}")

@bot.command()
async def share(ctx, userid_location: str):
    uid = str(ctx.author.id)
    shared = load_json(SHARED)
    if uid not in shared:
        shared[uid] = []
    shared[uid].append(userid_location)
    save_json(SHARED, shared)
    await ctx.send(f"✅ Shared with {userid_location}")

@bot.command()
async def create_text(ctx, name: str, *, message: str = None):
    if message:
        if not is_admin(ctx.author.id):
            return await ctx.send("❌ Only admins can create texts.")
        texts = load_json(TEXTS)
        texts[name] = message
        save_json(TEXTS, texts)
        await ctx.send(f"📝 Created text `{name}`.")
    else:
        texts = load_json(TEXTS)
        if name in texts:
            await ctx.send(f"📄 {texts[name]}")
        else:
            await ctx.send("❌ No such text.")

@bot.command()
async def port_add(ctx, port: int):
    await ctx.send(f"🔀 Forwarded local port {port} using Playit.gg")

@bot.command()
async def create_list(ctx, name: str):
    uid = str(ctx.author.id)
    data = load_json(USER_DATA)
    if uid not in data:
        return await ctx.send("❌ No VPS session.")
    if "lists" not in data[uid]:
        data[uid]["lists"] = []
    data[uid]["lists"].append({"name": name, "ssh": data[uid]["ssh"]})
    save_json(USER_DATA, data)
    await ctx.send(f"✅ Saved SSH session as `{name}`.")

bot.run(TOKEN)
