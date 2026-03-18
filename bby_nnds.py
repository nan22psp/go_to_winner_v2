"""
====================================================================================
🍀 WIN GO 30 SECONDS V2 (EXACT 4-PATTERN EDITION) 🍀
====================================================================================
Patterns Included:
1. BBBB -> BIG
2. SSSS -> SMALL
3. BBSS -> BIG
4. SSBB -> SMALL
5. SBSB -> SMALL
6. BSBS -> BIG
* Fallback: Follows the last trend if no pattern matched. (NO SKIP)
====================================================================================
"""

import asyncio
import time
import os
import logging
from collections import deque
from datetime import datetime
from typing import List, Optional
from dotenv import load_dotenv

import aiohttp
import motor.motor_asyncio 
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.exceptions import TelegramAPIError

# =========================================================================
# ⚙️ CONFIGURATION
# =========================================================================
load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] - %(message)s')
logger = logging.getLogger("WIN-GO-V2")

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN")
    CHANNEL_ID = os.getenv("CHANNEL_ID", "YOUR_CHANNEL_ID")
    ADMIN_ID = os.getenv("ADMIN_ID", "1318826936") 
    MONGO_URI = os.getenv("MONGO_URI", "YOUR_MONGO_URI")
    API_URL = os.getenv("API_URL", "https://api.bigwinqaz.com/api/webapi/GetNoaverageEmerdList")
    
    # 🛑 Stop-Loss: ၃ ဆ အထိသာ တက်မည်
    MULTIPLIERS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15] 
    
    WIN_STICKER = "CAACAgUAAxkBAAEQxuxputyXzdkRGgp-aKcQ8PW8fZNDDwAC3BUAApv76Val7MxrumxrLjoE"  
    LOSE_STICKER = "YOUR_LOSE_STICKER_ID"

    @staticmethod
    def get_headers():
        return {
            'authority': 'api.bigwinqaz.com', 
            'accept': 'application/json',
            'content-type': 'application/json;charset=UTF-8', 
            'user-agent': 'Mozilla/5.0'
        }

bot = Bot(token=Config.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# =========================================================================
# 🧩 EXACT 4-PATTERN ENGINE (NO SKIP)
# =========================================================================
class TrendPatternEngine:
    def __init__(self):
        # သင်တောင်းဆိုထားသော Pattern ၆ မျိုး အတိအကျ
        self.patterns = {
            "BBBB": "BIG",
            "SSSS": "SMALL",
            "BBSS": "BIG",
            "SSBB": "SMALL",
            "SBSB": "SMALL",
            "BSBS": "BIG"
        }

    def analyze(self, docs: List[dict], streak: int) -> dict:
        if len(docs) < 6:
            # Data မလုံလောက်သေးလျှင် Default အနေဖြင့် ပြမည်
            return {"pred": "BIG", "step": Config.MULTIPLIERS[0], "display": "B-B-B-B-B-B"}

        # အဟောင်းဆုံးမှ အသစ်ဆုံးသို့ စီထားသော Size များ
        sizes = [d.get('size', 'BIG') for d in docs]
        
        # 📊 ပုံစံပြသရန် နောက်ဆုံး ၆ ပွဲကို ယူမည် (e.g., S-S-S-S-S-S)
        history = "".join(['B' if s == 'BIG' else 'S' for s in sizes])
        display_pattern = "-".join(list(history[-6:]))

        pred_size = None
        
        # 🎯 နောက်ဆုံး (၄) ပွဲစာ Pattern ကိုသာ ယူ၍ တိုက်စစ်မည်
        history_4 = history[-4:]
        if history_4 in self.patterns:
            pred_size = self.patterns[history_4]

        if not pred_size:
            # 🚨 Pattern မမိပါက SKIP မလုပ်ဘဲ နောက်ဆုံးထွက်ခဲ့သည့် အဖြေအတိုင်း ဆက်လိုက်မည် (Trend Following)
            pred_size = sizes[-1]

        # 🛡️ 3x Stop Loss Limit
        safe_streak = streak if streak < len(Config.MULTIPLIERS) else 0
        actual_multiplier = Config.MULTIPLIERS[safe_streak]

        return {
            "pred": "BIG" if pred_size == "BIG" else "SMALL", 
            "step": actual_multiplier, 
            "display": display_pattern
        }

# =========================================================================
# 🏆 TELEGRAM APP LOOP
# =========================================================================
class AppController:
    def __init__(self):
        self.client = motor.motor_asyncio.AsyncIOMotorClient(Config.MONGO_URI)
        self.db = self.client['win_go_db']
        self.history = self.db['game_history']
        
        self.pattern_ai = TrendPatternEngine()
        self.last_issue = None
        self.lose_streak = 0  
        self.local_cache = deque(maxlen=200) 
        
    async def init_db_cache(self):
        await self.history.create_index("issue_number", unique=True)
        docs = await self.history.find().sort("issue_number", -1).limit(200).to_list(length=200)
        for d in reversed(docs): self.local_cache.append(d)

    async def fetch_api(self, session: aiohttp.ClientSession) -> Optional[dict]:
        json_data = {
            'pageSize': 10, 'pageNo': 1, 'typeId': 30, 'language': 7, 
            'random': '9ef85244056948ba8dcae7aee7758bf4', 
            'signature': '2EDB8C2B5264F62EC53116916A9EC05C', 
            'timestamp': int(time.time())
        }
        try:
            async with session.post(Config.API_URL, headers=Config.get_headers(), json=json_data, timeout=3) as r:
                if r.status == 200: return await r.json()
        except: pass
        return None

    async def send_prediction(self, issue: str, data: dict):
        # 🖼️ SKIP မရှိတော့သဖြင့် ပွဲတိုင်း အတိအကျ ပို့ပေးမည်
        msg = f"🍀 <b>𝐖𝐈𝐍 𝐆𝐎 𝟑𝟎 𝐒𝐄𝐂𝐎𝐍𝐃𝐒 𝐕𝟐</b> 🍀\n" \
              f"⏰ Pᴇʀɪᴏᴅ: <code>{issue}</code>\n" \
              f"🎯 Cʜᴏɪᴄᴇ : <b>{data['pred']}</b> {data['step']}x\n" \
              f"📊 Pᴀᴛᴛᴇʀɴ Mᴏᴅᴇ | {data['display']}"
              
        try: await bot.send_message(chat_id=Config.CHANNEL_ID, text=msg)
        except TelegramAPIError: pass

    async def handle_result(self, issue: str, pred_size: str, size: str, number: int):
        is_win = (pred_size == size)
        win_str, icon = ("𝐖𝐈𝐍", "🟢") if is_win else ("𝐋𝐎𝐒𝐄", "🔴")
        msg = f"<b>🏆 𝐑𝐄𝐒𝐔𝐋𝐓𝐒 ({issue})</b>\n📊 ʀᴇsᴜʟᴛs: {icon} <b>{win_str}</b> | {size[0]} ({number})"
        
        try:
            await bot.send_message(chat_id=Config.CHANNEL_ID, text=msg)
            if is_win:
                self.lose_streak = 0
                if Config.WIN_STICKER: await bot.send_sticker(chat_id=Config.CHANNEL_ID, sticker=Config.WIN_STICKER)
            else:
                self.lose_streak += 1
                if Config.LOSE_STICKER: await bot.send_sticker(chat_id=Config.CHANNEL_ID, sticker=Config.LOSE_STICKER)
        except TelegramAPIError: pass

    async def run_forever(self):
        await self.init_db_cache()
        connector = aiohttp.TCPConnector(limit=10) 
        
        async with aiohttp.ClientSession(connector=connector) as session:
            logger.info("🔥 EXACT 4-PATTERN LOOP STARTED (30 SECONDS MODE) 🔥")
            next_prediction = None
            
            while True:
                data = await self.fetch_api(session)
                if not data or data.get('code') != 0: 
                    await asyncio.sleep(1) 
                    continue
                
                latest = data["data"]["list"][0]
                issue, number = str(latest["issueNumber"]), int(latest["number"])
                size = "BIG" if number >= 5 else "SMALL"
                
                if not self.last_issue:
                    self.last_issue = issue
                    continue

                if int(issue) > int(self.last_issue):
                    logger.info(f"🟢 Result: {issue} -> {size} ({number})")
                    
                    doc = {"issue_number": issue, "number": number, "size": size, "timestamp": datetime.now()}
                    await self.history.update_one({"issue_number": issue}, {"$setOnInsert": doc}, upsert=True)
                    self.local_cache.append(doc)
                    
                    if next_prediction:
                        await self.handle_result(issue, next_prediction["pred"], size, number)

                    self.last_issue = issue
                    next_issue = str(int(issue) + 1)
                    
                    # 🎯 ပွဲတိုင်း Prediction ထုတ်ပေးမည်
                    next_prediction = self.pattern_ai.analyze(list(self.local_cache), self.lose_streak)
                    await self.send_prediction(next_issue, next_prediction)

                    # 30s Game Mode (Sleep 15s)
                    await asyncio.sleep(15)
                else:
                    await asyncio.sleep(1)

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    app = AppController()
    asyncio.create_task(app.run_forever())
    await dp.start_polling(bot)

if __name__ == '__main__':
    try: asyncio.run(main())
    except KeyboardInterrupt: logger.info("🛑 System Shut Down.")
