# -*- coding: utf-8 -*-

import urllib2, sqlite3, hashlib, re, random, os
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
        return (200, response.read())
    except urllib2.HTTPError, e:
        return_code = e.getcode()
    except urllib2.URLError, e:
        return_code = -1
    except socket.timeout:
        return_code = -2
    return (return_code, None)

def get_url_hash(url):
    return int(hashlib.sha224(url).hexdigest(), 16) % (1 << 63)

class Crawler:
    def __init__(self, config, db_name, shard, total):
        self.db_root = db_name + '.' + str(total) 
        self.db_name = db_name + '.' + str(total) + '.' + str(shard)
        self.total = total
        self.shard = shard
        self.init_crawler_db()
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
        self.cursor.execute('select src_id from link_graph')
        ret = set()
        for uid, in self.cursor.fetchall():
            ret.add(uid)
        return ret

    def get_new_urls(self):
        ret = set()

        for i in range(self.total):
            db = sqlite3.connect(self.db_root + '.' + str(i))
            db.text_factory = lambda x: unicode(x, 'utf-8', 'ignore')
            cursor = db.cursor()
            cursor.execute('select id, url from urls')
            for uid, url in cursor.fetchall():
                if uid % self.total == self.shard:
                    ret.add(url)
        return ret

    def init_crawler_db(self):
        self.db = sqlite3.connect(self.db_name)
        self.cursor = self.db.cursor()
        self.cursor.execute('create table if not exists urls (id bigint not null, url varchar(255) not null, html blob, updated_at timestamp default current_timestamp, primary key (id))')
        self.db.commit()

        self.cursor.execute('create table if not exists link_graph (src_id bigint not null, dst_id bigint not null, anchor_text varchar(255) not null, updated_at timestamp default current_timestamp, primary key (src_id, dst_id))')
        self.db.commit()

        self.db.text_factory = lambda x: unicode(x, 'utf-8', 'ignore')

    def insert_url(self, url, html):
        url_id = get_url_hash(url)
        if html != None:
            if len(html) < 1500000:
                self.cursor.execute('replace into urls (id, url, html) values (?, ?, ?)', (url_id, url, sqlite3.Binary(compress_util.compress(html))))
        else:
            self.cursor.execute('insert or ignore into urls (id, url) values (?, ?)', (url_id, url))
        self.db.commit()

    def insert_to_link_graph(self, src_url, dst_url, anchor_text):
        src_id = get_url_hash(src_url)
        dst_id = get_url_hash(dst_url)
        self.cursor.execute('replace into link_graph (src_id, dst_id, anchor_text) values (?, ?, ?)', (src_id, dst_id, anchor_text))
        self.db.commit()

    def print_urls(self, limit = 10):
        self.cursor.execute('select * from urls limit ' + str(limit))
        for e in self.cursor.fetchall():
            print e
            
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
            return ''

    def crawl_source(self, seed_urls, update_patterns, oneoff_patterns, limit = 500):
        pid = os.getpid()
        crawl_queue = [x for x in seed_urls if self.match_patterns(x, update_patterns)]
        crawl_queue += [x for x in self.get_new_urls()]
        visited = self.get_crawled_urls()
        crawled = 0
        queue_urls = []
        print pid, crawled, len(crawl_queue)
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
                        self.insert_to_link_graph(url, sub_url, anchor_text)
                        self.insert_url(sub_url, None)
                        if get_url_hash(sub_url) % self.total == self.shard:
                            crawl_queue.append(sub_url)
            except Exception, e:
                print 'exception', pid
                print e
                continue
        print pid, crawled, len(crawl_queue)

    def crawl(self):
        for source, seed_urls, updates, oneoffs in self.sources:
            self.crawl_source(seed_urls, updates, oneoffs)
