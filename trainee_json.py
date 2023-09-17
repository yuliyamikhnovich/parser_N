import json

with open('data.json') as f:
    data = json.loads(f.read())
pages = data['props']['initialState']['listing']['pagination']

next_page = 'https://www.kufar.by/l/r~minsk/noutbuki?cursor=' + list(filter(lambda el:el['label'] == 'next', pages))[0]['token']
print(next_page)