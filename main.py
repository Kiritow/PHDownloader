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


def readConfig():
    try:
        with open('config.json') as f:
            config=json.loads(f.read())
            return config
    except FileNotFoundError:
        print('Unable to read config.')
        return None

def setupConfig():
    print('Welcome to PHDownloader config setup.')
    config={}
    str=input('Use proxy? (Y/n): ')
    if(str=='' or str.lower()=='y'):
        config["useProxy"]=True
        config["proxy"]={}
        str=input('http proxy (http://127.0.0.1:1080): ')
        if(str!=''):
            config["proxy"]["http"]=str
        else:
            config["proxy"]["http"]='http://127.0.0.1:1080'

        str=input('https proxy (https://127.0.0.1:1080): ')
        if(str!=''):
            config["proxy"]["https"]=str
        else:
            config["proxy"]["https"]='https://127.0.0.1:1080'
    else:
        config["useProxy"]=False
        config["proxy"]={"http":"http://127.0.0.1:1080","https":"https://127.0.0.1:1080"}
    str=input("Use timeout? (None): ")
    if(str=='' or str.lower()=='none'):
        config["timeout"]=None
    else:
        config["timeout"]=int(str)
    str=input("Use debug? (y/N): ")
    if(str=='' or str.lower()=='n'):
        config["debug"]=False
    else:
        config["debug"]=True
    str=input("Allow overwrite? (y/N): ")
    if(str=='' or str.lower()=='n'):
        config["overwrite"]=False
    else:
        config["overwrite"]=True
    
    with open('config.json','w') as f:
        f.write(json.dumps(config,indent=4))

    print('Config saved to `config.json`')
    return config

if __name__ == "__main__":
    config=readConfig()
    if(config is None):
        config=setupConfig()

    if(config["useProxy"]):
        theProxy=config["proxy"]
    else:
        theProxy=None

    while True:
        try:
            url=input('Please input URL: ')
        except EOFError:
            break

        try:
            print('[BEGIN] {}'.format(url))
            res=requests.get(url,proxies=theProxy)
            info=PageResolver(res.text)
            print(info)
            downloader=MTDownloader(info['url'],filename=info['name'],overwrite=config["overwrite"],timeout=config["timeout"],proxy=theProxy,debug=config["debug"])
            time_before=time.time()
            downloader.start()
            downloader.wait()
            time_diff=time.time()-time_before
            print('[DONE] {} ({} in {} at {})'.format(info["name"],
                readableSize(downloader.length),readableTime(time_diff),
                '{}/s'.format(readableSize(downloader.length/time_diff))))
        except Exception as e:
            print('[Error] {}'.format(e))
