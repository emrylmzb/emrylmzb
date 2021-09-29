from scrapy.http.cookies import CookieJar


def extract_cookie(name, response):
    cj = CookieJar()
    cj.extract_cookies(response, response.request)
    cookie = [c.value for c in cj if c.name == name]
    if cookie:
        return cookie[0]
