from mtdownloader import MTDownloader
from mtdownloader import readable as readableSize
from phuburl import resolver as PageResolver
import requests
import json
import time

def readableTime(s):
    s=int(s)
    if(s<60):
        return '{}s'.format(s)
    elif(s<3600):
        return '{}m{}s'.format(s//60,s%60)
    else:
        return '{}h{}m{}s'.format(s//3600,(s%3600)//60,s%60)

socks5Proxy={"http":"http://127.0.0.1:1080","https":"https://127.0.0.1:1080"}

while True:
    try:
        url=input('Please input URL: ')
    except EOFError:
        break

    try:
        print('[BEGIN] {}'.format(url))
        res=requests.get(url,proxies=socks5Proxy)
        info=PageResolver(res.text)
        print(info)
        downloader=MTDownloader(info['url'],filename=info['name'],timeout=None,proxy=socks5Proxy,debug=True)
        time_before=time.time()
        downloader.start()
        downloader.wait()
        time_diff=time.time()-time_before
        print('[DONE] {} ({} in {} at {})'.format(info["name"],
            readableSize(downloader.length),readableTime(time_diff),
            '{}/s'.format(readableSize(downloader.length/time_diff))))
    except Exception as e:
        print('[Error] {}'.format(e))
    
