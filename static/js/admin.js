const GAME_PORT = '9000';
const HOSTNAME = window.location.hostname;
const GAME_URL = "ws://" + HOSTNAME + ":" + GAME_PORT;
const ADMIN_SOCKET_URL = GAME_URL + "?client_type=Admin";
const ADMIN_URL = '/admin';
const IS_RUNNING = 'is_running';
const IS_PAUSED = 'is_paused';
const SIZE = 'size';
const GUARDS = 'guards';
const GOLD = 'gold';
const TICK = 'tick';
const TIMESPAN = 'timespan';
const TIMER = 'timer';
const DEFAULT_RECONNECTION_RETRY_COUNT = 10;
const RECONNECTION_RETRY_TIMEOUT = 1000;
const PLAYERS_LIST_ID = 'players';
const START_STOP_BUTTON_ID = 'startStopButton';
const PAUSE_RESUME_BUTTON_ID = 'pauseResumeButton';
const TIMER_BUTTON_ID = 'timerButton';
const REGENERATE_BOARD_BUTTON_ID = 'regenerateBoardButton';
const BOARD_SIZE_SELECT_ID = 'boardSizeSelect';
const ROOT_NODE_ID = 'rootNode';
const BOARD_BLOCKS_NUMBERS = [1, 2, 3, 4, 5];
const IMAGES_ROOT = "static/images/";

let adminSocket;
let reconnectionRetryCount;
let playersList;
let startStopButton;
let pauseResumeButton;
let timeSpanControlBlock;
let regenerateBoardBlock;
let guardsControlBlock;
let guardsNumberButton;
let updateGuardsNumberButton;
let goldControlBlock;
let goldNumberButton;
let updateGoldNumberButton;
let tickControlBlock;
let tickTimeButton;
let timeSpanButton;
let timerButton;
let updateTickTimeButton;
let rootNode;


function main() {
    rootNode = document.createElement("div");
    rootNode.id = ROOT_NODE_ID;
    document.body.appendChild(rootNode);

    playersList = document.createElement("ul");
    playersList.id = PLAYERS_LIST_ID;

    startStopButton = document.createElement('button');
    startStopButton.id = START_STOP_BUTTON_ID;

    pauseResumeButton = document.createElement('button');
    pauseResumeButton.id = PAUSE_RESUME_BUTTON_ID;
    timerButton = document.createElement('button');
    timerButton.id = TIMER_BUTTON_ID;

    timeSpanControlBlock = getTimeSpanControlBlock();
    regenerateBoardBlock = getRegenerateBoardBlock();
    guardsControlBlock = getGuardsControlBlock();
    goldControlBlock = getGoldControlBlock();
    tickControlBlock = getTickControlBlock();

    rootNode.appendChild(startStopButton);
    rootNode.appendChild(pauseResumeButton);
    rootNode.appendChild(timerButton);
    rootNode.appendChild(timeSpanControlBlock);

    rootNode.appendChild(regenerateBoardBlock);
    rootNode.appendChild(guardsControlBlock);
    rootNode.appendChild(goldControlBlock);
    rootNode.appendChild(tickControlBlock);
    rootNode.appendChild(playersList);

    adminSocket = getAdminSocket();
}

function getAdminSocket() {
    let adminSocket = new WebSocket(ADMIN_SOCKET_URL);
    adminSocket.onmessage = (event) => {
        let sessionInfo = JSON.parse(event.data);
        // console.log(sessionInfo);
        showPlayers(sessionInfo[PLAYERS_LIST_ID]);
        showStartStopButton(sessionInfo[IS_RUNNING]);
        showPauseResumeButton(sessionInfo[IS_PAUSED]);
        document.getElementById(BOARD_SIZE_SELECT_ID).value = sessionInfo[SIZE];
        guardsNumberButton.innerText = sessionInfo[GUARDS];
        goldNumberButton.innerText = sessionInfo[GOLD];
        tickTimeButton.innerText = sessionInfo[TICK];
        timeSpanButton.innerText = sessionInfo[TIMESPAN];
        timerButton.innerText = sessionInfo[TIMER]
    };
    adminSocket.onclose = () => {
        console.log('Connection with game server has been dropped');
        $('#' + ROOT_NODE_ID + ' *').attr('disabled', true);
        reconnectionRetryCount--;
        if (reconnectionRetryCount > 0) {
            setTimeout(getAdminSocket, RECONNECTION_RETRY_TIMEOUT)
        } else {
            console.log("Couldn't establish connection. Giving up");
        }
    };
    adminSocket.onopen = () => {
        reconnectionRetryCount = DEFAULT_RECONNECTION_RETRY_COUNT;
        console.log('Connection with game server has been established');
        $('#' + ROOT_NODE_ID + ' *').attr('disabled', false);
    };
    return adminSocket;
}

function showPlayers(players) {
    let playersList = document.getElementById(PLAYERS_LIST_ID);
    playersList.innerHTML = '';
    playersList.innerText = "Players:";

    for (let idx in players) {
        let player = document.createElement('li');
        playersList.appendChild(player);
        player.innerHTML = player.innerHTML + players[idx];
    }
}

function showStartStopButton(isRunning) {
    startStopButton = document.getElementById(START_STOP_BUTTON_ID);
    if (isRunning) {
        startStopButton.innerText = 'Stop Game';
        startStopButton.removeEventListener("click", handleStart);
        startStopButton.addEventListener("click", handleStop);
    } else {
        startStopButton.innerText = 'Start Game';
        startStopButton.removeEventListener("click", handleStop);
        startStopButton.addEventListener("click", handleStart);
    }
}

function handleStart() {
    let startStopButton = document.getElementById(START_STOP_BUTTON_ID);
    sendAdminCommand(
        getCommandBody("start"),
        () => {
            console.log('Game has been started');
            startStopButton.removeEventListener("click", handleStart);
            startStopButton.addEventListener("click", handleStop);
            startStopButton.innerText = "Stop Game"
        }
    )
}

function handleStop() {
    let startStopButton = document.getElementById(START_STOP_BUTTON_ID);
    sendAdminCommand(
        getCommandBody("stop"),
        () => {
            console.log("Game has been stopped");
            startStopButton.removeEventListener("click", handleStop);
            startStopButton.addEventListener("click", handleStart);
            startStopButton.innerText = "Start Game"
        }
    )
}

function showPauseResumeButton(isPaused) {
    pauseResumeButton = document.getElementById(PAUSE_RESUME_BUTTON_ID);
    if (isPaused) {
        pauseResumeButton.innerText = 'Resume Game';
    } else {
        pauseResumeButton.innerText = 'Pause Game';
    }
    pauseResumeButton.onclick = () => {
        sendAdminCommand(
            getCommandBody("pause_resume"),
            console.log(pauseResumeButton.innerText)
        )
    }
}

function getRegenerateBoardBlock() {
    let blockDiv = document.createElement('div');
    let regenerateBoardButton = document.createElement('button');
    regenerateBoardButton.id = REGENERATE_BOARD_BUTTON_ID;
    regenerateBoardButton.innerText = 'Regenerate Game Board';
    regenerateBoardButton.onclick = () => {
        sendAdminCommand(
            getCommandBody(
                "regenerate_game_board",
                document.getElementById(BOARD_SIZE_SELECT_ID).value
            ),
            console.log("Game board has been regenerated")
        )
    };

    let boardSizeSelect = document.createElement('select');
    boardSizeSelect.id = BOARD_SIZE_SELECT_ID;
    for(let idx = 0; idx < BOARD_BLOCKS_NUMBERS.length; idx++) {
        let option = new Option(BOARD_BLOCKS_NUMBERS[idx], BOARD_BLOCKS_NUMBERS[idx]);
        boardSizeSelect.appendChild(option);
    }

    blockDiv.appendChild(regenerateBoardButton);
    blockDiv.appendChild(boardSizeSelect);
    return blockDiv
}

function getGuardsControlBlock() {
    let blockDiv = document.createElement('div');
    updateGuardsNumberButton = document.createElement('button');
    updateGuardsNumberButton.innerText = 'Update guards number';

    updateGuardsNumberButton.onclick = () => {
        sendAdminCommand(
            getCommandBody(
                "update_guards_number",
                guardsNumberButton.innerText,
                ),
            console.log("Guards number has been updated")
        )
    };
    let decreaseButton = document.createElement('button');
    decreaseButton.innerText = '-';
    decreaseButton.onclick = () => {
        if (guardsNumberButton.innerText !== '0') {
            guardsNumberButton.innerText = parseInt(guardsNumberButton.innerText) - 1;
        }
    };

    guardsNumberButton = document.createElement('button');
    guardsNumberButton.disabled = true;
    let increaseButton = document.createElement('button');
    increaseButton.innerText = '+';
    increaseButton.onclick = () => {
        guardsNumberButton.innerText = parseInt(guardsNumberButton.innerText) + 1;
    };

    blockDiv.appendChild(updateGuardsNumberButton);
    blockDiv.appendChild(decreaseButton);
    blockDiv.appendChild(guardsNumberButton);
    blockDiv.appendChild(increaseButton);
    return blockDiv
}

function getGoldControlBlock() {
    let goldControlBlock = document.createElement('div');
    updateGoldNumberButton = document.createElement('button');
    updateGoldNumberButton.innerText = 'Update gold cells number';
    updateGoldNumberButton.onclick = () => {
        sendAdminCommand(
            getCommandBody(
                "update_gold_cells",
                goldNumberButton.innerText,
            ),
            console.log("Gold cells have been re spawned")
        )
    };
    let decreaseGoldNumberButton = document.createElement('button');
    decreaseGoldNumberButton.innerText = '-';
    decreaseGoldNumberButton.onclick = () => {
        if (goldNumberButton.innerText !== '0') {
            goldNumberButton.innerText = parseInt(goldNumberButton.innerText) - 1;
        }
    };

    goldNumberButton = document.createElement('button');
    let increaseGoldNumberButton = document.createElement('button');
    increaseGoldNumberButton.innerText = '+';
    increaseGoldNumberButton.onclick = () => {
        goldNumberButton.innerText = parseInt(goldNumberButton.innerText) + 1;
    };

    goldControlBlock.appendChild(updateGoldNumberButton);
    goldControlBlock.appendChild(decreaseGoldNumberButton);
    goldControlBlock.appendChild(goldNumberButton);
    goldControlBlock.appendChild(increaseGoldNumberButton);
    return goldControlBlock
}

function getTickControlBlock() {
    let tickTimeControlBlock = document.createElement('div');
    updateTickTimeButton = document.createElement('button');
    updateTickTimeButton.innerText = 'Update tick time, sec';
    updateTickTimeButton.onclick = () => {
        sendAdminCommand(
            getCommandBody(
                "set_tick_time",
                parseFloat(tickTimeButton.innerText).toFixed(1)
            ),
            console.log("Tick time has been updated")
        )
    };
    let decreaseTickTimeButton = document.createElement('button');
    decreaseTickTimeButton.innerText = '-';
    decreaseTickTimeButton.onclick = () => {
        if (tickTimeButton.innerText !== '0.1') {
            tickTimeButton.innerText = (parseFloat(tickTimeButton.innerText) - 0.1).toFixed(1);
        }
    };

    tickTimeButton = document.createElement('button');
    let increaseTickTimeButton = document.createElement('button');
    increaseTickTimeButton.innerText = '+';
    increaseTickTimeButton.onclick = () => {
        tickTimeButton.innerText = (parseFloat(tickTimeButton.innerText) + 0.1).toFixed(1);
    };

    tickTimeControlBlock.appendChild(updateTickTimeButton);
    tickTimeControlBlock.appendChild(decreaseTickTimeButton);
    tickTimeControlBlock.appendChild(tickTimeButton);
    tickTimeControlBlock.appendChild(increaseTickTimeButton);
    return tickTimeControlBlock
}

function getTimeSpanControlBlock() {
    let rootDiv = document.createElement('div');
    let updateButton = document.createElement('button');
    updateButton.innerText = 'Update timespan, sec';
    updateButton.onclick = () => {
        sendAdminCommand(
            getCommandBody(
                "set_session_timespan",
                parseInt(timeSpanButton.innerText),
            ),
            console.log("Timespan has been updated")
        )
    };
    let decreaseButton = document.createElement('button');
    decreaseButton.innerText = '-';
    decreaseButton.onclick = () => {
        if (timeSpanButton.innerText !== '10') {
            timeSpanButton.innerText = parseInt(timeSpanButton.innerText) - 10;
        }
    };

    timeSpanButton = document.createElement('button');
    let increaseButton = document.createElement('button');
    increaseButton.innerText = '+';
    increaseButton.onclick = () => {
        timeSpanButton.innerText = parseInt(timeSpanButton.innerText) + 10;
    };

    rootDiv.appendChild(updateButton);
    rootDiv.appendChild(decreaseButton);
    rootDiv.appendChild(timeSpanButton);
    rootDiv.appendChild(increaseButton);
    return rootDiv
}

function getCommandBody(command, args) {
    return JSON.stringify({
            "command": command,
            "args": args
        })
}

function sendAdminCommand(body, callback) {
    fetch(ADMIN_URL, {
        method: "POST",
        mode: "cors",
        headers: {
            'Content-Type': 'application/json',
        },
        body: body
    }).then(() => {
        if(callback !== undefined) {
            callback()
        }
    }).catch(error => {
        if(error) {
            console.error(error)
        }
    })
}

function getButtonWithImage(text, imageName) {
    return text + ' <img src=' + IMAGES_ROOT + imageName + '/>'
}

main();

// TODO: add images to buttons
// TODO: merge admin and spectator page
// TODO: Implement classes
// TODO: Implement ReactJS