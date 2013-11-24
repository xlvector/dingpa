# -*- coding: utf-8 -*-

import sqlite3 as lite
import dingpa.html_parser as parser
import dingpa.compress_util
import jieba.posseg as pseg

for shard in range(10):
    con = lite.connect('edu.db.10.' + str(shard))
    con.text_factory = lambda x: unicode(x, 'utf-8', 'ignore')
    cur = con.cursor()
    cur.execute("SELECT url, html FROM urls where html is not null")
    
    for url, data, in cur.fetchall():
        try:
            data = dingpa.compress_util.decompress(data)
            doc = parser.HTMLParser(data)
            text = doc.text().decode(doc.charset().lower()).encode('utf-8')
            words = pseg.cut(text)
            ok = False
            for word in words:
                if word.flag == 'nr':
                    ok = True
                    break
            if False == ok:
                continue
            print '\t'.join([x.word.encode('utf-8') for x in words if len(x.word) > 0 and x.flag in ['nr', 'ns', 'nt', 'nz']])
        except Exception, e:
            continue
