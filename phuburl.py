import re
import json

def validate(name):
    patternStr = r"[\/\\\:\*\?\"\<\>\|]"  # '/ \ : * ? " < > |'
    return re.sub(patternStr, "_", name)

def resolver(pageContent):
    title=re.findall(r'<title>(.*?)<\/title>',pageContent)
    if(not title):
        return None
    title=validate(title[0])
    result=re.search(r'"mediaDefinitions".*?\[.*?\]',pageContent)
    if(not result):
        return None
    result=result.group()
    j=json.loads("{{{}}}".format(result))
    for video in j["mediaDefinitions"]:
        if(video["defaultQuality"]):
            url=video["videoUrl"]
            return {'url':url,'quality':video["quality"],'name':'{}.{}'.format(title,video["format"])}
    return None
