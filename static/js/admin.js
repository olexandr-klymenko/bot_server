const game_port = '9000';
const hostname = window.location.hostname;
const url = "ws://" + hostname + ":" + game_port;
const admin_socket_url = url + "?client_type=Admin";
const PLAYERS = 'players';
const STARTED = 'started';


function main() {
    getAdminSocket();
}

function getAdminSocket() {
    let adminSocket = new WebSocket(admin_socket_url);
    adminSocket.onmessage = (event) => {
        let sessionInfo = JSON.parse(event.data);
        console.log(sessionInfo);
        showPlayers(sessionInfo[PLAYERS]);
        showStartStopButton(sessionInfo[STARTED]);
    };
}

function showPlayers(players) {
    let rootNode = document.getElementById('AdminContent');
    let playersList = document.getElementById(PLAYERS);
    if (playersList) {
        playersList.innerHTML = ""
    } else {
        playersList = document.createElement("ul");
    }
    playersList.innerText = "Players:";

    playersList.setAttribute('id', PLAYERS);
    for (let idx in players) {
        let player = document.createElement('li');
        playersList.appendChild(player);
        player.innerHTML = player.innerHTML + players[idx];
    }
    rootNode.appendChild(playersList);
}

function showStartStopButton(started) {
    let rootNode = document.getElementById('AdminContent');
    let button = document.getElementById("BUTTON");
    if (! button) {button = document.createElement("BUTTON")}
    if (started) {
        button.innerText = 'Start Game';
        button.onclick = () => {
            $.get("/rest/start");
            button.innerText = 'Stop Game';
        }
    } else {
        button.innerText = 'Stop Game';
         button.onclick = () => {
            $.get("/rest/stop");
            button.innerText = 'Start Game';
        }
    }

    rootNode.appendChild(button);
}

main();