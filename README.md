Dingpa (钉耙)
======

python web crawler with rich config file


## Unit Test

Before install, you may want to run unittest. You can do it by

python unittest/unittest_all.py


## Install

python setup.py install

## Run

cd test
dingpa_crawl.py test.conf

and crawled info are stored in crawler.db which is a sqlite3 db. In Mac, you can use
 SQLiteStudio to view the crawler.db
 
## Config File Format

Following is a sample config

	[edu]

	url = http://zsb.bupt.edu.cn/
	url = http://www.pku.edu.cn/

	update = http://[a-z0-9]+.[a-z0-9]+.edu.cn/.*/
	update = http://[a-z0-9]+.[a-z0-9]+.edu.cn/.*htm
	update = http://[a-z0-9]+.[a-z0-9]+.edu.cn/.*html

	[gov]

	url = http://www.gov.cn
	update = http://www.gov.cn/[a-z0-9]+/

Here, edu, gov is a group name of pages. url define seed urls. update define rules which use regex to filter pages you want to crawl.