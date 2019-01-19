const game_port = '9000';
const hostname = window.location.hostname;
const url = "ws://" + hostname + ":" + game_port;
const admin_socket_url = url + "?client_type=Admin";
const BOARD = 'board';
const SCORE = 'score';
const PLAYERS = 'players';


function main() {
    get_admin_socket();
}

function get_admin_socket() {
    let admin_socket = new WebSocket(admin_socket_url);
    admin_socket.onmessage = (event) => {
        let sessionInfo = JSON.parse(event.data);
        show_players(sessionInfo[PLAYERS]);
    };
}

function show_players(players) {
    console.log(players);

    let players_list = document.createElement("ul");
    players_list.setAttribute('id', 'Players');
    Object.keys(players).forEach(function(key) {
        let player = document.createElement('li');
        player.setAttribute('class',key);
        players_list.appendChild(player)
        player.innerHTML = player.innerHTML + key;
    });
    document.getElementById('AdminContent').appendChild(players_list);
}

main();