#!/usr/bin/python


import sys
import pip

try:
    import requests
except ImportError as e:
        print(e)
        print("Attempting to install dependencies...")

        err = pip.run_install('--upgrade -r requirements.txt')

        if err:
            print("\nYou may need to %s to install dependencies." %
                  ['use sudo', 'run as admin'][sys.platform.startswith('win')])
        else:
            print("\nOk lets hope it worked\n")

import json
from time import sleep
from os.path import isfile
from datetime import datetime

def filewrite(data):
    with open("idcache.txt", "w") as f:
        for id in data:
            f.write(id["data"]["id"]+"\n")

def is_selfpost(data):
    if "reddit.com" in data["data"]["url"] and not "np.reddit.com" in data["data"]["url"]:
        return True
    else:
        return False

def is_preview(data):
    try:
        i = data["data"]["preview"]
        return True
    except:
        return False

def determine(data):
    if is_selfpost(data):
        return 0
    elif is_preview(data):
        return 1
    else:
        return 3

def get(sub):
    # An loop here is needed because for some reason html.json()["data]["children"] fails for no reason sporadically
    # Therefore if you loop it, it will eventually pass and return data.
    while True:
        try:
            html = requests.get("https://www.reddit.com/r/"+sub+"/new.json")
            data = html.json()["data"]["children"]
            return data
        except:
            pass

def truncate(text):
    if len(text) > 1650:
        i = 1600
        text = text[:i]
        while True:
            char = text[i]
            if char == " ":
                if text[i-1] == ".":
                    return text[i]+".."
                else:
                    return text[i]+"..."
            else:
                i -= 1
    return text

def makepost(data, footerimg):
    det = determine(data)
    if det == 0:
        description = truncate(data["data"]["selftext"])
        imageurl = None
    elif det == 1:
        description = data["data"]["url"]
        imageurl = data["data"]["preview"]["images"][0]["source"]["url"]
    elif det == 2:
        description = None
        imageurl = data["data"]["url"]
    elif det == 3:
        description = data["data"]["url"]
        imageurl = None
    ech = datetime.utcfromtimestamp(data["data"]["created_utc"]).strftime("%d/%m/%Y %H:%M:%S UTC")
    msg = {
        "embeds": [{
            "color": "16744192",
            "title": "/u/"+data["data"]["author"],
            "url": "https://www.reddit.com/u/" + data["data"]["author"],
            "author": {
                "name": data["data"]["title"],
                "url": "https://reddit.com"+data["data"]["permalink"]
            },
            "image": {
                "url": imageurl
            },
            "description": description,
            "footer": {
                "icon_url": footerimg,
                "text": "/r/"+data["data"]["subreddit"]+"  |  Created "+ ech
            }
        }]
    }
    if not imageurl:
        msg["embeds"][0].pop("image")
    if not description:
        msg["embeds"][0].pop("description")
    return msg

def post(data, url, img):
    msg = makepost(data, img)
    headers = {'Content-Type': 'application/json'}
    r = requests.post(url, data=json.dumps(msg), headers=headers)
    if r.status_code == 400:
        print("Post Failed, Error 400")
    else:
        print("Posted "+data["data"]["title"])
    print("Code "+str(r.status_code))
    print("")
    sleep(2)

if __name__ == "__main__":
    subreddit = str(input("Subreddit: ")).lower()
    url = str(input("Webhook URL: "))
    img = str(input("Footer Image (Leave blank if you don't want/have one): "))
    x = False
    while True:
        data = get(subreddit)
        if isfile("./idcache.txt"):
            file =  open("idcache.txt","r")
            f = file.read().splitlines()
            file.close()
            i = 25 # Always will be 25 because 25 entries and a empty 26th line
            for id in reversed(data):
                i -= 1
                if id["data"]["id"] not in f:
                    post(data[i], url, img)
                    x = True
        filewrite(data)
        if not x:
            print("No new posts found...")
        print("Sleeping for 5 Minutes...")
        print("\n")
        sleep(300) # 5 Minutes in seconds