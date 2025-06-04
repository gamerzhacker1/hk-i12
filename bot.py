import discord
from discord.ext import commands
from discord import app_commands
import paramiko
import json
import os
from datetime import datetime

# CONFIG
TOKEN = "YOUR_BOT_TOKEN"
VPS_IP = "YOUR_VPS_IP"
VPS_ROOT_PASSWORD = "YOUR_VPS_PASSWORD"
BASE_PORT = 2200
DATA_FILE = "users.json"

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree
used_ports = set()
running_times = {}

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE) as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

@bot.event
async def on_ready():
    await tree.sync()
    print("Bot is ready")

@tree.command(name="create-vps", description="Create a new VPS user")
@app_commands.describe(
    hostname="Your hostname (e.g., myserver)",
    ram="Amount of RAM (e.g., 2GB)",
    password="Password for SSH user"
)
async def create_vps(interaction: discord.Interaction, hostname: str, ram: str, password: str):
    user_id = str(interaction.user.id)
    username = hostname.lower()
    port = BASE_PORT + len(load_data())
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(VPS_IP, username='root', password=VPS_ROOT_PASSWORD)
        commands = f"""
        useradd -m {username}
        echo '{username}:{password}' | chpasswd
        cp /etc/ssh/sshd_config /etc/ssh/sshd_config.bak
        echo 'Port {port}' >> /etc/ssh/sshd_config
        echo -e 'Match User {username}\n    AllowTcpForwarding yes\n    X11Forwarding yes' >> /etc/ssh/sshd_config
        systemctl restart ssh
        """
        ssh.exec_command(commands)
        ssh.close()

        data = load_data()
        data[user_id] = {"username": username, "port": port, "password": password, "hostname": hostname, "ram": ram}
        save_data(data)

        await interaction.response.send_message("✅ VPS details sent to your DM!", ephemeral=True)
        await interaction.user.send(
            f"✅ **VPS Created Successfully!**\n\n"
            f"🔹 **IP**: `{VPS_IP}`\n"
            f"🔹 **Port**: `{port}`\n"
            f"🔹 **User**: `{username}`\n"
            f"🔹 **Pass**: `{password}`\n"
            f"🔹 **Hostname**: `{hostname}`\n"
            f"🔹 **RAM**: `{ram}`"
        )
    except Exception as e:
        await interaction.response.send_message(f"❌ Error: {str(e)}", ephemeral=True)

@tree.command(name="myvps", description="Manage your VPS")
async def myvps(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    data = load_data()
    if user_id not in data:
        await interaction.response.send_message("❌ You have not created a VPS yet!", ephemeral=True)
        return

    info = data[user_id]
    embed = discord.Embed(title="🖥️ Your VPS", description=f"**Hostname**: `{info['hostname']}`\n**Port**: `{info['port']}`", color=0x00ff00)
    if user_id in running_times:
        uptime = datetime.now() - running_times[user_id]
        embed.add_field(name="Status", value=f"🟢 Running\n⏱️ Uptime: {uptime}", inline=False)
    else:
        embed.add_field(name="Status", value="🔴 Stopped", inline=False)

    class ReinstallDropdown(discord.ui.Select):
        def __init__(self):
            options = [
                discord.SelectOption(label="Ubuntu-22.04", value="ubuntu"),
                discord.SelectOption(label="Debian-12", value="debian")
            ]
            super().__init__(placeholder="Choose OS", options=options)

        async def callback(self, interaction2):
            await reinstall_vps(info['username'], self.values[0])
            await interaction2.response.send_message(f"🔁 VPS reinstalled with {self.values[0]}", ephemeral=True)

    async def start_vps():
        running_times[user_id] = datetime.now()
        return "VPS started!"

    async def stop_vps():
        running_times.pop(user_id, None)
        return "VPS stopped!"

    view = discord.ui.View()

    @discord.ui.button(label="Start", style=discord.ButtonStyle.success)
    async def start_button(button, interaction2):
        msg = await start_vps()
        await interaction2.response.send_message(f"✅ {msg}", ephemeral=True)

    @discord.ui.button(label="Stop", style=discord.ButtonStyle.danger)
    async def stop_button(button, interaction2):
        msg = await stop_vps()
        await interaction2.response.send_message(f"⛔ {msg}", ephemeral=True)

    @discord.ui.button(label="Reinstall", style=discord.ButtonStyle.primary)
    async def reinstall_button(button, interaction2):
        dropdown = discord.ui.View()
        dropdown.add_item(ReinstallDropdown())
        await interaction2.response.send_message("Choose OS to reinstall:", view=dropdown, ephemeral=True)

    view.add_item(start_button)
    view.add_item(stop_button)
    view.add_item(reinstall_button)

    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

async def reinstall_vps(username, os_choice):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_IP, username='root', password=VPS_ROOT_PASSWORD)
    if os_choice == "ubuntu":
        reinstall_cmd = f"echo Reinstalling Ubuntu for {username}"
    else:
        reinstall_cmd = f"echo Reinstalling Debian for {username}"
    ssh.exec_command(reinstall_cmd)
    ssh.close()

bot.run(TOKEN)
