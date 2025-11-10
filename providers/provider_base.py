class AnimeProvider:
    def __init__(self, name, baseUrl):
        self.name = name
        self.baseUrl = baseUrl
        self.agent = "Mozilla/5.0 (Windows NT 6.1; Win64; rv:109.0) Gecko/20100101 Firefox/109.0"
        self.mode = "sub"
    
    def search(query:str):
        raise NotImplementedError
    
    def get_episodes(id:str):
        raise NotImplementedError
    
    def play(id:str, ep:int):
        raise NotImplementedError