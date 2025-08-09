import json
import requests
from threading import Thread
from flask import Flask, request
import discord
from discord import app_commands

# 여기 아까 준 정보 그대로 넣음 (실사용 절대 권장 안 함)
TOKEN = "MTQwMzU1NjM5Nzg4NjYwNzQ3MQ.GCNdJM.oB4226ypucj4uPhCSYOm0q0FZWrdbwWW3B_42E"
CLIENT_ID = "1403556397886607471"
CLIENT_SECRET = "yUrfPuOh93nz4cCJvZIbMjE071my660Q"
REDIRECT_URI = "https://verify.com/callback"  # 너가 말한 주소

USER_FILE = "users.json"

app = Flask(__name__)

@app.route("/callback")
def callback():
    code = request.args.get("code")
    if not code:
        return "❌ 인증 실패: code가 없습니다."

    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "scope": "identify guilds.join"
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    token_res = requests.post("https://discord.com/api/oauth2/token", data=data, headers=headers)
    if token_res.status_code != 200:
        return f"❌ 토큰 발급 실패: {token_res.text}"

    token_json = token_res.json()
    access_token = token_json.get("access_token")
    if not access_token:
        return "❌ 액세스 토큰이 없습니다."

    user_res = requests.get("https://discord.com/api/users/@me", headers={"Authorization": f"Bearer {access_token}"})
    if user_res.status_code != 200:
        return f"❌ 사용자 정보 조회 실패: {user_res.text}"

    user_json = user_res.json()
    user_id = user_json["id"]

    try:
        with open(USER_FILE, "r", encoding="utf-8") as f:
            users = json.load(f)
    except FileNotFoundError:
        users = {}

    users[user_id] = access_token
    with open(USER_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=4)

    return "✅ 승인 완료! 디스코드로 돌아가 /컴온 명령어를 사용하세요."

intents = discord.Intents.default()
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

@bot.event
async def on_ready():
    print(f"봇 실행됨: {bot.user}")
    await tree.sync()

@tree.command(name="버튼")
async def send_oauth_button(interaction: discord.Interaction):
    oauth_url = (
        f"https://discord.com/oauth2/authorize"
        f"?client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=identify%20guilds.join"
    )
    view = discord.ui.View()
    button = discord.ui.Button(label="나 대신 서버에 참여하기", url=oauth_url)
    view.add_item(button)
    await interaction.response.send_message("아래 버튼 눌러 서버 참여를 승인하세요.", view=view)

@tree.command(name="컴온")
async def invite_users(interaction: discord.Interaction):
    try:
        with open(USER_FILE, "r", encoding="utf-8") as f:
            users = json.load(f)
    except FileNotFoundError:
        return await interaction.response.send_message("승인한 사용자가 없습니다.")

    guild_id = interaction.guild.id
    success_count = 0
    fail_count = 0

    for user_id, access_token in users.items():
        url = f"https://discord.com/api/guilds/{guild_id}/members/{user_id}"
        headers = {
            "Authorization": f"Bot {TOKEN}",
            "Content-Type": "application/json"
        }
        json_data = {"access_token": access_token}
        res = requests.put(url, json=json_data, headers=headers)

        if res.status_code in (200, 201, 204):
            success_count += 1
        else:
            fail_count += 1

    await interaction.response.send_message(f"✅ {success_count}명 초대 완료, 실패 {fail_count}명")

def run_flask():
    app.run(host="0.0.0.0", port=int( os.environ.get("PORT", 5000) ))

def run_bot():
    bot.run(TOKEN)

if __name__ == "__main__":
    Thread(target=run_flask).start()
    run_bot()
