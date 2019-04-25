'''A script to scrap billboard chart using selenium and update a weekly playlist in spotify
   Author:ambati@stanford.edu'''
from datetime import date
import yaml
import os
import sys
import spotipy
import spotipy.util as util
import bs4
from selenium import webdriver
from collections import defaultdict
from selenium.webdriver.chrome.options import Options


def GetTags(tracks):
    '''HTML parser to extract the song titles and albums'''
    TrackDic = defaultdict(set)
    for item in tracks:
        if item:
            artist = item.find(
                "div", {"class": "chart-list-item__artist"}).get_text().strip().lower()
            song = item.find(
                "span", {"class": "chart-list-item__title-text"}).get_text().strip().lower()
            TrackDic[artist].add(song)
    return TrackDic


def SelScrap():
    '''A selenium instance to get the dynamic content of the webpage'''
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    Url = "https://www.billboard.com/charts/rock-songs"
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(Url)
    soup = bs4.BeautifulSoup(driver.page_source, 'lxml')
    tracks = soup.find_all("div", {"class": "chart-list-item"})
    TrackDic = GetTags(tracks=tracks)
    driver.quit()
    return TrackDic


def LoadConfig():
    '''Spotify client secret and credentials as described in spotify API'''
    CfgFile = open('SPConfig.yml', 'r')
    cfg = yaml.safe_load(CfgFile)
    return cfg


## implement search in spotify library
def SpotifyConn():
    '''Spotify conncetion instance'''
    SPConfig = LoadConfig()
    token = util.prompt_for_user_token(**SPConfig)
    sp = spotipy.Spotify(auth=token)
    return sp


def ParseSpotifySearch(TrackDic, sp):
    '''A search function to extract tracks from spotify master api'''
    SPResults = set()
    for k, v in TrackDic.items():
        artist = k
        for song in v:
            track = song
            track_id = sp.search(q='artist:' + artist + ' track:' +
                                 track, type='track', limit=1, market='us')
            if track_id:
                tracks = track_id['tracks']['items'] 
                if tracks:
                    tracklist = [i.get('uri').split(':')[-1]
                                 for i in tracks][0]
                    SPResults.add(tracklist)
            else:
                continue
    if len(SPResults) > 0:
        return SPResults
    else:
        exit()

def MakeWeeklyPlayList(sp):
    '''A spotify APPI call to make a playlist based on the date of the scrap'''
    dt= date.today()
    dtformat = dt.strftime("%d %B %Y")
    NamePlaylist = 'BillBoardRock '+dtformat
    playlists = sp.user_playlist_create(
        user='adityasai', name=NamePlaylist, public=True)
    GetID = playlists.get('uri')
    PLID = GetID.split(':')[2]
    return PLID

    
def UpdatePlaylist(TrackList, sp, PLID):
    '''Since spotify API allows for only adding 100 tracks at once to a playslist, recursive function to update the playlist 98 tracks at once'''
    username = 'adityasai'
    if len(TrackList) > 0 and len(TrackList) <= 100:
        sp.user_playlist_add_tracks(
            username, playlist_id=PLID, tracks=TrackList)
    else:
        n = len(TrackList)
        ChunkLoad = 98
        nchunk = 1
        ItemC = 1
        templist = []
        for i in range(0, n):
            if ItemC == ChunkLoad:
                templist.append(TrackList[i])
                nchunk += 1
                ItemC = 1
                UpdatePlaylist(TrackList=templist, sp=sp, PLID=PLID)
                templist =[]
            else:
                templist.append(TrackList[i])
                ItemC += 1
        UpdatePlaylist(TrackList=templist, sp=sp, PLID=PLID)


def main():
    TrackDic = SelScrap()
    print(TrackDic)
    sp = SpotifyConn()
    SPResults = ParseSpotifySearch(TrackDic=TrackDic, sp=sp)
    TrackList = [i for i in SPResults]
    #TrackNoDup = CheckForDup(TrackList)
    if TrackList:
        PLID = MakeWeeklyPlayList(sp=sp)
        UpdatePlaylist(TrackList=TrackList, sp=sp, PLID=PLID)
    else:
        exit()


if __name__ == "__main__":
    main()

