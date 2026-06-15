import requests
from bs4 import BeautifulSoup
import re

def get_win5_race_ids(date_str):
    url = f"https://race.netkeiba.com/top/race_list_sub.html?kaisai_date={date_str}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    res = requests.get(url, headers=headers, timeout=5)
    res.encoding = 'utf-8'
    soup = BeautifulSoup(res.text, 'html.parser')
    
    candidates = []
    for a in soup.find_all('a', href=re.compile(r'shutuba\.html\?race_id=\d{12}')):
        m = re.search(r'race_id=(\d{12})', a['href'])
        if not m: continue
        rid = m.group(1)
        r_num = int(rid[-2:])
        if r_num not in [9, 10, 11]:
            continue
        
        time_span = a.find('span', class_='RaceList_Itemtime')
        if time_span:
            t_str = time_span.get_text(strip=True)
            candidates.append((rid, t_str))
            
    unique_candidates = {}
    for rid, t in candidates:
        unique_candidates[rid] = t
        
    sorted_cands = sorted(unique_candidates.items(), key=lambda x: x[1])
    if len(sorted_cands) >= 5:
        # 後ろから5つ取得し、時間順に並び替え
        win5_races = [x[0] for x in sorted_cands[-5:]]
        return sorted(win5_races, key=lambda rid: unique_candidates[rid])
    return []

print(get_win5_race_ids('20260614'))
