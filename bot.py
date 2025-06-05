import discord
from discord.ext import commands
from discord import app_commands
import subprocess
import asyncio
import json
import os

TOKEN = "YOUR_BOT_TOKEN"  # Replace with your bot token
ADMIN_ID = "1159037240622723092"
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="/", intents=intents)
tree = bot.tree

# JSON data files
USERS_FILE = "vps_data.json"
ROLES_FILE = "roles.json"
TEXTS_FILE = "texts.json"
SHARE_FILE = "share.json"

# JSON helpers
def load_json(file):
    if not os.path.exists(file): return {}
    with open(file, 'r') as f: return json.load(f)

def save_json(file, data):
    with open(file, 'w') as f: json.dump(data, f, indent=4)

@bot.event
async def on_ready():
    await tree.sync()
    print(f"✅ Bot ready as {bot.user}")

@tree.command(name="ping", description="Check bot latency")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"Pong! `{round(bot.latency * 1000)}ms`")

@tree.command(name="adminadd", description="Make user admin")
async def adminadd(interaction: discord.Interaction, userid: str):
    roles = load_json(ROLES_FILE)
    roles[userid] = "admin"
    save_json(ROLES_FILE, roles)
    await interaction.response.send_message(f"✅ <@{userid}> promoted to admin.")

@tree.command(name="role", description="Set user role")
async def role(interaction: discord.Interaction, userid: str, role: str):
    roles = load_json(ROLES_FILE)
    roles[userid] = role
    save_json(ROLES_FILE, roles)
    await interaction.response.send_message(f"✅ Role set: <@{userid}> = `{role}`")


@tree.command(name="create_vps", description="⚙️ Creating Your VPS...")
async def create_vps(ctx):
    if not is_admin(ctx.author.id):
        return await ctx.send("❌ Only admins can use this command.")
    
    await ctx.send("⚙️ Creating Your VPS...")

    # Run tmate and capture SSH
    try:
        proc = subprocess.Popen(["tmate", "-F"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate(timeout=10)
        if proc.returncode != 0:
            await ctx.send(f"❌ Error: {stderr.decode()}")
            return

        ssh_line = next((line for line in stdout.decode().split("\\n") if line.strip().startswith("ssh")), "Unknown")

        user_data = load_data()
        user_data[str(ctx.author.id)] = {
            "ssh": ssh_line,
            "os": "Ubuntu 22.04",
            "password": "root"
        }
        save_data(user_data)

        await ctx.author.send(
            f"✅ Successfully created Instance\\n"
            f"**SSH Session Command:**\\n```{ssh_line}```\\n"
            f"OS: Ubuntu 22.04\\nPassword: root"
        )
        await ctx.send("✅ VPS details sent to your DM.")
    except Exception as e:
        await ctx.send(f"❌ Exception: {e}")

@tree.command(name="myvps", description="Show your VPS info")
async def myvps(interaction: discord.Interaction):
    data = load_json(USERS_FILE)
    uid = str(interaction.user.id)
    if uid not in data:
        await interaction.response.send_message("❌ You have no VPS.")
        return
    v = data[uid]
    msg = f"""🔍 **Your VPS Info**
**SSH:** `{v['ssh']}`
**IP:** `{v['ip']}` | **Port:** `{v['port']}`
**Hostname:** `{v['hostname']}`
**RAM:** {v['ram']} | **CPU:** {v['cpu']} | **Disk:** {v['disk']}
**Location:** {v['location']}"""
    await interaction.response.send_message(msg)

@tree.command(name="port_add", description="Forward local port using Playit")
async def port_add(interaction: discord.Interaction, localport: int):
    await interaction.response.defer()
    try:
        playit_proc = subprocess.Popen(["./playit-linux-amd64"], stdout=subprocess.PIPE, text=True)
        await asyncio.sleep(6)
        for line in playit_proc.stdout:
            if f"127.0.0.1:{localport}" in line:
                msg = f"✅ Port `{localport}` forwarded to: `{line.split(' -> ')[1].strip()}`"
                await interaction.followup.send(msg)
                return
        await interaction.followup.send("❌ No match found.")
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {str(e)}")

@tree.command(name="create_list", description="Save VPS as list name")
async def create_list(interaction: discord.Interaction, name: str):
    data = load_json(USERS_FILE)
    uid = str(interaction.user.id)
    if uid not in data:
        await interaction.response.send_message("❌ No VPS found.")
        return
    ssh = data[uid]["ssh"]
    os.makedirs("ssh_lists", exist_ok=True)
    with open(f"ssh_lists/{name}.txt", "w") as f:
        f.write(ssh)
    await interaction.response.send_message(f"✅ List `{name}` saved.")

@tree.command(name="node", description="Show VPS Node Info")
async def node(interaction: discord.Interaction):
    await interaction.response.send_message("📡 Node: `IN`\nRAM: 2GB | CPU: 1 Core | Disk: 10GB\n🛠️ Made by Gamerzhacker")

@tree.command(name="nodeadmin", description="Show all VPS info (admin)")
async def nodeadmin(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Admins only.")
        return
    data = load_json(USERS_FILE)
    msg = "**🔐 All VPS:**\n"
    for uid, v in data.items():
        msg += f"<@{uid}> — {v['location']}\n"
    await interaction.response.send_message(msg)

@tree.command(name="list", description="Show all users and location")
async def list_users(interaction: discord.Interaction):
    data = load_json(USERS_FILE)
    msg = "**👥 Users:**\n"
    for uid, v in data.items():
        msg += f"<@{uid}> | {v['location']}\n"
    await interaction.response.send_message(msg)

@tree.command(name="share", description="Share VPS with another user")
async def share(interaction: discord.Interaction, targetid: str):
    uid = str(interaction.user.id)
    shared = load_json(SHARE_FILE)
    if uid not in shared:
        shared[uid] = []
    if targetid not in shared[uid]:
        shared[uid].append(targetid)
        save_json(SHARE_FILE, shared)
        await interaction.response.send_message(f"✅ VPS shared with <@{targetid}>.")
    else:
        await interaction.response.send_message("❌ Already shared.")

@tree.command(name="create-text", description="Create or get text (admin only)")
async def create_text(interaction: discord.Interaction, name: str, msg: str = None):
    texts = load_json(TEXTS_FILE)
    if msg:  # create mode
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Admin only.")
            return
        texts[name] = msg
        save_json(TEXTS_FILE, texts)
        await interaction.response.send_message(f"✅ Text `{name}` saved.")
    else:  # get mode
        if name not in texts:
            await interaction.response.send_message("❌ Not found.")
            return
        await interaction.response.send_message(f"📄 **{name}:** {texts[name]}")
@tree.command(name="port_add", description="Forward local port using playit.gg")
    async def port_add(self, interaction: discord.Interaction, localport: int):
        await interaction.response.defer()
        try:
            proc = subprocess.Popen(["./playit-linux-amd64"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            await asyncio.sleep(6)
            msg = "❌ Could not find forwarded port."
            for line in proc.stdout:
                if f"127.0.0.1:{localport}" in line:
                    msg = f"✅ Port `{localport}` forwarded to: `{line.split(' -> ')[1].strip()}`"
                    break
            await interaction.followup.send(msg)
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {str(e)}")

bot.run(TOKEN)
