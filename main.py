import re
from bs4 import BeautifulSoup
import requests
from lxml.html.clean import Cleaner
from PIL import Image
from io import BytesIO
from tqdm import tqdm
import os
import mimetypes
from time import strftime, sleep
import random

timeout = 2
csm_domain = r'https://chuansongme.com'
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.40 Safari/537.36",
    "referer": csm_domain
}
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
        print('initialization')
        self.sess = requests.Session()
        adapter = requests.adapters.HTTPAdapter(max_retries=10)
        self.sess.mount('http://', adapter)
        self.sess.mount('https://', adapter)
        self.url = url
        self.html = self.sess.get(self.url, headers=headers, timeout=timeout)
        self.home = BeautifulSoup(self.html.text, features='lxml')
        self.bookName = self.home.h1.text
        self.OEBPS_loc = self.bookName + '/' + 'OEBPS/'
        self.images_loc = self.bookName + '/' + 'OEBPS/images/'
        if not os.path.exists(self.bookName):
            os.mkdir(self.bookName)
            os.mkdir(self.OEBPS_loc)
            os.mkdir(self.images_loc)
        self.articles = []
        self.img_list = {}

    def get_list_of_articles(self):
        #  get all pages
        pages = self.home.find('span', style=pages_style)
        page_num = len(pages.find_all('a')) + 1
        # page_num = 1 # debug

        for page in range(page_num):
            sleep(random.random())
            html = self.sess.get(self.url, params={'start': page * 12}, headers=headers, timeout=timeout)
            soup = BeautifulSoup(html.text, features='lxml')
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
        soup = BeautifulSoup(html, features='lxml')
        article = soup.find('div', id="js_article")

        try:
            # _ = soup.find('div', class_="header wrapper").extract()
            # _ = soup.find('div', class_="RecentPosts").extract()
            # _ = soup.find('div', class_="side e_col side_col w2_5").extract()
            # _ = soup.find('div', id='wrapper').extract()
            # _ = soup.find('div', style='padding:5px 5px 0px 5px;border-bottom:1px dotted #C8D8F2; height:30px;margin:5px 0px 0px 0px;border-top:1px dotted #C8D8F2;').extract()
            # _ = soup.find('div', class_="footer wrapper").extract()
            _ = article('section', class_="xmt-style-block")[-1].extract()
        except:
            pass

        return cleaner.clean_html(str(article))

    def img_process(self, html):
        soup = BeautifulSoup(html, features='lxml')
        for img in soup('img'):
            try:
                img_url = img['src']
            except:
                _ = img.extract()
                continue
            if img_url is '':
                continue
            if img_url not in self.img_list.keys():  # save img to local

                # sleep(random.random())
                if not re.match('http', img_url):
                    if re.match('//', img_url):
                        img_url = 'https:' + img_url
                    else:
                        img_url = csm_domain+img_url
                try:
                    req = self.sess.get(img_url, headers=headers, timeout=timeout)
                    image = Image.open(BytesIO(req.content))
                    image_name = 'img' + str(hash(img_url)) + '.png'
                    image.save(self.images_loc + image_name)
                    self.img_list['img_url'] = image_name
                except:
                    img['src'] = ''
                    continue
            else:
                image_name = self.img_list['img_url']
            img['src'] = 'images/' + image_name

        return soup.prettify()

    def get_articles(self):
        print('download articles')
        del_articles =[]
        for article in tqdm(self.articles):

            sleep(random.random())
            req = self.sess.get(csm_domain + article['link'], headers=headers, timeout=timeout)

            if req.status_code != 200:
                print("\nArticle: {} is not available\n".format(article['title']))
                del_articles.append(article)
                continue

            sim_html = self.simplify_html(req.text)
            sim_html = self.img_process(sim_html)
            article['content'] = sim_html
        if len(del_articles) > 0:
            for article in del_articles:
                self.articles.remove(article)

    def save_ebook(self):
        print('create ebook')
        intCounter = 0
        strTOC = ""
        strHTML4Index = ""
        mimetypes.init()
        manifest = ""
        spine = ""

        for article in tqdm(self.articles):
            intCounter += 1
            strLocalFilename = 'post' + str(hash(article['link'])) + '.html'
            strLocalFile = self.OEBPS_loc + strLocalFilename
            strBody = BeautifulSoup(article['content'], features='lxml').body
            strHTML4Post = ('<!DOCTYPE html\n'
                            'PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"\n'
                            '"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">\n'
                            '<html xmlns="http://www.w3.org/1999/xhtml" lang="zh" xml:lang="zh">\n'
                            '    <head>\n'
                            '    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />\n'
                            '    <title>'
                            ) + article[
                               'title'] + '</title><style type="text/css">body{font-family: arial, sans-serif;}</style></head>' + \
                           str(strBody) + '</html>'
            with open(strLocalFile, 'w') as f:
                f.write(strHTML4Post)
            mime = mimetypes.guess_type(strLocalFile, strict=True)
            manifest += '\t<item id = "file_%s" href="%s" media-type="%s"/>\n' % (intCounter, strLocalFilename, mime[0])
            spine += '\n\t<itemref idref="file_%s" />' % (intCounter)
            strTOC += '''<navPoint class="chapter " id="{0:s}" playorder="{1:s}">
             <navLabel>
             <text>{2:s}</text>
             </navLabel>
             <content src="{3:s}"/>
             </navPoint>'''.format(str(intCounter), str(intCounter + 1), article['title'], strLocalFilename)
            strHTML4Index = strHTML4Index + '<li><a href="' + strLocalFilename + '">' + article['title'] + '</a></li>\n'

        # add images to manifest
        for _, image_name in self.img_list.items():
            intCounter += 1
            strLocalFile = self.images_loc + image_name
            mime = mimetypes.guess_type(strLocalFile, strict=True)
            manifest += '\t<item id = "file_%s" href="images/%s" media-type="%s"/>\n' % (intCounter, image_name, mime[0])

        # build index
        strCurrentTimestamp = str(strftime("%Y-%m-%d %H:%M:%S"))
        strHTML4Index = ('<!DOCTYPE html\n'
                         'PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"\n'
                         '"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">\n'
                         '<html xmlns="http://www.w3.org/1999/xhtml" lang="zh" xml:lang="zh">\n'
                         '    <head>\n'
                         '    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />\n'
                         '    <title>'
                         ) + self.bookName + "文章汇总</title>\n</head>\n<body>\n<h2>微信公众号：" + self.bookName + "</h2>\n<p>共" + \
                        str(len(
                            self.articles)) + "篇文章，制作时间：<em>" + strCurrentTimestamp + "</em></p>\n<ol>\n" + strHTML4Index + "\n</ol>\n</body>\n</html>"
        with open(self.OEBPS_loc + 'index.html', 'w') as f:
            f.write(strHTML4Index)

        # build opf
        template_top1 = '''<package xmlns="http://www.idpf.org/2007/opf"
          unique-identifier="book-id"
          version="3.0" xml:lang="zh">
          <metadata >
          '''
        # <!-- TITLE -->
        template_title = '<dc:title>' + self.bookName + '</dc:title>'
        template_top2 = '''    <!-- AUTHOR, PUBLISHER AND PUBLICATION DATES-->
            <dc:creator></dc:creator>
            <dc:publisher></dc:publisher>
             <dc:date></dc:date>
             <meta property="dcterms:modified"></meta>
             <!-- MISC INFORMATION -->
              <dc:language>zh</dc:language>
              <dc:identifier id="book-id"></dc:identifier>
              <meta name="cover" content="img-cov" />
          <manifest>
          '''
        template_transition = '''</manifest>
          <spine toc="ncx">'''

        template_bottom = '''</spine>
        <guide>
        <reference type="toc" title="Table of Contents" href="index.html"></reference>
        </guide>
        </package>'''

        with open(self.OEBPS_loc + 'package.opf', 'w') as f:
            f.write(template_top1)
            f.write(template_title)
            f.write(template_top2)
            f.write(manifest)
            f.write('''<item id="toc" media-type="application/x-dtbncx+xml" href="toc.ncx"/>
            <item id="index" media-type="text/html" href="index.html"/>''')
            f.write(template_transition)
            f.write(spine)
            f.write('''<itemref idref="toc"/>
            <itemref idref="index"/>''')
            f.write(template_bottom)

        # build TOC
        strTOC = '''<?xml version="1.0" encoding="UTF-8"?>
        <!DOCTYPE ncx PUBLIC "-//NISO//DTD ncx 2005-1//EN"
        "http://www.daisy.org/z3986/2005/ncx-2005-1.dtd">

        <!--
        For a detailed description of NCX usage please refer to:
        http://www.idpf.org/2007/opf/OPF_2.0_final_spec.html#Section2.4.1
        -->

        <ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1" xml:lang="zh-CN">
        <head>
        <meta name="dtb:uid" content=""/>
        <meta name="dtb:depth" content="2"/>
        <meta name="dtb:totalPageCount" content="0"/>
        <meta name="dtb:maxPageNumber" content="0"/>
        </head>
        <navMap>
        <navPoint class="toc" id="toc" playOrder="1">
        <navLabel>
        <text>Table of Contents</text>
        </navLabel>
        <content src="index.html"/>
        </navPoint>''' + strTOC + '''</navmap>
        </ncx>'''
        with open(self.OEBPS_loc + 'toc.ncx', 'w') as f:
            f.write(strTOC)

if __name__ == "__main__":
    url = input('Enter the url of the account: \n')
    ebook = EBook(url)
    ebook.get_list_of_articles()
    ebook.get_articles()
    ebook.save_ebook()