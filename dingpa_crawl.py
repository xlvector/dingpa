import dingpa.crawler
import sys

if __name__ == '__main__':
	config, db_name, shard, total = sys.argv[1:]
	shard = int(shard)
	total = int(total)
	crawler = dingpa.crawler.Crawler(config, db_name, shard, total)
	crawler.crawl()
