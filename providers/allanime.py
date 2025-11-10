import os
import json
import time
import requests
from requests_html import HTMLSession

from . import provider_base as base

os.environ['PYPPETEER_EXECUTABLE_PATH'] = "C:\\chrome-win\\chrome.exe"  # Adjust this path

class VideoLink:
    def __init__(self, link="", hls=False, mp4=False, resolutionStr="", src="", rawUrls=None):
        self.link = link
        self.hls = hls
        self.mp4 = mp4
        self.resolutionStr = resolutionStr
        self.src = src
        self.rawUrls = rawUrls if rawUrls is not None else {}

class AllAnime(base.AnimeProvider):
    def __init__(self):
        self.agent = "Mozilla/5.0 (Windows NT 6.1; Win64; rv:109.0) Gecko/20100101 Firefox/109.0"
        self.allanime_api = "https://api.allanime.day"
        self.allanime_base = "https://allmanga.to"
        self.lang = "en"
        self.mode = "sub"
        self.internalLinks = [
            "Luf-mp4",
            "Sak",
            "Default",
            "S-mp4",
        ]
        self.session = requests.Session()
        self.endpoint = self.session.get(self.allanime_base + "/getVersion").json()['episodeIframeHead']
        print(self.endpoint)
        # exit()
        
        self.cache_filename = "soramai.cache.json"
        self.cache = self.load_cache()
        
        # queries
        self.popular_query = """
            query(
                $type: VaildPopularTypeEnumType!
                $size: Int!
                $page: Int
                $dateRange: Int
            ) {
                queryPopular(
                    type: $type
                    size: $size
                    dateRange: $dateRange
                    page: $page
                ) {
                    total
                    recommendations {
                        anyCard {
                            _id
                            name
                            thumbnail
                            englishName
                            slugTime
                        }
                    }
                }
            }
        """
        self.searchQuery = """
            query(
                $search: SearchInput
                $limit: Int
                $page: Int
                $translationType: VaildTranslationTypeEnumType
                $countryOrigin: VaildCountryOriginEnumType
            ) {
                shows(
                    search: $search
                    limit: $limit
                    page: $page
                    translationType: $translationType
                    countryOrigin: $countryOrigin
                ) {
                    pageInfo {
                        total
                    }
                    edges {
                        _id
                        name
                        thumbnail
                        englishName
                        episodeCount
                        score
                        genres
                        slugTime
                        __typename
                    }
                }
            }
        """
        self.details_query = """
            query ($_id: String!) {
                show(
                    _id: $_id
                ) {
                    thumbnail
                    description
                    type
                    season
                    score
                    genres
                    status
                    studios
                }
            }
        """
        self.episodes_query = """
            query ($_id: String!) {
                show(
                    _id: $_id
                ) {
                    _id
                    availableEpisodesDetail
                }
            }
        """
        self.streams_query = """
            query(
                $showId: String!,
                $translationType: VaildTranslationTypeEnumType!,
                $episodeString: String!
            ) {
                episode(
                    showId: $showId
                    translationType: $translationType
                    episodeString: $episodeString
                ) {
                    sourceUrls
                }
            }
        """
        
    
    def load_cache(self):
        if os.path.exists(self.cache_filename):
            with open(self.cache_filename, "r") as file:
                return json.load(file)
        return {}

    def save_cache(self):
        with open(self.cache_filename, "w") as file:
            json.dump(self.cache, file, indent=4)

    def get_from_cache(self, key):
        return self.cache.get(key)

    def add_to_cache(self, key, value):
        self.cache[key] = value
        self.save_cache()
    
    def decrypt(self, provider_id) -> str:
        decrypted = ''
        for hex_value in [provider_id[i:i+2] for i in range(0, len(provider_id), 2)]:
            dec = int(hex_value, 16)
            xor = dec ^ 56
            oct_value = oct(xor)[2:].zfill(3)
            decrypted += chr(int(oct_value, 8))
        return decrypted
    
    def isInternal(self, link:str) -> bool:
        return link in self.internalLinks
    
    def get_popular(self, page:int):
        cache_key = f"popular_{page}"
        cached_data = self.get_from_cache(cache_key)
        if cached_data:
            if time.time() - cached_data["timestamp"] <= 60 * 60 * 24:
                return cached_data
        resp = requests.get(
            f"{self.allanime_api}/api",
            params={
                "variables": json.dumps({
                    "type": "anime",
                    "size": 26,
                    "dateRange": 7,
                    "page": page
                }),
                "query": self.popular_query
            },
            headers={
                "Referer": self.allanime_base,
                "User-Agent": self.agent
            }
        )
        
        data = resp.json()["data"]["queryPopular"]["recommendations"]
        data["timestamp"] = time.time()
        self.add_to_cache(cache_key, data)
        return data

    def get_latest_update(self, page: int):
        resp = requests.get(
            f"{self.allanime_api}/api",
            params={
                "variables": json.dumps({
                    "search": {
                        "allowAdult": False,
                        "allowUnknown": False,
                    },
                    "limit": 26,
                    "page": page,
                    "translationType": self.mode,
                    "countryOrigin": "ALL"
                }),
                "query": self.searchQuery
            },
            headers={
                "Referer": self.allanime_base,
                "User-Agent": self.agent
            }
        )
        
        return resp.json()["data"]["shows"]["edges"]
    
    def get_search(self, page: int, query: str):
        cache_key = f"search_{query}"
        cached_data = self.get_from_cache(cache_key)
        if cached_data:
            tmplist = []
            for edge in cached_data:
                tmplist.append(Anime(edge["_id"], edge["name"], edge["thumbnail"], int(edge["episodeCount"] or "0"), anime_type=edge["__typename"], anime_score=edge["score"],))

            return tmplist
        resp = requests.get(
            f"{self.allanime_api}/api",
            params={
                "variables": json.dumps({
                    "search": {
                        "query": query,
                        "allowAdult": False,
                        "allowUnknown": False,
                    },
                    "limit": 50,
                    "page": page,
                    "translationType": self.mode,
                    "countryOrigin": "ALL"
                }),
                "query": self.searchQuery
            },
            headers={
                "Referer": self.allanime_base,
                "User-Agent": self.agent
            }
        )
        
        data = resp.json()["data"]["shows"]["edges"]
        self.add_to_cache(f"search_{query}", data)
        anime_list = []
        # print(f"data len: {len(data)}")
        for edge in data:
            anime_list.append(Anime(edge["_id"], edge["name"], edge["thumbnail"], int(edge["episodeCount"] or "0"), anime_type=edge["__typename"], anime_score=edge["score"],))
            
        # print(f"anime list len: {len(anime_list)}")
        return anime_list
    
    def get_anime_details(self, anime_id: str):
        cache_key = f"anime_details_{anime_id}"
        cached_data = self.get_from_cache(cache_key)
        if cached_data:
            return cached_data
        
        resp = requests.get(
            f"{self.allanime_api}/api",
            params={
                "variables": json.dumps({
                    "_id": anime_id
                }),
                "query": self.details_query
            },
            headers={
                "Referer": self.allanime_base,
                "User-Agent": self.agent
            }
        )
        
        data = resp.json()["data"]["show"]
        self.add_to_cache(f"anime_details_{anime_id}", data)
        return data
    
    def get_episodes_list(self, anime_id: str):
        cache_key = f"episodes_list_{anime_id}"
        cached_data = self.get_from_cache(cache_key)
        if cached_data:
            return cached_data
        resp = requests.get(
            f"{self.allanime_api}/api",
            params={
                "variables": json.dumps({
                    "_id": anime_id
                }),
                "query": self.episodes_query
            },
            headers={
                "Referer": self.allanime_base,
                "User-Agent": self.agent
            }
        )
        data = resp.json()["data"]["show"]["availableEpisodesDetail"][self.mode]
        self.add_to_cache(f"episodes_list_{anime_id}", data)
        return data
    
    def get_episode_streams(self, anime_id: str, episode_num: int) -> list:
        cache_key = f"episode_streams{anime_id}_{episode_num}"
        cached_data = self.get_from_cache(cache_key)
        if cached_data:
            return cached_data
        resp = requests.get(
            f"{self.allanime_api}/api",
            params={
                "variables": json.dumps({
                    "showId": anime_id,
                    "translationType": self.mode,
                    "episodeString": f"{episode_num}"
                }),
                "query": self.streams_query
            },
            headers={
                "Referer": self.allanime_base,
                "User-Agent": self.agent
            }
        )
        
        data = resp.json()["data"]["episode"]["sourceUrls"]
        self.add_to_cache(f"episode_streams{anime_id}_{episode_num}", data)
        return data
    
    def get_video_from_url(self, url: str, name: str) -> dict:
        decryptedUrl = self.decrypt(url.replace("--", ""))
        resp = requests.get(self.endpoint + decryptedUrl.replace("/clock?", "/clock.json?"))
        if resp.status_code != 200:
            return None
        links = resp.json()["links"]
        return links
    
    def get_video_list(self, anime_id: str, episode_num: int):
        cache_key = f"video_list_{anime_id}_{episode_num}"
        cached_data = self.get_from_cache(cache_key)
        if cached_data:
            tmp_links = []
            for video in cached_data:
                try:
                    print(f'video: {video}')
                    video = video[0]
                    link = video["link"]
                    hls = self.select(video, "hls", "mp4", reverse=True)
                    mp4 = self.select(video, "mp4", "hls", reverse=True)
                    resolution = video["resolutionStr"]
                    src = self.select(video, "src", "", opt2notInDict=True)
                    rawUrls = self.select(video, "rawUrls", {}, opt2notInDict=True)
                    tmp_links.append(VideoLink(link=link, hls=hls, mp4=mp4, resolutionStr=resolution, src=src, rawUrls=rawUrls))
                except TypeError:
                    continue
            return tmp_links
        
        
        episode_streams = self.get_episode_streams(anime_id, episode_num)
        video_list = []
        for stream in episode_streams:
            if self.isInternal(stream["sourceName"]):
                links = self.get_video_from_url(stream["sourceUrl"], stream["sourceName"])
                video_list.append(links)
        
        # print(video_list)
                
        self.add_to_cache(f"video_list_{anime_id}_{episode_num}", video_list)
                
        video_links = []
        for video in video_list:
            try:
                video = video[0]
                link = video["link"]
                hls = self.select(video, "hls", "mp4", reverse=True)
                mp4 = self.select(video, "mp4", "hls", reverse=True)
                resolution = video["resolutionStr"]
                src = self.select(video, "src", "", opt2notInDict=True)
                rawUrls = self.select(video, "rawUrls", {}, opt2notInDict=True)
                video_links.append(VideoLink(link=link, hls=hls, mp4=mp4, resolutionStr=resolution, src=src, rawUrls=rawUrls))
            except TypeError:
                continue
        return video_links
    
    def select(self, dictobj, opt1, opt2, reverse=False, opt2notInDict=False):
        try:
            val = dictobj[opt1]
            return val
        except KeyError:
            if opt2notInDict:
                return opt2
            if reverse:
                return not dictobj[opt2]
            return dictobj[opt2]

class Anime:
    def __init__(self, anime_id: str, anime_title: str, thumbnail: str,episodes_count: int = 0, description="", anime_type="", anime_status="", anime_score=0.0, anime_genres=[]):
        self.id = anime_id
        self.title = anime_title
        self.episodes_count = episodes_count
        self.episodes = []  # List to store fetched episodes        
    
    def get_episode(self, episode_num: int):
        # Fetch and append episode to self.episodes
        episode_streams = AllAnime().get_video_list(self.id, episode_num)
        episode_title = f"Episode {episode_num}"
        episode = Episode(self.id, episode_num, episode_title, episode_streams)
        self.episodes.append(episode)
        return episode

class Episode:
    def __init__(self, animeId: str, episode_num: int, episode_title: str, videoStreams: list[VideoLink]):
        self.num = episode_num
        self.title = episode_title
        self.streams = videoStreams
    

def test():
    a = AllAnime()
    anime = a.get_search(1, "KnY")[0]
    anime.get_episode(1)  # Fetch and append episode 1
    print(anime.episodes[0].title)  # Print title of the first episode