Dingpa (钉耙)
======

python web crawler with rich config file


## Unit Test

Before install, you may want to run unittest. You can do it by

	python unittest/unittest_all.py


## Install

   python setup.py install

## Run

	dingpa_crawl.py [config_file_name] [db_prefix] [shard] [total]

	e.g.

	dingpa_crawl.py test.conf test.db 1 10

The example command will use test.conf as config file, and save data in test.db.10.1. Here the shard/total is for sharding. And example command will only crawl urls whose hash mod 10 equals 1.
 
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