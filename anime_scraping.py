from encodings import utf_8
from bs4 import BeautifulSoup
import re
import csv
# import numpy as np

class ToCsv:
    def __init__(self, html):
        self.soup = BeautifulSoup(html, 'html.parser')

    def find(self):
        self.koumoku_arr = []
        name = self.soup.find_all('p', class_='spots-name')
        anime = self.soup.find_all('p', class_='spots-anime')
        addr = self.soup.find_all('p', class_='spots-addr')
        self.distance = self.soup.find_all('p', class_='spots-distance')
        self.koumoku_arr += name, anime, addr

    def get_text(self):
        self.all_text = []
        lat = []
        lng = []
        for koumoku in self.koumoku_arr:
            text = []
            for tag in koumoku:
                text.append(tag.get_text())
            self.all_text.append(text)
        for distance in self.distance:
            lat.append(distance['data-spot-lat'])
            lng.append(distance['data-spot-lng'])
        self.all_text.append(lat)
        self.all_text.append(lng)

    def output_csv(self):
        with open('anime.csv', 'w') as f:
            writer = csv.writer(f)
            for i in range(len(self.all_text[0])):
                writer.writerow([self.all_text[0][i], self.all_text[1][i], self.all_text[2][i], self.all_text[3][i], self.all_text[4][i]])


with open('anime.html', encoding='utf-8') as f:
    html = f.read()
soup = ToCsv(html)
all_tags = soup.find()
text = soup.get_text()
soup.output_csv()