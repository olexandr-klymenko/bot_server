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
    let rootNode = document.getElementById('adminContent');
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

function showStartStopButton(isStarted) {
    let rootNode = document.getElementById('adminContent');
    let button = document.getElementById('startStopButton');
    if (! button) {
        button = document.createElement('BUTTON');
        button.id = 'startStopButton'
    }
    if (isStarted) {
        button.innerText = 'Stop Game';
        button.removeEventListener("click", handleStart);
        button.addEventListener("click", handleStop)
    } else {
        button.innerText = 'Start Game';
        button.removeEventListener("click", handleStop);
        button.addEventListener("click", handleStart)
    }

    rootNode.appendChild(button);

    function handleStart() {
        $.get("/rest/start", () => {
            console.log('Game has been started');
            button.removeEventListener("click", handleStart);
            button.addEventListener("click", handleStop);
            button.innerText = "Stop Game"
        })
    }

    function handleStop() {
        // adminSocket.send('stop');
        // console.log('Game has been stopped');
        // button.removeEventListener("click", handleStop);
        // button.addEventListener("click", handleStart);
        // button.innerText = "Start Game"
        $.get("/rest/stop", () => {
            console.log('Game has been stopped');
            button.removeEventListener("click", handleStop);
            button.addEventListener("click", handleStart);
            button.innerText = "Start Game"
        })
    }
}


main();