import urllib2, sqlite3, hashlib, re
import html_parser
import url_util

def download(url, timeout):
    try:
        request = urllib2.Request(url)
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
    def __init__(self, config):
        self.init_crawler_db()
        source = ''
        seed_urls = []
        updates = []
        oneoffs = []
        self.sources = []
        for line in file(config):
            line = line.strip()
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

    def init_crawler_db(self):
        self.db = sqlite3.connect('crawler.db')
        self.cursor = self.db.cursor()
        self.cursor.execute('create table if not exists urls (id bigint not null, url varchar(255) not null, updated_at timestamp default current_timestamp, primary key (id))')
        self.db.commit()

        self.cursor.execute('create table if not exists link_graph (src_id bigint not null, dst_id bigint not null, anchor_text varchar(255) not null, updated_at timestamp default current_timestamp, primary key (src_id, dst_id))')
        self.db.commit()

    def insert_url(self, url):
        url_id = get_url_hash(url)
        self.cursor.execute('replace into urls (id, url) values (?, ?)', (url_id, url))
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
    
    def encodeUTF8(self, buf, charset):
        try:
            ret = buf.decode(charset).encode('utf-8')
            return ret
        except Exception, e:
            return ''

    def encodeUnicode(self, buf, charset):
        try:
            ret = buf.decode(charset)
            return ret
        except Exception, e:
            return ''

    def crawl_source(self, seed_urls, update_patterns, oneoff_patterns, limit = 100):
        crawl_queue = [x for x in seed_urls if self.match_patterns(x, update_patterns)]
        visited = set()
        while len(crawl_queue) > 0 and len(visited) < limit:
            try:
                url = crawl_queue.pop(0)
                url_id = get_url_hash(url)
                if url_id in visited:
                    continue
                if self.match_patterns(url, update_patterns) == False:
                    continue
                code, html = download(url, timeout = 10)
                if html == None:
                    continue
                visited.add(url_id)
                doc = html_parser.HTMLParser(html)
                print url, len(visited), self.encodeUTF8(doc.title(), doc.charset())
                for sub_url, anchor_text in doc.links():
                    sub_url = url_util.combine_url(url, sub_url)
                    anchor_text = self.encodeUnicode(anchor_text, doc.charset())
                    if self.match_patterns(sub_url, update_patterns) or self.match_patterns(sub_url, oneoff_patterns):
                        self.insert_url(sub_url)
                        self.insert_to_link_graph(url, sub_url, anchor_text)
                        crawl_queue.append(sub_url)
            except Exception, e:
                print e
    def crawl(self):
        for source, seed_urls, updates, oneoffs in self.sources:
            print source, seed_urls, updates, oneoffs
            self.crawl_source(seed_urls, updates, oneoffs)
