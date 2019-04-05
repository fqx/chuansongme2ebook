import re
from bs4 import BeautifulSoup
import requests

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
        self.articles = []

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

    def get_articles(self):
        pass


