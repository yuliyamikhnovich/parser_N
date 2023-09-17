import requests
from bs4 import BeautifulSoup

ALIAS_CHARACTER = {'Производитель': 'manufacturer', 'Диагональ экрана': "diagonal",
                     'Разрешение экрана': 'screen_resolution', 'Операционная система': 'os', 'Процессор': 'processor',
                     'Оперативная память': 'op_mem', 'Тип видеокарты': 'type_video_card', 'Видеокарта': 'video_card',
                     'Тип накопителя': 'type_drive', 'Ёмкость накопителя': 'capacity_drive',
                     'Время автономной работы': 'auto_word_time', 'Состояние': 'state'}

url = 'https://www.kufar.by/l/r~minsk/noutbuki?cursor=eyJ0IjoiYWJzIiwiZiI6dHJ1ZSwicCI6MX0%3D'

response = requests.get(url)
soup = BeautifulSoup(response.text, 'lxml')

cards = soup.find_all('section')
links = []
for card in cards:
    a = card.find('a', href=True)['href']
    a = a.split('?')[0]
    links.append(a)

print(links)

for link in links:
    resp = requests.get(link)
    soup = BeautifulSoup(resp.text, 'lxml')
    title = soup.find('h1', class_='styles_brief_wrapper__title__Ksuxa').text
    price = soup.find('span', class_='styles_main__eFbJH').text
    price = price.replace(' р.', '').replace(' ', '')
    try:
        price = float(price)
    except Exception as e:
        print('ERROR>>' + price + "<<")
        continue
    description = soup.find('div', itemprop="description").text

    props = soup.find_all('div', {"class": 'styles_parameter_wrapper__L7UfK'})
    props_data = {}
    for p in props:
        k = p.find('div', class_='styles_parameter_label__i_OkS').text
        v = p.find('div', class_='styles_parameter_value__BkYDy').text
        if k in ALIAS_CHARACTER:
            k = ALIAS_CHARACTER[k]
            props_data[k] = v
    print(props_data)
    image = soup.find('img', 'styles_slide__image__YIPad')['src']
    print(image)


