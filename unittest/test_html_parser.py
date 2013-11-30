import sys

sys.path.append("../dingpa/")

import html_parser as parser

import random
import unittest

class TestSequenceFunctions(unittest.TestCase):

    def setUp(self):
        self.html = '<html><head><title>Hello World</title></head>' + \
                    '<body><h1>H1</h1><div Class=\"c1\">C1 <A HREF=\"#\">Click</a> Here</div></body></html>'

    def test_parser(self):
        doc = parser.HTMLParser(self.html)
        self.assertEqual(doc.title(), 'Hello World')

        e = doc.get_elements_by_attributes('tag', 'title')
        self.assertEqual(len(e), 1)
        self.assertEqual(doc.inner_text(e[0]), 'Hello World')

        e = doc.get_elements_by_attributes('tag', 'h1')
        self.assertEqual(len(e), 1)
        self.assertEqual(doc.inner_text(e[0]), 'H1')

        e = doc.get_elements_by_attributes('class', 'c1')
        self.assertEqual(doc.inner_text(e[0]), 'C1 Click Here')

        e = doc.get_elements_by_attributes('tag', 'a')
        node = doc.node(e[0])
        self.assertEqual(node.attr('href'), '#')

if __name__ == '__main__':
    unittest.main()