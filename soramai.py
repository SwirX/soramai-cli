import os
import subprocess
import sys
from providers.provider_base import AnimeProvider
from providers.allanime import AllAnime
from flask import Flask, render_template, request, jsonify, redirect

class Soramai:
    def __init__(self, provider: AnimeProvider = AllAnime) -> None:
        self.mode = "sub"
        self.provider = provider()
        self.results = []

        if "ui" in sys.argv:
            print("Launching web UI...")
            self.start_web_ui()
        elif "debug" in sys.argv:
            print("Debug mode!")
            self.debug()
        else:
            self.cli()
    
    def cli(self):
        query = ""
        download = False
        skip = False
        ep = None

        for i in range(len(sys.argv)):
            arg = sys.argv[i]
            if arg in ["-d", "--download", "--dl"]:
                download = True
            elif arg in ["-s", "--skip"]:
                skip = True
            elif arg in ["-e", "-ep", "--episode"]:
                ep = sys.argv[i+1]
            elif arg in ["-u", "--update"]:
                self.update()
            elif arg == "--dub":
                self.mode = "dub"
            else:
                if i != 0 and "-" not in arg[i-1]:
                    query += arg + " "

        os.system("clear")
        query = query.strip()
        print(query)

        if query == "":
            query = input("\33[2K\r\033[1;36mSearch anime: \033[0m")
        
        anime_list = self.provider.get_search(1, query)
        if len(anime_list) == 0:
            self.die("No results found!")
        
        os.system("clear")
        print("Select anime:")
        for i in range(1, len(anime_list) + 1):
            print(f"{i}. {anime_list[i-1].title}")
        
        result = input()
        if not result:
            exit(1)
        result = int(result) - 1
        anime = anime_list[result]
        title = anime.title
        ep_list = anime.episodes_count
        os.system("clear")
        print("Select episode:")
        for ep in range(ep_list):
            print(ep + 1)
        
        result = input("\n-> ")
        if not result:
            exit(1)
        episode = anime.get_episode(int(result))
        stream = episode.streams[0].link
        cmd = f"mpv {stream}"
        subprocess.call(cmd)

    def debug(self):
        self.provider.get_search(1, "death note")
        print("")

    def start_web_ui(self):
        app = Flask(__name__, template_folder='server/templates', static_folder='server/static')
        anime_results = []
        anime = None

        @app.route('/')
        def index():
            return render_template('index.html')

        @app.route('/search', methods=['GET'])
        def search():
            query = request.args.get('q', '')
            self.results = self.provider.get_search(1, query)
            results = [{'title': anime.title, 'url': f'/details/{anime.id}'} for anime in self.results]
            return jsonify(results)

        @app.route('/details/<anime_id>')
        def details(anime_id):
            print(self.results)
            
            for anime_iter in self.results:
                if anime_iter.id == anime_id:
                    eps = anime_iter.episodes_count
                    
                    ep_list = [{'ep_number': ep+1, 'url': f"/watch/{anime_id}/{ep+1}"} for ep in range(eps)]
                    
                    return render_template('details.html', anime_title=anime_iter.title, episodes=ep_list)
            return

        @app.route('/watch/<anime_id>/<episode_num>')
        def watch(anime_id, episode_num):
            for anime_iter in self.results:
                if anime_iter.id == anime_id:
                    episode = anime_iter.get_episode(int(episode_num))
                    stream = episode.streams[0].link
                    return render_template('watch.html', hls=stream, anime_title=f"{anime_iter.title} - ep {episode_num}")
            return "Episode not found", 404

        app.run(debug=True)

    def die(self, message):
        print(message)
        exit(1)

# Run the application
Soramai()
