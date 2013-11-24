def domain(url):
    if url.find('http://') != 0:
        return None
    tks = url.split('/')
    return tks[2]

def combine_url(base_url, relative_url):
    if relative_url.find('http://') == 0:
        return relative_url
    return 'http://' + domain(base_url) + '/' + relative_url.lstrip('/')
