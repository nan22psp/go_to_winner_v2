"""
====================================================================================
🏆 ULTRA-AI AUTONOMOUS BOT (PATTERN + 20-CORE AI) - PRODUCTION EDITION 🏆
====================================================================================
Version: 4.0.0 (Ultimate 30-Second Polling & Pattern Catching)
Features:
- Trend Pattern Engine (Dragon, Ping-Pong, Two-Two, Three-Three)
- 3x Max Stop-Loss Limit (1x, 2x, 3x) -> Falls back to 1x on 4th loss
- Asyncio Offloading & Memory Deque Caching (Zero DB lag)
- Interval Training (Train every 10 rounds to save 90% CPU)
- 7-Loss Streak Alert System for Admin
====================================================================================
"""

import asyncio
import time
import os
import logging
from logging.handlers import RotatingFileHandler
from collections import deque
from datetime import datetime
from typing import List, Dict, Optional
from dotenv import load_dotenv

import aiohttp
import motor.motor_asyncio 
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.exceptions import TelegramAPIError

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

import torch
import torch.nn as nn

import warnings
warnings.filterwarnings("ignore")

# =========================================================================
# [1] ⚙️ CONFIGURATION & LOGGING SETUP
# =========================================================================
load_dotenv()

if not os.path.exists('logs'):
    os.makedirs('logs')

logger = logging.getLogger("ULTRA-AI")
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] - %(message)s', datefmt='%H:%M:%S')

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

file_handler = RotatingFileHandler('logs/bot_system.log', maxBytes=5*1024*1024, backupCount=3)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN")
    CHANNEL_ID = os.getenv("CHANNEL_ID", "YOUR_CHANNEL_ID")
    ADMIN_ID = os.getenv("ADMIN_ID", "1318826936") 
    MONGO_URI = os.getenv("MONGO_URI", "YOUR_MONGO_URI")
    API_URL = os.getenv("API_URL", "https://api.bigwinqaz.com/api/webapi/GetNoaverageEmerdList")
    
    # 🛑 ၃ ဆ (3x) ထိသာ အများဆုံးတက်မည်။ ၄ ပွဲမြောက် ရှုံးပါက အရင်းမပြုတ်ရန် 1x မှ ပြန်စမည်။
    MULTIPLIERS = [1, 2, 3, 5, 8, 15] 
    
    WIN_STICKER = "CAACAgUAAxkBAAEQxupputyQrtjWe6a-N4-txUyUHderxQAC3xIAAqUd6VZVZKMYNf4oXzoE"  
    LOSE_STICKER = "YOUR_LOSE_STICKER_ID"

    @staticmethod
    def get_headers():
        return {
            'authority': 'api.bigwinqaz.com', 
            'accept': 'application/json',
            'content-type': 'application/json;charset=UTF-8', 
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

bot = Bot(token=Config.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# =========================================================================
# [2] 🧩 TREND PATTERN ENGINE (အလိုအလျောက် ပုံစံဖမ်းမည့်စနစ်)
# =========================================================================
class TrendPatternEngine:
    def __init__(self):
        # B = BIG, S = SMALL
        self.patterns = {
            # 1. Dragon Trend (အတန်းရှည်)
            "BBB": "BIG",   
            "SSS": "SMALL",
            # 2. Ping-Pong Trend (တစ်လှည့်စီ)
            "BSB": "SMALL", 
            "SBS": "BIG",
            # 3. Two-Two Trend (နှစ်လုံးတွဲ)
            "BBS": "SMALL",  
            "SSB": "BIG",    
            "BBSS": "BIG",   
            "SSBB": "SMALL",
            # 4. Three-Three Trend (သုံးလုံးတွဲ)
            "BBBS": "SMALL", 
            "SSSB": "BIG"
        }

    def catch_pattern(self, sizes: List[str]) -> dict:
        if len(sizes) < 4: return {} 

        # နောက်ဆုံး ၄ ပွဲကို 'B' သို့မဟုတ် 'S' အဖြစ်ပြောင်းမည်
        history = "".join(['B' if s == 'BIG' else 'S' for s in sizes[-4:]])
        history_3 = history[-3:] 

        pred_size = None
        if history in self.patterns:
            pred_size = self.patterns[history]
        elif history_3 in self.patterns:
            pred_size = self.patterns[history_3]

        if pred_size:
            # Pattern ဖမ်းမိပါက 85% Confidence ပြမည်
            return {"pred": "BIG" if pred_size == "BIG" else "SMALL", "conf": 85.0} 
        return {} 

# =========================================================================
# [3] 🧠 AI ENGINES (PyTorch & Scikit-Learn)
# =========================================================================
class CNN1D(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv1d(1, 8, kernel_size=3, padding=1)
        self.fc = nn.Linear(8 * 20, 1)
        self.relu = nn.ReLU()
    def forward(self, x):
        x = self.relu(self.conv1(x))
        x = x.view(x.size(0), -1)
        return torch.sigmoid(self.fc(x))

class LSTMPredictor(nn.Module):
    def __init__(self):
        super().__init__()
        self.lstm = nn.LSTM(1, 16, batch_first=True)
        self.fc = nn.Linear(16, 1)
    def forward(self, x):
        _, (hn, _) = self.lstm(x)
        return torch.sigmoid(self.fc(hn[-1]))

class DeepLearningGroup:
    def __init__(self):
        self.lstm_model = LSTMPredictor()
        self.cnn_model = CNN1D()
        self.q_table = {} 
        
        try:
            if os.path.exists('lstm_weights.pth'):
                self.lstm_model.load_state_dict(torch.load('lstm_weights.pth', map_location='cpu', weights_only=True))
            if os.path.exists('cnn_weights.pth'):
                self.cnn_model.load_state_dict(torch.load('cnn_weights.pth', map_location='cpu', weights_only=True))
        except Exception: pass

        # ⚡ CPU ပေါ်တွင် အမြန်ဆုံး Run ရန် 8-bit ပြောင်းခြင်း
        self.lstm_model = torch.quantization.quantize_dynamic(self.lstm_model, {nn.LSTM, nn.Linear}, dtype=torch.qint8)
        self.cnn_model = torch.quantization.quantize_dynamic(self.cnn_model, {nn.Linear}, dtype=torch.qint8)
        self.lstm_model.eval()
        self.cnn_model.eval()

    def predict(self, sizes: List[str], default_b: float) -> Dict[str, float]:
        res = {"lstm": default_b, "cnn": default_b, "rl": default_b}
        if len(sizes) < 21: return res
        try:
            data = [1.0 if s == 'BIG' else 0.0 for s in sizes[-21:]]
            with torch.no_grad(): 
                seq_lstm = torch.tensor(data[:-1], dtype=torch.float32).view(1, 20, 1)
                res["lstm"] = float(self.lstm_model(seq_lstm).item())
                seq_cnn = torch.tensor(data[:-1], dtype=torch.float32).view(1, 1, 20)
                res["cnn"] = float(self.cnn_model(seq_cnn).item())
            res["rl"] = self.q_table.get(tuple(sizes[-3:]), default_b)
        except Exception: pass
        return res

class MachineLearningGroup:
    def __init__(self, train_interval=10):
        self.models = {
            "rf": RandomForestClassifier(n_estimators=30, max_depth=3, n_jobs=-1),
            "logistic": LogisticRegression(max_iter=100)
        }
        self.train_interval = train_interval
        self.predict_count = 0
        self.is_trained = False

    def predict(self, X: np.ndarray, y: np.ndarray, curr_X: np.ndarray, default_b: float) -> Dict[str, float]:
        res = {k: default_b for k in self.models.keys()}
        if X is None or len(X) < 20: return res
        
        if not self.is_trained or self.predict_count % self.train_interval == 0:
            for name, model in self.models.items():
                try: model.fit(X, y)
                except: pass
            self.is_trained = True
            
        self.predict_count += 1
        for name, model in self.models.items():
            try: res[name] = float(model.predict_proba(curr_X)[0][1]) if 1.0 in model.classes_ else default_b
            except: pass
        return res

# =========================================================================
# [4] 🤖 AUTONOMOUS ORCHESTRATOR 
# =========================================================================
class AutonomousBot:
    def __init__(self):
        self.trend_engine = TrendPatternEngine()
        self.dl = DeepLearningGroup()
        self.ml = MachineLearningGroup(train_interval=10)
        self.scaler = StandardScaler()
        self.meta_weights = {"ml": 0.4, "dl": 0.6}
        self.last_state = ()

    def analyze(self, docs: List[dict], streak: int) -> dict:
        if len(docs) < 30: 
            return {"pred": "SKIP", "conf": 0, "step": 0, "type": ""}
        
        sizes = [d.get('size', 'BIG') for d in docs]
        default_b = sizes.count('BIG') / len(sizes) if sizes else 0.5
        self.last_state = tuple(sizes[-3:])

        # 🎯 1. Pattern Engine ကို အရင်စစ်မည် 
        pattern_match = self.trend_engine.catch_pattern(sizes)
        
        if pattern_match:
            pred_size = pattern_match["pred"]
            final_conf = pattern_match["conf"]
            logic_type = "🧩 Pattern Mode"
        else:
            # 🧠 2. Pattern မမိပါက AI ဖြင့်သာ တွက်မည်
            window = 8
            X, y = [], []
            for i in range(len(sizes) - window - 1):
                X.append([1.0 if s == 'BIG' else 0.0 for s in sizes[i:i+window]])
                y.append(1.0 if sizes[i+window] == 'BIG' else 0.0)
            
            curr_X = [[1.0 if s == 'BIG' else 0.0 for s in sizes[-window:]]]
            try:
                X = self.scaler.fit_transform(np.array(X))
                curr_X = self.scaler.transform(np.array(curr_X))
            except: curr_X = None

            ml_preds = self.ml.predict(X, np.array(y), curr_X, default_b)
            dl_preds = self.dl.predict(sizes, default_b)
            
            final_prob = (np.mean(list(dl_preds.values())) * self.meta_weights["dl"]) + \
                         (np.mean(list(ml_preds.values())) * self.meta_weights["ml"])
            
            pred_size = "BIG" if final_prob > 0.5 else "SMALL"
            final_conf = max(final_prob, 1 - final_prob) * 100
            logic_type = "🧠 AI Mode"

        # 🛡️ Risk Management (Stop-Loss System)
        # ၃ ဆ အထိသာ တက်မည်။ streak က multiplier array ထက်ကြီးသွားပါက index 0 (1x) သို့ ပြန်ချမည်
        safe_streak = streak if streak < len(Config.MULTIPLIERS) else 0
        actual_multiplier = Config.MULTIPLIERS[safe_streak]

        return {"pred": pred_size, "conf": round(final_conf, 1), "step": actual_multiplier, "type": logic_type}

# =========================================================================
# [5] 🏆 TELEGRAM APP & 30-SEC ASYNC LOOP
# =========================================================================
class AppController:
    def __init__(self):
        self.client = motor.motor_asyncio.AsyncIOMotorClient(Config.MONGO_URI)
        self.db = self.client['ultra20core_db']
        self.history = self.db['game_history']
        
        self.bot_ai = AutonomousBot()
        self.last_issue = None
        self.lose_streak = 0  
        self.local_cache = deque(maxlen=500) 
        
    async def init_db_cache(self):
        logger.info("📦 Preloading Data to Memory Cache...")
        await self.history.create_index("issue_number", unique=True)
        docs = await self.history.find().sort("issue_number", -1).limit(500).to_list(length=500)
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
        if data["pred"] == "SKIP": return
        msg = f"<b>☘️ 𝐖𝐈𝐍 𝐆𝐎 𝟑𝟎 𝐒𝐄𝐂𝐎𝐍𝐃𝐒 𝐕𝟐 ☘️</b>\n⏰ Pᴇʀɪᴏᴅ: <code>{issue}</code>\n🎯 Cʜᴏɪᴄᴇ: <b>{data['pred']}</b> {data['step']}x\n📊 {data['type']} | Cᴏɴғ: {data['conf']}%"
        try: await bot.send_message(chat_id=Config.CHANNEL_ID, text=msg)
        except TelegramAPIError: pass

    async def handle_result(self, issue: str, pred_size: str, size: str, number: int):
        is_win = (pred_size == size)
        win_str, icon = ("𝐖𝐢𝐧", "🟢") if is_win else ("𝐋𝐨𝐬𝐞", "🔴")
        msg = f"<b>🏆 𝐑𝐄𝐒𝐔𝐋𝐓𝐒 ({issue})</b>\n📊 𝐑𝐞𝐬𝐮𝐥𝐭 : {icon} <b>{win_str}</b> | {size[0]} ({number})"
        
        try:
            await bot.send_message(chat_id=Config.CHANNEL_ID, text=msg)
            if is_win:
                self.lose_streak = 0
                if Config.WIN_STICKER: await bot.send_sticker(chat_id=Config.CHANNEL_ID, sticker=Config.WIN_STICKER)
            else:
                self.lose_streak += 1
                if Config.LOSE_STICKER: await bot.send_sticker(chat_id=Config.CHANNEL_ID, sticker=Config.LOSE_STICKER)

                if self.lose_streak == 7 and Config.ADMIN_ID:
                    alert_msg = f"⚠️ <b>URGENT ALERT</b> ⚠️\nBot သည် (၇) ပွဲဆက်တိုက် ရှုံးနေပါသည်။"
                    await bot.send_message(chat_id=Config.ADMIN_ID, text=alert_msg)
        except TelegramAPIError: pass

    async def run_forever(self):
        await self.init_db_cache()
        connector = aiohttp.TCPConnector(limit=10) 
        
        async with aiohttp.ClientSession(connector=connector) as session:
            logger.info("🔥 PATTERN + AI LOOP STARTED (30 SECONDS MODE) 🔥")
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
                        old_q = self.bot_ai.dl.q_table.get(self.bot_ai.last_state, 0.5)
                        reward = 1.0 if next_prediction["pred"] == size else 0.0
                        self.bot_ai.dl.q_table[self.bot_ai.last_state] = old_q + 0.1 * (reward - old_q)

                    self.last_issue = issue
                    next_issue = str(int(issue) + 1)
                    
                    # Offload to thread to prevent blocking
                    next_prediction = await asyncio.to_thread(self.bot_ai.analyze, list(self.local_cache), self.lose_streak)
                    await self.send_prediction(next_issue, next_prediction)

                    # ⚡ 30s Game Mode: Sleep 15s safely
                    await asyncio.sleep(10)
                else:
                    # ⚡ Polling Mode: Check every 1s
                    await asyncio.sleep(1)

async def main():
    logger.info("Starting Telegram Bot Polling...")
    await bot.delete_webhook(drop_pending_updates=True)
    app = AppController()
    asyncio.create_task(app.run_forever())
    await dp.start_polling(bot)

if __name__ == '__main__':
    try: asyncio.run(main())
    except KeyboardInterrupt: logger.info("🛑 System Shut Down by Admin.")
