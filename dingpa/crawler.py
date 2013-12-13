# -*- coding: utf-8 -*-

import urllib2, hashlib, re, random, os, time, traceback, httplib
from CodernityDB.database import Database
import html_parser
import url_util, compress_util
import gzip
import cStringIO
import socket
import random

def random_ip():
    return '.'.join([str(random.randint(23, 179)) for i in range(4)])

def download(url, timeout):
    headers = {'Referer': url, \
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/31.0.1650.57 Safari/537.36',\
            'X-Forwarded-For' : random_ip()}
    try:
        request = urllib2.Request(url = url, headers = headers)
        response = urllib2.urlopen(request, timeout = timeout)
        content_type = response.info()['Content-Type']
        if content_type == None or content_type.find('text/html') < 0:
            return ('none_html', None)
        else:
            return (200, response.read())
    except urllib2.HTTPError, e:
        return_code = e.getcode()
    except urllib2.URLError, e:
        return_code = 'URLError'
    except socket.timeout:
        return_code = 'timeout'
    except httplib.BadStatusLine:
        return_code = 'BadStatusLine'
    return (return_code, None)

def get_url_hash(url):
    return int(hashlib.sha224(url).hexdigest(), 16) % (1 << 63)

class Crawler:
    def __init__(self, config, name, shard, total):
        self.name = name
        self.db = Database(name + '.' + str(total) + '.' + str(shard) + '.db')
        if self.db.exists():
            self.db.open()
        else:
            self.db.create()
        self.docs = {}
        self.total = total
        self.shard = shard
        self.prev_getaddrinfo = socket.getaddrinfo
        self.dns_cache = {}

        socket.getaddrinfo = self.getaddrinfo

        source = ''
        seed_urls = []
        updates = []
        oneoffs = []
        self.sources = []
        for line in file(config):
            line = line.strip()
            if len(line) == 0:
                continue
            if line[0] == '#':
                continue
            if line[0] == '[':
                source = line
            elif line.find('=') > 0:
                k, v = line.split('=', 1)
                k = k.strip()
                v = v.strip()
                if k == 'update':
                    updates.append(v)
                elif k == 'oneoff':
                    oneoffs.append(v)
                elif k == 'url':
                    seed_urls.append(v)
            elif len(line) == 0:
                if source != '':
                    self.sources.append((source, seed_urls, updates, oneoffs))
                source = ''
                seed_urls = []
                updates= []
                oneoffs = []
        if source != '':
            self.sources.append((source, seed_urls, updates, oneoffs))


    def getaddrinfo(self, *args):
        if args in self.dns_cache:
            return self.dns_cache[args]
        else:
            res = self.prev_getaddrinfo(*args)
            self.dns_cache[args] = res
            return res

    def get_crawled_urls(self):
        ret = set()
        for doc in self.db.all('id'):
            if doc['html'] != '':
                ret.add(doc['id'])
        return ret

    def get_new_urls(self):
        ret = set()

        for doc in self.db.all('id'):
            if doc['html'] == '' and doc['id'] % self.total == self.shard:
                ret.add(doc['url'])

        for i in range(self.total):
            if i == self.shard:
                continue
            db = Database(self.name + '.' + str(self.total) + '.' + str(i) + '.db')
            if db.exists():
                db.open()
            else:
                continue
            for doc in db.all('id'):
                if len(doc['html']) == 0 and doc['id'] % self.total == self.shard:
                    ret.add(doc['url'])
        return ret

    def insert_url(self, url, html):
        url_id = get_url_hash(url)
        doc = {'url': url, 'html': compress_util.compress(html), 'id': url_id, 'updated_at': time.time()}
        if html == None or html == '':
            if url_id not in self.docs:
                self.docs[url_id] = doc
        else:
            self.docs[url_id] = doc
            
    def match_single_pattern(self, url, pattern):
        match = re.match(pattern, url)
        if match and match.group(0) == url:
            return True
        else:
            return False

    def match_patterns(self, url, patterns):
        for pattern in patterns:
            if self.match_single_pattern(url, pattern):
                return True
        return False

    def encode_unicode(self, buf, charset):
        try:
            ret = buf.decode(charset)
            return ret
        except Exception, e:
            print e
            return ''

    def crawl_source(self, seed_urls, update_patterns, oneoff_patterns, limit = 500):
        pid = os.getpid()

        crawl_queue = [x for x in seed_urls if self.match_patterns(x, update_patterns)]
        crawl_queue += [x for x in self.get_new_urls()]
        visited = self.get_crawled_urls()
        crawled = 0
        queue_urls = []
        print pid, crawled, len(crawl_queue)
        code_count = {}
        while len(crawl_queue) > 0 and crawled < limit:
            try:
                url = crawl_queue.pop(0)
                url_id = get_url_hash(url)
                if url_id % self.total != self.shard:
                    continue
                if url_id in visited:
                    continue
                if self.match_patterns(url, update_patterns) == False:
                    continue
                code, html = download(url, timeout = 5)
                if code not in code_count:
                    code_count[code] = 1
                else:
                    code_count[code] += 1
                if html == None:
                    continue
                self.insert_url(url, html)
                visited.add(url_id)
                crawled += 1
                print pid, crawled, len(crawl_queue), url
                doc = html_parser.HTMLParser(html)
                for sub_url, anchor_text in doc.links():
                    sub_url = sub_url.strip(' \'')
                    sub_url = url_util.combine_url(url, sub_url)
                    anchor_text = self.encode_unicode(anchor_text, doc.charset())

                    if self.match_patterns(sub_url, update_patterns) or self.match_patterns(sub_url, oneoff_patterns):
                        self.insert_url(sub_url, '')
                        if get_url_hash(sub_url) % self.total == self.shard:
                            crawl_queue.append(sub_url)
            except Exception, e:
                print 'exception', pid
                print e
                continue
        print pid, crawled, len(crawl_queue)
        print code_count

    def crawl(self):
        for source, seed_urls, updates, oneoffs in self.sources:
            self.crawl_source(seed_urls, updates, oneoffs)
            for uid, doc in self.docs.items():
                self.db.insert(doc)
        self.db.close()
