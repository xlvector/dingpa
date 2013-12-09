import urllib2

class HTMLNode:
    def __init__(self, html):
        self._html = html
        self._valid = 1
        self._end_tag_index = -1
        self._tag = ''
        self._params = {}

        if self.is_start_tag():
            self.parse_start_tag()
        elif self.is_end_tag():
            self._tag = self._html.strip('</>')

    def valid(self):
        return self._valid

    def set_valid(self, v):
        self._valid = v

    def set_end_tag_index(self, i):
        self._end_tag_index = i

    def get_end_tag_index(self):
        return self._end_tag_index

    def set_index(self, i):
        self._index = i

    def get_index(self):
        return self._index

    def tag(self):
        return self._tag.lower()

    def html(self):
        return self._html

    def attr(self, key):
        if self._params != None and key in self._params:
            return self._params[key]
        return None

    def is_close_tag(self):
        if self.is_start_tag() and self._html[-2] == '/':
            return True
        else:
            return False

    def is_start_tag(self):
        if len(self._html) < 2:
            return False
        if self._html[0] == '<' and self._html[-1] == '>' and self._html[1] != '/':
            return True
        else:
            return False

    def is_end_tag(self):
        if len(self._html) < 3:
            return False
        if self._html[0] == '<' and self._html[-1] == '>' and self._html[1] == '/':
            return True
        else:
            return False

    def is_tag(self):
        if len(self._html) == 0:
            return False
        if self._html[0] == '<':
            return True
        else:
            return False

    def split(self, buf):
        n = 0
        tk = ''
        ret = []
        for ch in buf:
            if ch == ' ' and n % 2 == 0:
                if len(tk) > 0:
                    ret.append(tk)
                tk = ''
            tk += ch
            if ch == '\"':
                n += 1
        if len(tk) > 0:
            ret.append(tk)
        return ret

    def params(self):
        return self._params

    def parse_start_tag(self):
        buf = self._html.strip('<>')
        tks = self.split(buf)
        if len(tks) == 0:
            return
        self._tag = tks[0]
        self._params = {}
        for tk in tks:
            if tk.find('=') < 0:
                continue
            k, v = tk.split('=', 1)
            k = k.strip().lower()
            v = v.strip('\"')
            self._params[k] = v

class HTMLParser:
    def __init__(self, html):
        self._nodes = self.tokenize(html)
        self._links = []
        self._title = ''
        self._charset = 'utf-8'
        self.build_dom()
        self._delete_chars = set(['<', '>', '[', ']', '-', '!'])

    def inner_text(self, k):
        i = k - 1
        ret = ''
        while i <= self._nodes[k].get_end_tag_index():
            i += 1
            if self._nodes[i].is_tag():
                continue
            else:
                ret += self._nodes[i].html()
        return ret

    def get_elements_by_attributes(self, search_attr, expect_value, within_node_index = -1):
        begin_index = 0
        end_index = len(self._nodes)

        if within_node_index >= 0 and within_node_index < end_index:
            begin_index = within_node_index
            end_index = self.node(begin_index).get_end_tag_index()

        ret = []
        for i in range(begin_index, end_index):
            node = self._nodes[i]
            value = node.attr(search_attr)
            if search_attr == 'tag' and node.is_start_tag():
                value = node.tag()
            if value != None and value == expect_value:
                ret.append(i)
        return ret

    def node(self, i):
        if i < 0 or i >= len(self._nodes):
            return None
        else:
            return self._nodes[i]

    def nodes(self):
        return self._nodes

    def links(self):
        return self._links

    def print_nodes(self):
        for node in self._nodes:
            if node.is_start_tag():
                print node.tag()
    
    def clean_html(self):
        ret = ''
        for node in self._nodes:
            if node.valid() == 1:
                ret += node.html() + ' '
        return ret

    def clean_text(self, buf):
        ret = ''
        for ch in buf:
            if ch in self._delete_chars:
                continue
            ret += ch
        return ret

    def text(self):
        ret = ''
        i = -1
        while i < len(self._nodes):
            i += 1
            if i >= len(self._nodes):
                break
            node = self._nodes[i]
            if node.is_close_tag():
                continue
            elif node.is_start_tag():
                if node.tag() in ['a', 'link', 'script', 'option', 'style']:
                    if node.get_end_tag_index() > 0:
                        i = node.get_end_tag_index()
                    continue
            elif node.is_end_tag():
                continue
            else:
                buf = node.html().strip()
                if len(buf) > 0:
                    ret += self.clean_text(buf) + '\n'
        return ret

    def build_dom(self):
        for i in range(len(self._nodes)):
            self._nodes[i].set_index(i)
        stack = []
        for node in self._nodes:
            if node.tag() == 'meta':
                content = node.attr('content')
                if content == None:
                    continue
                tks = content.split(';')
                for tk in tks:
                    if tk.find('charset=') >= 0:
                        self._charset = tk.split('=')[1]
                continue
            elif node.is_end_tag():
                inner_text = ''
                valid = 1
                if node.tag() in ['script', 'style']:
                    valid = 0
                while len(stack) > 0:
                    v = stack.pop()
                    v.set_valid(valid)
                    if False == v.is_start_tag() and False == v.is_end_tag():
                        inner_text = v.html() + ' ' + inner_text
                    if v.is_start_tag() and v.tag() == node.tag():
                        v.set_end_tag_index(node.get_index())
                        if v.tag() == 'title':
                            self._title = inner_text.strip()
                        elif v.tag() == 'a' and v.attr('href') != None:
                            self._links.append((v.attr('href'), inner_text.strip()))
                        break
            else:
                stack.append(node)

    def charset(self):
        if self._charset == 'gb2312':
            return 'gb18030'
        return self._charset

    def title(self):
        return self._title
                    
    
    def tokenize(self, html):
        ret = []
        buf = ''
        for ch in html:
            if ch == '<':
                ret.append(HTMLNode(buf))
                buf = ch
            elif ch == '>':
                buf += ch
                ret.append(HTMLNode(buf))
                buf = ''
            else:
                buf += ch
        return ret

if __name__ == '__main__':
    html = urllib2.urlopen('http://www.szxuexiao.com/news/html/2013/11/2376.html').read()
    parser = HTMLParser(html)

    print parser.charset()
    print parser.title().decode(parser.charset()).encode('utf-8')
    print parser.links()
    print parser.text().decode(parser.charset()).encode('utf-8')
