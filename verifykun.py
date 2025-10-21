import os
import random
import string
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

# ==== 環境変数 ====
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# ==== Bot設定 ====
intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ==== ボタン認証 ====
class VerifyButtonView(discord.ui.View):
    def __init__(self, role_id):
        super().__init__(timeout=None)
        self.role_id = role_id

    @discord.ui.button(label="✅ Verify", style=discord.ButtonStyle.green)
    async def verify(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = interaction.guild.get_role(self.role_id)
        if not role:
            await interaction.response.send_message("⚠️ ロールが見つかりません。", ephemeral=True)
            return

        if role in interaction.user.roles:
            await interaction.response.send_message("✅ すでに認証済みです！", ephemeral=True)
        else:
            await interaction.user.add_roles(role)
            await interaction.response.send_message("🎉 認証に成功しました！", ephemeral=True)

# ==== 簡易CAPTCHA認証 ====
class CaptchaView(discord.ui.View):
    def __init__(self, role_id):
        super().__init__(timeout=None)
        self.role_id = role_id
        self.codes = {}

    @discord.ui.button(label="🧩 認証を開始", style=discord.ButtonStyle.blurple)
    async def start_captcha(self, interaction: discord.Interaction, button: discord.ui.Button):
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
        self.codes[interaction.user.id] = code
        await interaction.response.send_message(
            f"🔒 以下の5文字を入力してください：\n`{code}`",
            ephemeral=True
        )

    @discord.ui.button(label="💬 コードを送信", style=discord.ButtonStyle.green)
    async def verify_captcha(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in self.codes:
            await interaction.response.send_message("🕓 まず『認証を開始』を押してください！", ephemeral=True)
            return

        def check(msg):
            return msg.author == interaction.user and isinstance(msg.channel, discord.DMChannel)

        await interaction.user.send("💬 ここにコードを入力してください！")
        await interaction.response.send_message("📩 DMを確認してください。", ephemeral=True)

        try:
            msg = await bot.wait_for("message", timeout=60, check=check)
            if msg.content.strip().upper() == self.codes[interaction.user.id]:
                role = interaction.guild.get_role(self.role_id)
                if role:
                    await interaction.user.add_roles(role)
                    await interaction.user.send("✅ 認証に成功しました！")
                else:
                    await interaction.user.send("⚠️ ロールが見つかりません。")
            else:
                await interaction.user.send("❌ コードが違います。もう一度試してください。")
        except:
            await interaction.user.send("⌛ 時間切れです。もう一度『認証を開始』を押してください。")

# ==== コマンド ====
@bot.tree.command(name="sendverify", description="認証パネルを送信します。")
@app_commands.describe(
    channel="送信先チャンネル",
    role="認証時に付与するロール",
    title="パネルのタイトル",
    description="説明文",
    type="認証タイプ（button または captcha）"
)
async def sendverify(interaction: discord.Interaction, channel: discord.TextChannel, role: discord.Role, title: str, description: str, type: str):
    type = type.lower()
    if type not in ["button", "captcha"]:
        await interaction.response.send_message("❌ type は `button` または `captcha` を指定してください。", ephemeral=True)
        return

    embed = discord.Embed(title=title, description=description, color=discord.Color.blue())
    embed.set_footer(text="Verification System")

    view = VerifyButtonView(role.id) if type == "button" else CaptchaView(role.id)
    await channel.send(embed=embed, view=view)
    await interaction.response.send_message(f"✅ {type.capitalize()} 認証パネルを {channel.mention} に送信しました。", ephemeral=True)

# ==== 起動 ====
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    try:
        await bot.tree.sync()
        print("🌍 Synced global commands.")
    except Exception as e:
        print(f"⚠️ Sync error: {e}")

bot.run(TOKEN)
