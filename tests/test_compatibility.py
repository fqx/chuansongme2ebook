"""Small offline fixtures; real requests/urllib3 transport, loopback only."""
from contextlib import ExitStack
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
from pathlib import Path
import os
import tempfile
import threading
import unittest
from unittest.mock import patch
import zlib

from bs4 import BeautifulSoup
from PIL import Image
import requests
import main

HOME = '''<html><body><h1>Fixture Book</h1>
<span style="font-size: 1em;font-weight: bold"></span>
<h2><a href="/article">Fixture title</a><span class="timestamp">2026-10-01</span></h2>
</body></html>'''
ARTICLE = '''<html><body><div id="js_article"><p>Fixture article text.</p>
<script>removed()</script><img src="/image.png"><section class="xmt-style-block">footer</section>
</div></body></html>'''


class CompatibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        image = BytesIO()
        Image.new('RGB', (2, 3), 'blue').save(image, format='PNG')
        cls.image = image.getvalue()

        class Handler(BaseHTTPRequestHandler):
            protocol_version = 'HTTP/1.1'

            def do_GET(self):
                route = self.path.split('?')[0]
                if route == '/redirect':
                    self.send_response(302)
                    self.send_header('Location', '/article')
                    self.send_header('Content-Length', '0')
                    self.end_headers()
                    return
                if route == '/missing':
                    body, status = b'not found', 404
                else:
                    status = 200
                    body = cls.image if route == '/image.png' else (
                        HOME if route == '/account/fixture' else ARTICLE).encode()
                self.send_response(status)
                self.send_header('Content-Type', 'image/png' if route == '/image.png'
                                 else 'text/html; charset=utf-8')
                if route in ('/article', '/deflate'):
                    body = zlib.compress(body)
                    self.send_header('Content-Encoding', 'deflate')
                    self.send_header('Transfer-Encoding', 'chunked')
                    self.end_headers()
                    for start in range(0, len(body), 7):
                        chunk = body[start:start + 7]
                        self.wfile.write(f'{len(chunk):x}\r\n'.encode() + chunk + b'\r\n')
                    self.wfile.write(b'0\r\n\r\n')
                else:
                    self.send_header('Content-Length', str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)

            def log_message(self, *args):
                pass

        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.origin = f'http://127.0.0.1:{cls.server.server_port}'

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)

    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        # Disable environment proxy discovery and deny unexpected destinations.
        send = requests.Session.send
        origin = self.origin
        def local_send(session, request, **kwargs):
            if not request.url.startswith(origin + '/'):
                raise AssertionError('Non-loopback request forbidden: ' + request.url)
            return send(session, request, **kwargs)
        self.stack.enter_context(patch.object(requests.Session, 'send', local_send))
        self.stack.enter_context(patch.dict(os.environ, {'NO_PROXY': '*', 'no_proxy': '*'}))
        self.stack.enter_context(patch.object(main, 'csm_domain', self.origin))
        self.stack.enter_context(patch.object(main, 'urlisgood',
                                            lambda url: url == self.origin + '/account/fixture'))
        self.stack.enter_context(patch.object(main, 'sleep'))
        temporary = self.stack.enter_context(tempfile.TemporaryDirectory())
        previous = os.getcwd()
        os.chdir(temporary)
        self.stack.callback(os.chdir, previous)

    def ebook(self):
        book = main.EBook(self.origin + '/account/fixture')
        self.stack.callback(book.sess.close)
        return book

    def test_article_image_to_ebook_files(self):
        book = self.ebook()
        book.get_list_of_articles()
        self.assertEqual(len(book.articles), 1)
        book.get_articles()
        self.assertIn('Fixture article text.', book.articles[0]['content'])
        self.assertNotIn('<script', book.articles[0]['content'])
        self.assertNotIn('footer', book.articles[0]['content'])
        images = list(Path(book.images_loc).glob('*.png'))
        self.assertEqual(len(images), 1)
        with Image.open(images[0]) as image:
            self.assertEqual(image.size, (2, 3))
        book.save_ebook()
        for name in ('index.html', 'package.opf', 'toc.ncx'):
            self.assertTrue((Path(book.OEBPS_loc) / name).is_file())
        self.assertIn(images[0].name, (Path(book.OEBPS_loc) / 'package.opf').read_text())
        self.assertEqual(len(list(Path(book.OEBPS_loc).glob('post*.html'))), 1)

    def test_deflate_chunked_stream_and_redirect(self):
        with requests.Session() as session:
            session.trust_env = False
            with session.get(self.origin + '/deflate', stream=True, timeout=2) as response:
                self.assertEqual(b''.join(response.iter_content(5)).decode(), ARTICLE)
            response = session.get(self.origin + '/redirect', timeout=2)
            self.assertEqual(response.text, ARTICLE)
            self.assertEqual(len(response.history), 1)

    def test_http_error_removes_unavailable_article(self):
        book = self.ebook()
        book.articles = [{'link': '/missing', 'title': 'Missing', 'date': '2026-10-01'}]
        book.get_articles()
        self.assertEqual(book.articles, [])

    def test_date_filter_skips_outside_range(self):
        book = self.ebook()
        book.get_list_of_articles()
        book.get_articles(start='2026-10-02')
        self.assertEqual(book.articles, [])

    def test_soupsieve_selector_boundaries(self):
        soup = BeautifulSoup('<ol><li>A</li><li>B</li><li>C</li></ol>', 'lxml')
        self.assertEqual([li.text for li in soup.select('li:nth-child(2n-2)')], ['B'])
        self.assertEqual([li.text for li in soup.select('li:nth-child(n-1)')], ['A', 'B', 'C'])


if __name__ == '__main__':
    unittest.main()
