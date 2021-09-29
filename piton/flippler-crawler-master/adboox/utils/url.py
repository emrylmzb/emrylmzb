import os.path
from urllib.parse import urlparse

def get_ext_from_url(url):
        path = urlparse(url).path
        ext = os.path.splitext(path)[1].strip(".").title()
        return ext