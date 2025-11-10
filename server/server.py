from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Mock function to simulate anime search
def search_anime(query):
    # Replace this with actual logic to search anime from your database or API
    results = [
        {"title": "Naruto", "url": "/watch/naruto"},
        {"title": "Attack on Titan", "url": "/watch/aot"},
        {"title": "One Piece", "url": "/watch/one-piece"},
    ]
    return [anime for anime in results if query.lower() in anime['title'].lower()]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('q', '')
    results = search_anime(query)
    return jsonify(results)

@app.route('/watch/<anime>')
def watch(anime):
    # Replace this with the actual video serving logic
    return f"Now watching: {anime.replace('-', ' ').title()}"

if __name__ == '__main__':
    app.run(debug=True)
