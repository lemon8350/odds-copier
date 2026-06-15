from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from scraper import get_race_ids, get_win5_race_ids, get_win5_live_odds
from datetime import datetime, timedelta
import os
from typing import List

app = FastAPI(title="WIN5 Difficulty Meter API")

# 開発中のCORS許可
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_weekend_dates():
    """現在時刻から直近の土日を判定する（月〜木は次の土日、金〜日は今の週）"""
    now = datetime.now()
    if now.weekday() < 4:  # Mon(0) to Thu(3)
        saturday = now + timedelta(days=(5 - now.weekday()))
    else:
        saturday = now - timedelta(days=(now.weekday() - 5))
    sunday = saturday + timedelta(days=1)
    return saturday.strftime("%Y%m%d"), sunday.strftime("%Y%m%d")

@app.get("/api/status")
def get_status():
    sat, sun = get_weekend_dates()
    return {
        "status": "ok",
        "target_saturday": sat,
        "target_sunday": sun
    }

@app.get("/api/races")
def api_get_races(target_date: str = Query(...)):
    """指定された日付の全レースIDと、予測されたWIN5対象レースIDを返す"""
    race_ids = get_race_ids(target_date)
    win5_races = get_win5_race_ids(target_date)
    return {"date": target_date, "races": race_ids, "win5_races": win5_races}

@app.get("/api/win5-live-odds")
def api_get_win5_live_odds(race_ids: List[str] = Query(...)):
    """指定されたレースIDのリストに対して、リアルタイムオッズを返す"""
    data = get_win5_live_odds(race_ids)
    return {"races": data}


# フロントエンドの静的ファイルをマウント
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
