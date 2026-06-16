import requests
from bs4 import BeautifulSoup
import re
import os
import time

def fetch_with_retry(url, headers, max_retries=3):
    for i in range(max_retries):
        try:
            res = requests.get(url, headers=headers)
            return res
        except Exception as e:
            print(f"Request failed ({i+1}/{max_retries}) for {url}: {e}")
            if i < max_retries - 1:
                time.sleep(1.5)
    raise Exception(f"Failed after {max_retries} retries: {url}")

def get_race_ids(date_str):
    """指定した日付のレースID一覧を取得する"""
    url = f"https://race.netkeiba.com/top/race_list_sub.html?kaisai_date={date_str}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'}
    try:
        res = fetch_with_retry(url, headers=headers, max_retries=1)
        res.encoding = 'utf-8'
        matches = re.findall(r'race_id=(\d{12})', res.text)
        return sorted(list(set(matches)))
    except Exception as e:
        print(f"レース一覧取得エラー（{date_str}）: {e}")
        return []

def fetch_single_race_1st_place(race_id):
    """1レースの結果ページをスクレイピングし、1着馬の[レース番号, 人気順]を返す"""
    url = f"https://race.netkeiba.com/race/result.html?race_id={race_id}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'}
    try:
        res = fetch_with_retry(url, headers=headers)
        res.encoding = 'euc-jp'
        
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 着順1（または現在の1番人気）の行を探す
        result_table = soup.find('table', class_='RaceTable01') # レース終了後の結果テーブル
        if not result_table:
            result_table = soup.find('table', class_='RaceNFriendsTable') # 開催中のオッズテーブル
        if not result_table:
            return None
            
        for row in result_table.find_all('tr')[1:]: # ヘッダスキップ
            cols = row.find_all('td')
            if len(cols) > 10:
                rank = cols[0].get_text(strip=True)
                if rank == '1':
                    pop = cols[9].get_text(strip=True)
                    try:
                        return [race_id, int(pop)]
                    except ValueError:
                        return None
        return None
    except Exception as e:
        print(f"1着データ取得エラー（{race_id}）: {e}")
        return None

def fetch_1st_place_popularities(race_ids):
    """複数レースの1着人気順を直列で取得する（IPブロック回避のため）"""
    results = {}
    for rid in race_ids:
        data = fetch_single_race_1st_place(rid)
        if data:
            results[data[0]] = data[1]
        time.sleep(1.5) # 連続アクセスによるブロックを回避
    
    # 元のID順にソートしてリスト化
    sorted_pops = [results[rid] for rid in race_ids if rid in results]
    return sorted_pops

