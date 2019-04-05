import re
from bs4 import BeautifulSoup
import requests
from lxml.html.clean import Cleaner
from PIL import Image
from io import BytesIO
from tqdm import tqdm

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.1 Safari/605.1.15"
}

csm_domain = r'https://chuansongme.com'
pages_style = r"font-size: 1em;font-weight: bold"


def urlisgood(url):


    urlpatten = re.compile(r'https://chuansongme.com/account/')
    if urlpatten.match(url):
        return True
    else:
        return False


class EBook():

    def __init__(self, url):
        assert urlisgood(url), "URL is not valid. It should look like 'https://chuansongme.com/account/gh_4c12eeda5979'"
        self.url = url
        self.html = requests.get(self.url, headers=headers, timeout=1)
        self.home = BeautifulSoup(self.html.text)
        self.bookName = self.home.h1.text
        self.OEBPS_loc = self.bookName+'/'+'OEBPS/'
        self.images_loc = self.bookName+'/'+'OEBPS/images/'
        self.articles = []
        self.img_list = {}

    def get_list_of_articles(self):
        #  get all pages
        pages = self.home.find('span', style=pages_style)
        page_num = len(pages.find_all('a')) + 1

        for page in range(page_num):
            html = requests.get(self.url, params={'start':page*12}, headers=headers, timeout=1)
            soup = BeautifulSoup(html.text)
            articles = soup.find_all('h2')
            for article in articles:
                link = article.find('a')['href']
                title = article.find('a').text.strip()
                date = article.find(class_='timestamp').text
                self.articles.append({
                    'link': link,
                    'title': title,
                    'date': date
                })
        self.articles.reverse()

    def simplify_html(self, html):
        cleaner = Cleaner(
            page_structure=True,
            meta=True,
            embedded=True,
            links=True,
            style=True,
            processing_instructions=True,
            inline_style=True,
            scripts=True,
            javascript=True,
            comments=True,
            frames=True,
            forms=True,
            annoying_tags=True,
            remove_unknown_tags=True,
            safe_attrs_only=True,
            safe_attrs=frozenset(['src', 'color', 'href', 'title', 'class', 'name', 'id']),
            remove_tags=('span', 'font', 'div')
        )
        soup = BeautifulSoup(html)
        _ = soup.find('div', class_="header wrapper").extract()
        _ = soup.find('div', class_="RecentPosts").extract()
        _ = soup.find('div', class_="side e_col side_col w2_5").extract()
        _ = soup.find('div', class_=" footer wrapper").extract()

        return cleaner.clean_html(soup.prettify())

    def img_process(self, html):
        soup = BeautifulSoup(html)
        for img in soup('img'):
            img_url = img['src']
            if img_url not in self.img_list.keys(): # save img to local
                req_bin = requests.get(img_url, headers=headers, timeout=1).content
                image = Image.open(BytesIO(req_bin))
                image_name = str(hash(img_url))+'.png'
                image.save(self.images_loc+image_name)
                self.img_list['img_url'] = image_name
            else:
                image_name = self.img_list['img_url']
            img['src'] = 'images/'+image_name

        return soup.prettify()

    def get_articles(self):
        for article in tqdm(self.articles):
            req = requests.get(csm_domain+article['link'], headers=headers, timeout=1)
            sim_html = self.simplify_html(req.text)
            sim_html = self.img_process(sim_html)
            article['content'] = sim_html

    def save_ebook(self):
        pass





