from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from calculator import get_popularity_sum
from scraper import get_race_ids
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


@app.get("/api/saturday-ceiling")
def get_saturday_ceiling(target_date: str = Query(None, description="YYYYMMDD形式の日付（省略時は自動判定）")):
    if target_date:
        sat_date = target_date
    else:
        sat_date, _ = get_weekend_dates()
    # 土曜日は全レースを対象（up_to_race=None）
    data = get_popularity_sum(sat_date, up_to_race=None)
    return {
        "date": sat_date,
        "ceiling": data["sum"],
        "count": data["count"],
        "details": data["details"]
    }

@app.get("/api/sunday-current")
def get_sunday_current(up_to_race: int = Query(9, description="集計するレース番号の上限（デフォルト第9レースまで）"), target_date: str = Query(None, description="YYYYMMDD形式")):
    if target_date:
        sun_date = target_date
    else:
        _, sun_date = get_weekend_dates()
    data = get_popularity_sum(sun_date, up_to_race=up_to_race)
    return {
        "date": sun_date,
        "current_sum": data["sum"],
        "count": data["count"],
        "up_to_race": up_to_race,
        "details": data["details"]
    }

# フロントエンドの静的ファイルをマウント
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
