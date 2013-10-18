from setuptools import setup, find_packages
setup(
    name = "dingpa",
    version = "1.0",
    packages = find_packages(exclude=["test/*"]),
    scripts = ['dingpa_crawl.py'],
    author='xlvector',
    author_email = 'xlvector@gmail.com',
    description = 'Python web crawler with rich config'
)
