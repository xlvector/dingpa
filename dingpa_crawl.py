import dingpa.crawler
import sys

config, db_name, shard, total = sys.argv[1:]
shard = int(shard)
total = int(total)
crawler = dingpa.crawler.Crawler(config, db_name, shard, total)
crawler.crawl()
