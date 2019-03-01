from mtdownloader import MTDownloader
from phuburl import resolver as PageResolver
import requests
import json

socks5Proxy={"http":"http://127.0.0.1:1080","https":"https://127.0.0.1:1080"}

while True:
    try:
        url=input('Please input URL: ')
    except EOFError:
        break
    print('BEGIN')
    res=requests.get(url,proxies=socks5Proxy)
    info=PageResolver(res.text)
    print(info)
    downloader=MTDownloader(info['url'],filename=info['name'],timeout=None,proxy=socks5Proxy,debug=True)
    downloader.start()
    downloader.wait()
    print('DONE')
