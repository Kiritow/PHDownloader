import requests
import threading
import os
import sys
import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def readable(n):
    if(n<1024):
        return "{} B".format(n)
    elif(n<1024**2):
        return "{:.2f} KB".format(n/1024)
    elif(n<1024**3):
        return "{:.2f} MB".format(n/(1024**2))
    else:
        return "{:.2f} GB".format(n/(1024**3))

# Used when partial download is not allowed, or the file is too small.
def SingleDownloader(url,filename,ua=None,timeout=None,chunkSize=1024*1024*10,proxy=None):
    headers={}
    if(ua):
        headers['User-Agent']=ua
    # Use stream option to avoid OOM.
    res=requests.get(url,headers=headers,timeout=timeout,stream=True,proxies=proxy)
    with open(filename,'wb') as f:
        for data in res.iter_content(chunkSize):
            f.write(data)

def GroupDownloader(url,fileObj,lock,L,R,ua=None,timeout=None,chunkSize=1024*1024*10,proxy=None):
    headers={}
    headers["Range"]='bytes={}-{}'.format(L,R)
    if(ua):
        headers['User-Agent']=ua
    # Also stream
    res=requests.get(url,headers=headers,timeout=timeout,stream=True,proxies=proxy)
    nWritten=0
    for data in res.iter_content(chunkSize):
        with lock:
            fileObj.seek(L+nWritten)
            fileObj.write(data)
            nWritten+=len(data)

def GroupWorker(*args,**kwargs):
    try:
        GroupDownloader(*args,**kwargs)
    except Exception as e:
        return (False,e)
    else:
        return (True,None)

class MTDownloader:
    '''Mutli-Thread Downloader

    `maxThread`: limit of spawned threads.

    `chunkSize`: used by GroupDownloader. not recommended to modify.

    `pieceSize`: used to calculate how many threads to spawn. If maxThread presents, maxThread wins.

    `thresholdSize`: If file length is less than it, use SingleDownloader instead.
    '''

    ua='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36'

    def __init__(self,url,filename=None,overwrite=False,timeout=5,maxThread=None,retryTime=2,chunkSize=1024*1024*10, pieceSize=1024*1024*30, thresholdSize=1024*1024*10,proxy=None,debug=False):
        self.url=url
        self.filename=filename
        self.overwrite=overwrite
        self.timeout=timeout
        self.maxThread=maxThread
        self.retryTime=retryTime
        self.chunkSize=chunkSize
        self.pieceSize=pieceSize
        self.threshold=thresholdSize
        self.proxy=proxy
        self.debug=debug

        self.exception=None
    
    def _fetch(self):
        headers={'User-Agent':self.ua}
        res=requests.head(self.url,headers=headers,allow_redirects=True,timeout=self.timeout,proxies=self.proxy)
        self.url=res.url
        self.length=int(res.headers["Content-Length"])
        if(not self.filename):
            self.filename=res.url.split('/')[-1]

        if(os.path.exists(self.filename) and not self.overwrite):
            raise Exception("file exists and overwrite is banned: {}".format(self.filename))
        
        headers["Range"]="bytes=0-{}".format(self.length//2)
        res=requests.head(self.url,headers=headers,timeout=5,proxies=self.proxy)
        self.supported = (res.status_code==206)

        logging.debug(r'''{}
URL: {}
Content length: {} ({})
Filename: {}
Range: {}
{}'''.format(
                '='*20,
                self.url,
                self.length,readable(self.length),
                self.filename,
                "Supported" if self.supported else "Not supported",
                '='*20
            ))

    def _download(self):
        if(not self.supported or (self.threshold and self.length<self.threshold)):
            logging.debug('calling SingleDownloader in thread {}...'.format(threading.currentThread().getName()))
            nRetry=0
            while True:
                try:
                    SingleDownloader(self.url,self.filename,
                        ua=self.ua,
                        timeout=self.timeout,
                        chunkSize=self.chunkSize,
                        proxy=self.proxy)
                except Exception as e:
                    logging.debug('{} SingleDownloader exception: {}'.format(threading.currentThread().getName(),e))
                else:
                    break
                
                nRetry+=1
                if(nRetry<self.retryTime):
                    logging.debug('{} retry SingleDownloader: {} of {}'.format(threading.currentThread().getName(),nRetry,self.retryTime))
                else:
                    raise Exception('SingleDownloader error') from e
        else:
            if(self.maxThread):
                nThread=self.maxThread
            else:
                nThread=self.length // self.pieceSize
            nThread=max(nThread,1)
            lock=threading.Lock()
            jobs=[]
            with open(self.filename,'wb') as f:
                for i in range(nThread):
                    L=i*self.pieceSize
                    R=min( (i+1)*self.pieceSize-1, self.length )
                    thisJob=threading.Thread(target=GroupWorker,
                        args=(self.url,f,lock,L,R),
                        kwargs={'ua':self.ua,'timeout':self.timeout,'chunkSize':self.chunkSize,'proxy':self.proxy})
                    logging.debug('call GroupDownloader in thread {}'.format(thisJob.getName()))
                    thisJob.start()
                    jobs.append(thisJob)
                for j in jobs:
                    j.join()
                    logging.debug('{} work done.'.format(j.getName()))

    def _work(self):
        try:
            self._fetch()
            self._download()
        except Exception as e:
            self.exception=e
        except:
            self.exception=sys.exc_info()[0]
            
    def start(self):
        self.tdev=threading.Event()
        self.td = threading.Thread(target=self._work)
        self.td.start()

    def wait(self,timeout=None):
        self.td.join(timeout)
        if(not self.td.isAlive()):
            if(self.exception is Exception):
                raise self.exception
            elif(self.exception):
                raise Exception(self.exception)
            else:
                return True
        else:
            return False
