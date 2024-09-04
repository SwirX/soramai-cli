function searchAnime() {
    const query = document.getElementById('search-bar').value;
    fetch(`/search?q=${query}`)
        .then(response => response.json())
        .then(data => {
            const resultsList = document.getElementById('results-list');
            resultsList.innerHTML = '';
            data.forEach(anime => {
                const li = document.createElement('li');
                const a = document.createElement('a');
                a.href = anime.url;
                a.textContent = anime.title;
                li.appendChild(a);
                resultsList.appendChild(li);
            });
        });
}
