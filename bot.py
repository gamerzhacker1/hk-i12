import discord
from discord.ext import commands
import json
import os
import random

TOKEN = "BOT_TOKEN"
DATA_FILE = "vps_users.json"
TEXT_FILE = "texts.json"
ADMIN_IDS = [1159037240622723092]  # replace with your admin user ID(s)

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

def load_data():
    return json.load(open(DATA_FILE)) if os.path.exists(DATA_FILE) else {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def load_texts():
    return json.load(open(TEXT_FILE)) if os.path.exists(TEXT_FILE) else {}

def save_texts(data):
    with open(TEXT_FILE, "w") as f:
        json.dump(data, f, indent=2)

class VPSManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    
    @app_commands.command(name="create-vps", description="Create a VPS with SSH using tmate and playit.gg")
    async def create_vps(self, interaction: discord.Interaction):
        await interaction.response.defer()
        user_id = str(interaction.user.id)

        password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        hostname = f"vps-{random.randint(1000,9999)}"

        try:
            tmate_proc = subprocess.Popen(["tmate", "-F"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            playit_proc = subprocess.Popen(["./playit-linux-amd64"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            await asyncio.sleep(5)

            ip, port = "N/A", "N/A"
            for line in playit_proc.stdout:
                if "Forwarding TCP" in line:
                    ip_port = line.strip().split()[3]
                    ip, port = ip_port.split(":")
                    break

            msg = (
                f"⚙️ Creating your VPS...

"
                f"🔐 **SSH Details:**
"
                f"IP: `{ip}`
"
                f"Port: `{port}`
"
                f"User: `root`
"
                f"Pass: `{password}`
"
                f"Hostname: `{hostname}`
"
                f"Forwarded via: `playit.gg`"
            )

            # Save data
            data = load_data()
            data[user_id] = {
                "ip": ip,
                "port": port,
                "user": "root",
                "pass": password,
                "hostname": hostname
            }
            save_data(data)

            await interaction.user.send(msg)
            await interaction.followup.send("✅ VPS created. Details sent in DM.")

        except Exception as e:
            await interaction.followup.send(f"❌ Error: {str(e)}")

@bot.command()
async def myvps(ctx):
    uid = str(ctx.author.id)
    data = load_data()
    index, found, msg = 1, False, ""

    for owner, user_data in data.items():
        for vps in user_data.get("vps", []):
            if owner == uid or uid in user_data.get("shared_with", []):
                msg += f"**#{index} VPS (Owner: {owner})**\nHostname: `{vps['hostname']}`\nIP: `{vps['ip']}` Port: `{vps['port']}`\nRAM: `{vps['ram']}` Status: `{vps['status']}` OS: `{vps['os']}`\n\n"
                found = True
                index += 1
    await ctx.send(msg if found else "❌ You have no VPS or shared VPS.")

@bot.command()
async def start(ctx, vps_number: int): await change_status(ctx, vps_number, "running")
@bot.command()
async def stop(ctx, vps_number: int): await change_status(ctx, vps_number, "stopped")

async def change_status(ctx, vps_number, new_status):
    uid = str(ctx.author.id)
    data = load_data()
    index = 1
    for owner, user_data in data.items():
        for vps in user_data["vps"]:
            if owner == uid or uid in user_data["shared_with"]:
                if index == vps_number:
                    vps["status"] = new_status
                    save_data(data)
                    await ctx.send(f"✅ VPS #{vps_number} is now `{new_status}`.")
                    return
                index += 1
    await ctx.send("❌ VPS not found.")

@bot.command()
async def reinstall(ctx, vps_number: int, os_name: str):
    if os_name not in ["Ubuntu-22.04", "Debian-12"]:
        await ctx.send("❌ OS must be 'Ubuntu-22.04' or 'Debian-12'.")
        return

    uid = str(ctx.author.id)
    data = load_data()
    index = 1
    for owner, user_data in data.items():
        for vps in user_data["vps"]:
            if owner == uid or uid in user_data["shared_with"]:
                if index == vps_number:
                    vps["os"] = os_name
                    save_data(data)
                    await ctx.send(f"✅ VPS #{vps_number} reinstalled with `{os_name}`.")
                    return
                index += 1
    await ctx.send("❌ VPS not found.")

@bot.command()
async def share(ctx, owner_id: str, target_id: str):
    data = load_data()
    if owner_id in data:
        if target_id not in data[owner_id]["shared_with"]:
            data[owner_id]["shared_with"].append(target_id)
            save_data(data)
            await ctx.send("✅ VPS shared.")
        else:
            await ctx.send("⚠️ Already shared.")
    else:
        await ctx.send("❌ Owner not found.")

@bot.command()
async def unshare(ctx, owner_id: str, target_id: str):
    data = load_data()
    if owner_id in data and target_id in data[owner_id]["shared_with"]:
        data[owner_id]["shared_with"].remove(target_id)
        save_data(data)
        await ctx.send("❌ Removed shared access.")
    else:
        await ctx.send("❌ Not shared or invalid.")

@bot.command()
async def list(ctx):
    if ctx.author.id not in ADMIN_IDS:
        await ctx.send("❌ Admin only.")
        return
    data = load_data()
    msg = "\n".join([f"User: {uid} - VPSs: {len(data[uid].get('vps', []))} - Location: in" for uid in data])
    await ctx.send(msg or "No users found.")

@bot.command()
async def adminadd(ctx, uid: int):
    if ctx.author.id not in ADMIN_IDS:
        await ctx.send("❌ Only admins can use this.")
        return
    if uid not in ADMIN_IDS:
        ADMIN_IDS.append(uid)
        await ctx.send(f"✅ User `{uid}` added as admin.")
    else:
        await ctx.send("⚠️ Already admin.")

@bot.command()
async def role(ctx, uid: str):
    data = load_data()
    vps_count = len(data.get(uid, {}).get("vps", []))
    await ctx.send(f"👤 User `{uid}` has `{vps_count}` VPS.")

@bot.command()
async def create_text(ctx, name: str, *, message: str):
    if ctx.author.id not in ADMIN_IDS:
        await ctx.send("❌ Admin only.")
        return
    texts = load_texts()
    texts[name] = message
    save_texts(texts)
    await ctx.send(f"✅ Saved text `{name}`.")

@bot.command()
async def text(ctx, name: str):
    texts = load_texts()
    await ctx.send(texts.get(name, "❌ Text not found."))

@bot.command()
async def ping(ctx):
    await ctx.send(f"🏓 Pong! `{round(bot.latency * 1000)}ms`")

bot.run(TOKEN)
