const API_BASE = "https://api.andrew-zhu.com";
const DATA_BASE = "https://andrew-zhu.com/dnd";


var games;

const urlParams = new URLSearchParams(window.location.search);
const error = urlParams.get('error');
if (error) {
    document.getElementById("error").style.visibility = "visible";
}

after_load_data = function (data) {
    console.log("Loading data");
    games = data;

    let gameSelect = document.getElementById("game");
    gameSelect.options.length = 0;
    for (let i = 0; i < games.length; i++) {
        gameSelect.options[gameSelect.options.length] = new Option(games[i].name, games[i].id);
    }
};


$(function () {
    console.log("Getting data");
    $.getJSON(`${API_BASE}/game_options`, after_load_data);
});
