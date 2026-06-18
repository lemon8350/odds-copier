import requests
from bs4 import BeautifulSoup

url = "https://race.netkeiba.com/race/shutuba.html?race_id=202605030504"
headers = {'User-Agent': 'Mozilla/5.0'}
res = requests.get(url, headers=headers)
soup = BeautifulSoup(res.content, 'html.parser')
for horse in soup.find_all('span', class_='HorseName'):
    print(repr(horse.get_text(strip=True)))
