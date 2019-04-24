from datetime import date
import yaml
import sys
import os
import bs4
import sys
import spotipy
import spotipy.util as util
import os
from json.decoder import JSONDecodeError
from selenium import webdriver
from collections import defaultdict
from selenium.webdriver.chrome.options import Options


def GetTags(tracks):
    TrackDic = defaultdict(set)
    for item in tracks:
        if item:
            artist = item.find(
                "div", {"class": "chart-list-item__artist"}).get_text().strip().lower()
            song = item.find(
                "span", {"class": "chart-list-item__title-text"}).get_text().strip().lower()
            #album = item.find("div", {'class': "ts-artist tagstation__album"})
            TrackDic[artist].add(song)
    return TrackDic


def SelScrap():
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
    CfgFile = open('SPConfig.yml', 'r')
    cfg = yaml.safe_load(CfgFile)
    return cfg


## implement search in spotify library
def SpotifyConn():
    SPConfig = LoadConfig()
    token = util.prompt_for_user_token(**SPConfig)
    sp = spotipy.Spotify(auth=token)
    return sp


def ParseSpotifySearch(TrackDic, sp):
    SPResults = set()
    for k, v in TrackDic.items():
        artist = k
        for song in v:
            track = song
            track_id = sp.search(q='artist:' + artist + ' track:' +
                                 track, type='track', limit=1, market='us')
            if track_id:
                tracks = track_id['tracks']['items']  # [0].get('uri')
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
    dt= date.today()
    dtformat = dt.strftime("%d %B %Y")
    NamePlaylist = 'BillBoardRock '+dtformat
    playlists = sp.user_playlist_create(
        user='adityasai', name=NamePlaylist, public=True)
    GetID = playlists.get('uri')
    PLID = GetID.split(':')[2]
    return PLID

    
def UpdatePlaylist(TrackList, sp, PLID):
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


# def CheckForDup(TrackList):
#     NoDUPS = set()
#     CacheFile = '/home/labcomp/PLAYLIST.CACHE'
#     if os.path.exists(CacheFile):
#         Cache = open(CacheFile, 'r')
#         TrackIds = set(line.strip() for line in Cache)
#         Cache.close()
#         MakeDupFile = open(CacheFile, 'a')
#         for track in TrackList:
#             if track not in TrackIds:
#                 MakeDupFile.write(track+'\n')
#                 NoDUPS.add(track)
#         MakeDupFile.close()
#         NoDUPSList = [i for i in NoDUPS]
#         return NoDUPSList
#     else:
#         MakeDupFile = open(CacheFile, 'w')
#         for track in TrackList:
#             MakeDupFile.write(track+'\n')
#         MakeDupFile.close()
#         return TrackList


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

# tracklist = [i for i in SPResults]
# PLID = '48FlMoZaugE96JFEq3PPGJ'
# results = sp.user_playlist_add_tracks(
#     username, playlist_id=PLID, tracks=tracklist)
# ## create a new playlist
# playlists = sp.user_playlist_create(
#     user='adityasai', name='testplaylistapi', public=True)
# GetID = playlists.get('uri')


# search for a artist song combination
# artist = 'Nine Inch Nails'
# track = 'Hurt'
# track_id = sp.search(q='artist:' + artist + ' track:' +
#                      track, type='track', limit=10)
# tracks = track_id['tracks']['items']  # [0].get('uri')
# tracklist = [i.get('uri').split(':')[-1] for i in tracks]


# results = sp.user_playlist_add_tracks(
#     username, playlist_id=PLID, tracks=tracklist)
# Url="https://alt1053.radio.com/playlist"
# chrome_options = Options()
# chrome_options.add_argument("--headless")
# driver = webdriver.Chrome(options=chrome_options)
# driver.get(Url)
# soup = bs4.BeautifulSoup(driver.page_source, 'lxml')
# tracks=soup.find_all("div", {"class": "ts-track-item"})
