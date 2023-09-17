import json
from dataclasses import astuple

import requests
from bs4 import BeautifulSoup
from models import Notebook
from tqdm import tqdm
from db_client import DbPostgres

from loguru import logger


class Parser:
    ALIAS_CHARACTER = {'Производитель': 'manufacturer', 'Диагональ экрана': "diagonal",
                       'Разрешение экрана': 'screen_resolution', 'Операционная система': 'os', 'Процессор': 'processor',
                       'Оперативная память': 'op_mem', 'Тип видеокарты': 'type_video_card', 'Видеокарта': 'video_card',
                       'Тип накопителя': 'type_drive', 'Ёмкость накопителя': 'capacity_drive',
                       'Время автономной работы': 'auto_word_time', 'Состояние': 'state'}

    HEADERS = {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/114.0'}
    DB = DbPostgres()

    def get_links(self, url: str) -> list:
        response = requests.get(url, headers=self.HEADERS)
        soup = BeautifulSoup(response.text, 'lxml')
        cards = soup.find_all('section')
        links = []
        for card in cards:
            a = card.find('a', href=True)['href']
            a = a.split('?')[0]
            links.append(a)
        next_data = soup.find('script', id='__NEXT_DATA__').text
        pages = json.loads(next_data)['props']['initialState']['listing']['pagination']
        current_page = list(filter(lambda el: el['label'] == 'self', pages))[0]
        logger.info(f"Обрабатывается страница номер {current_page['num']}")
        try:
            page = list(filter(lambda el: el['label'] == 'next', pages))[0]['token']
        except Exception as e:
            page = ''

        return [links, page]

    def get_data(self, urls: list) -> list:
        data = []
        for url in tqdm(urls, desc='PARSING DATA'):
            resp = requests.get(url, self.HEADERS)
            soup = BeautifulSoup(resp.text, 'lxml')
            props_data = {}
            title = soup.find('h1', class_='styles_brief_wrapper__title__Ksuxa').text
            price = soup.find('span', class_='styles_main__eFbJH').text
            price = price.replace(' р.', '').replace(' ', '')
            try:
                price = float(price)
            except Exception as e:
                logger.error(f'Не корректная цена {price}')
                continue
            description = soup.find('div', itemprop="description").text

            props = soup.find_all('div', {"class": 'styles_parameter_wrapper__L7UfK'})

            for p in props:
                k = p.find('div', class_='styles_parameter_label__i_OkS').text
                v = p.find('div', class_='styles_parameter_value__BkYDy').text
                if k in self.ALIAS_CHARACTER:
                    k = self.ALIAS_CHARACTER[k]
                    props_data[k] = str(v)
            try:
                image = soup.find('img', 'styles_slide__image__YIPad')['src']
            except Exception as e:
                logger.error(f"Нет картинки")
                image = ''
            props_data['title'] = title
            props_data['price'] = price
            props_data['description'] = description
            props_data['image'] = image
            props_data['url'] = url
            data.append(Notebook(**props_data))
        return data

    def save_data(self, data: list) -> None:
        data = [astuple(i) for i in data]
        self.DB.query_update("""
        INSERT INTO notebook(title, url, price, description, image, manufacturer, diagonal, screen_resolution, os,
         processor, op_mem, type_video_card, video_card, type_drive, capacity_drive, auto_word_time, state) 
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s, %s) ON CONFLICT DO NOTHING 
        """, data, many=True, message='notes saved')

    def save_temp_links(self, links: list) -> None:
        links = [(i,) for i in links]
        self.DB.query_update("""
        INSERT INTO temp_notebook(url) VALUES (%s) ON CONFLICT DO NOTHING
        """, links, many=True, message='Temp_notes saved')

    def check_notebook(self) -> None:
        temp_links = list(map(lambda el: el[0], self.DB.fetch_all("""SELECT url from temp_notebook""", factory='list')))
        links = [i[0] for i in self.DB.fetch_all("""SELECT url from notebook""", factory='list')]
        to_delete = [i for i in links if i not in temp_links]
        self.DB.query_update("""DELETE FROM notebook WHERE url IN %s""", (tuple(to_delete),))

    def run(self):
        self.DB.query_update("""TRUNCATE TABLE temp_notebook""", message='temp_notes очищена')
        url = 'https://www.kufar.by/l/r~minsk/noutbuki?cursor=eyJ0IjoiYWJzIiwiZiI6dHJ1ZSwicCI6MX0%3D'
        flag = True
        while flag:
            links_and_token = self.get_links(url)
            links = links_and_token[0]
            self.save_temp_links(links)
            token = links_and_token[1]
            data = self.get_data(links)
            self.save_data(data)
            url = 'https://www.kufar.by/l/r~minsk/noutbuki?cursor=' + token
            if not token:
                flag = False

        self.check_notebook()


Parser().run()
