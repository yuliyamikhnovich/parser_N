import json

import requests
from bs4 import BeautifulSoup


url = 'https://www.kufar.by/l/r~minsk/noutbuki?cursor=eyJ0IjoiYWJzIiwiZiI6dHJ1ZSwicCI6MX0%3D'

response = requests.get(url)
soup = BeautifulSoup(response.text, 'lxml')

data = soup.find('script', id='__NEXT_DATA__')
data = json.loads(data.text)
with open('data.json', 'w') as f:
    f.write(json.dumps(data, ensure_ascii=False, indent=4))