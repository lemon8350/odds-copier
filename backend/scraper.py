import requests
from bs4 import BeautifulSoup
import re
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

def fetch_with_retry(url, headers, max_retries=3):
    for i in range(max_retries):
        try:
            # Render上での挙動を安定させるため、強制的なタイムアウト設定を削除（元々の安定した挙動に戻す）
            res = requests.get(url, headers=headers)
            return res
        except Exception as e:
            print(f"Request failed ({i+1}/{max_retries}) for {url}: {e}")
            if i < max_retries - 1:
                import time
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

def get_win5_race_ids(date_str):
    """指定した日付のWIN5対象レースを取得する（過去日付にも対応）"""
    url = f"https://race.netkeiba.com/top/race_list_sub.html?kaisai_date={date_str}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        res = fetch_with_retry(url, headers=headers, max_retries=1)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        
        candidates = []
        # shutuba.html または result.html の両方に対応（過去日付の対策）
        for a in soup.find_all('a', href=re.compile(r'(shutuba|result)\.html\?race_id=\d{12}')):
            m = re.search(r'race_id=(\d{12})', a['href'])
            if not m: continue
            rid = m.group(1)
            r_num = int(rid[-2:])
            # WIN5は通常10Rと11R（稀に9R）。12Rは含まれないため除外。
            if r_num not in [9, 10, 11]:
                continue
            
            time_span = a.find('span', class_='RaceList_Itemtime')
            if time_span:
                t_str = time_span.get_text(strip=True)
                candidates.append((rid, t_str))
                
        unique_candidates = {}
        for rid, t in candidates:
            unique_candidates[rid] = t
            
        # 発走時刻順に並び替え
        sorted_cands = sorted(unique_candidates.items(), key=lambda x: x[1])
        if len(sorted_cands) >= 5:
            # 12Rを除いた中で最も遅い時間の5レースがWIN5対象
            win5_races = [x[0] for x in sorted_cands[-5:]]
            # 最終的なリストも発走時刻順（= WIN5の対象レース順）にする
            return sorted(win5_races, key=lambda rid: unique_candidates[rid])
        return []
    except Exception as e:
        print(f"WIN5レース取得エラー（{date_str}）: {e}")
        return []

def fetch_single_race_1st_place(race_id):
    """1レースの結果ページをスクレイピングし、1着馬の[レース番号, 人気順]を返す"""
    url = f"https://race.netkeiba.com/race/result.html?race_id={race_id}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'}
    try:
        res = fetch_with_retry(url, headers=headers)
        res.encoding = 'euc-jp'
        
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 着順1の行を探す
        result_table = soup.find('table', class_='RaceNFriendsTable')
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
    """複数レースの1着人気順を並列で取得する"""
    results = {}
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_race = {executor.submit(fetch_single_race_1st_place, rid): rid for rid in race_ids}
        for future in as_completed(future_to_race):
            data = future.result()
            if data:
                results[data[0]] = data[1]
    
    # 元のID順にソートしてリスト化
    sorted_pops = [results[rid] for rid in race_ids if rid in results]
    return sorted_pops

def fetch_live_odds(race_id):
    """
    指定レースの馬番、枠番、馬名、騎手、最新オッズ、人気順を取得する
    """
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'}
    
    # 1. 出馬表から基本情報（枠、馬番、馬名、騎手）を取得
    shutuba_url = f"https://race.netkeiba.com/race/shutuba.html?race_id={race_id}"
    try:
        res_s = fetch_with_retry(shutuba_url, headers=headers)
        res_s.encoding = 'euc-jp'
        soup_s = BeautifulSoup(res_s.text, 'html.parser')
    except Exception as e:
        print(f"Error fetching shutuba for {race_id}: {e}")
        return []

    horses_info = {}
    table_s = soup_s.find('table', class_='Shutuba_Table')
    if table_s:
        for row in table_s.find_all('tr', class_='HorseList'):
            waku_td = row.find('td', class_=re.compile('Waku'))
            umaban_td = row.find('td', class_=re.compile('Umaban'))
            horse_span = row.find('span', class_='HorseName')
            jockey_td = row.find('td', class_='Jockey')
            
            if umaban_td and horse_span:
                umaban = umaban_td.get_text(strip=True)
                waku = waku_td.get_text(strip=True) if waku_td else ""
                horse_name = horse_span.get_text(strip=True)
                # 騎手名は改行などがあるため、テキストのみ抽出して整形
                jockey = jockey_td.get_text(strip=True).split(' ')[0] if jockey_td else ""
                
                horses_info[umaban] = {
                    "waku": waku,
                    "umaban": umaban,
                    "horse_name": horse_name,
                    "jockey": jockey,
                    "odds": "---",
                    "popularity": 999
                }

    # 2. オッズページから最新オッズと人気を取得 (HTMLFallback)
    odds_url = f"https://race.netkeiba.com/odds/index.html?type=b1&race_id={race_id}"
    try:
        res_o = fetch_with_retry(odds_url, headers=headers, max_retries=1)
        res_o.encoding = 'euc-jp'
        soup_o = BeautifulSoup(res_o.text, 'html.parser')
    except Exception as e:
        print(f"Error fetching odds for {race_id}: {e}")
        return list(horses_info.values())

    # 3. リアルタイムJSON APIからオッズを取得（当日のレース用）
    api_url = f"https://race.netkeiba.com/api/api_get_jra_odds.html?race_id={race_id}&type=1&action=init"
    api_odds_data = {}
    try:
        res_api = fetch_with_retry(api_url, headers=headers, max_retries=2)
        api_json = res_api.json()
        if "data" in api_json and "odds" in api_json["data"] and "1" in api_json["data"]["odds"]:
            # "1" は単勝オッズを表す
            api_odds_data = api_json["data"]["odds"]["1"]
            print(f"Loaded live odds from JSON API for {race_id}")
    except Exception as e:
        print(f"Failed to load JSON odds API for {race_id}: {e}")

    # HTMLからのオッズ取得用にテーブルをパースしておく（APIがない場合のみ使用）
    html_odds_map = {}
    tables_o = soup_o.find_all('table', class_='RaceOdds_HorseList_Table')
    for table_o in tables_o:
        for row in table_o.find_all('tr'):
            tds = row.find_all('td')
            if len(tds) < 5:
                continue
            umaban_td = row.find('td', class_=re.compile('W31'))
            if not umaban_td:
                umaban_td = tds[1]
            umaban = umaban_td.get_text(strip=True)
            odds_td = row.find('td', class_='Popular')
            if odds_td:
                html_odds_map[umaban] = odds_td.get_text(strip=True)

    # 全馬に対してオッズ・人気を更新
    for umaban, h_info in horses_info.items():
        odds_str = '---.-'
        popularity = 999
        horse_key = umaban.zfill(2)
        
        if horse_key in api_odds_data:
            # APIデータが存在すれば優先
            odds_data = api_odds_data[horse_key]
            odds_str = odds_data[0]
            try:
                popularity = int(odds_data[2])
            except ValueError:
                pass
        elif umaban in html_odds_map:
            # APIがなければHTMLから
            odds_str = html_odds_map[umaban]

        h_info["odds"] = odds_str
        if popularity == 999:
            try:
                if odds_str != '---.-' and odds_str != '':
                    h_info["odds_val"] = float(odds_str)
            except ValueError:
                pass
        else:
            h_info["popularity"] = popularity

    # リスト化
    result_list = list(horses_info.values())
    
    # 過去レースなどAPIがない場合のフォールバック用: popularityが999のままでオッズ(float)があればソートして付与
    fallback_horses = [h for h in result_list if h["popularity"] == 999 and "odds_val" in h]
    fallback_horses.sort(key=lambda x: x["odds_val"])
    for i, h in enumerate(fallback_horses):
        h["popularity"] = i + 1

    # 全体を人気順 -> 馬番順でソート
    result_list.sort(key=lambda x: (x["popularity"], int(x["umaban"]) if x["umaban"].isdigit() else 999))
    
    return result_list

def get_win5_live_odds(race_ids):
    """指定された複数のレースIDのリアルタイムオッズを直列で取得する（IPブロック回避のため）"""
    results = {}
    for r_id in race_ids:
        try:
            data = fetch_live_odds(r_id)
            results[r_id] = data
        except Exception as e:
            print(f"Failed to fetch live odds for {r_id}: {e}")
            results[r_id] = []
        time.sleep(1.5) # 連続アクセスブロック回避
    return results
