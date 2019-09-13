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
const ROOT_NODE_ID = 'rootNode';
const IMAGES_ROOT = "static/images/";

let reconnectionRetryCount;


function main() {
    let controlGroups = new ControlGroups();
    let rootNode = new AdminPanel(controlGroups.groups);
    rootNode.init();
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
        if (callback !== undefined) {
            callback()
        }
    }).catch(error => {
        if (error) {
            console.error(error)
        }
    })
}

class ControlGroupArgs {
    constructor(name, label, command, minValue, maxValue, stepValue) {
        this.name = name;
        this.label = label;
        this.command = command;
        this.minValue = minValue;
        this.maxValue = maxValue;
        this.stepValue = stepValue || minValue;
    }
}

class ControlGroups {
    constructor() {
        this.groups = [];
        this.init();
    }

    init() {
        let durationGroupArgs = new ControlGroupArgs(
            TIMESPAN,
            "Update duration, sec",
            "set_session_timespan",
            10,
            1800,
            10,
        );
        let durationGroup = new ControlGroup(durationGroupArgs);
        this.groups.push(durationGroup);

        let boardRegenerationGroupArgs = new ControlGroupArgs(
            SIZE,
            "Regenerate Game Board",
            "regenerate_game_board",
            1,
            6,
            1
        );
        let boardRegenerationGroup = new ControlGroup(boardRegenerationGroupArgs);
        this.groups.push(boardRegenerationGroup);

        let GuardsControlGroupArgs = new ControlGroupArgs(
            GUARDS,
            "Update guards number",
            "update_guards_number",
            0,
            10,
            1
        );
        let GuardsControlGroup = new ControlGroup(GuardsControlGroupArgs);
        this.groups.push(GuardsControlGroup);

        let GoldControlGroupArgs = new ControlGroupArgs(
            GOLD,
            "Update gold number",
            "update_gold_number",
            0,
            1000,
            1
        );
        let GoldControlGroup = new ControlGroup(GoldControlGroupArgs);
        this.groups.push(GoldControlGroup);

        let TickControlGroupArgs = new ControlGroupArgs(
            TICK,
            "Update tick time, sec",
            "set_tick_time",
            0.1,
            2,
            0.1
        );
        let TickControlGroup = new ControlGroup(TickControlGroupArgs);
        this.groups.push(TickControlGroup);
    }
}

class AdminPanel {
    constructor(controlGroups) {
        this.controlGroups = controlGroups;
        this.node = document.createElement("div");
        this.node.id = ROOT_NODE_ID;
        document.body.appendChild(this.node);
        this.groupsInfo = {};
        this.mainGroup = new MainGroup();
        this.initAdminSocket = this.initAdminSocket.bind(this);
        this.addControlGroups = this.addControlGroups.bind(this);
        this.appendControlGroup = this.appendControlGroup.bind(this);
    }

    init() {
        this.node.appendChild(this.mainGroup.node);
        this.addControlGroups();
        this.initAdminSocket()
    }

    addControlGroups() {
        this.controlGroups.map(group => this.appendControlGroup(group));
    }

    update(sessionInfo) {
        this.mainGroup.update(sessionInfo[IS_RUNNING], sessionInfo[IS_PAUSED], sessionInfo[TIMER]);
        for (let key in this.groupsInfo) {
            this.groupsInfo[key].updateValue(sessionInfo[key])
        }
    }

    appendControlGroup(group) {
        this.node.appendChild(group.node);
        this.groupsInfo[group.name] = group;
    }

    initAdminSocket() {
        let adminSocket = new WebSocket(ADMIN_SOCKET_URL);
        adminSocket.onmessage = (event) => {
            let sessionInfo = JSON.parse(event.data);
            this.update(sessionInfo);
        };
        adminSocket.onclose = () => {
            console.log('Connection with game server has been dropped');
            $('#' + this.node.id + ' *').attr('disabled', true);
            reconnectionRetryCount--;
            if (reconnectionRetryCount > 0) {
                setTimeout(this.initAdminSocket, RECONNECTION_RETRY_TIMEOUT)
            } else {
                console.log("Couldn't establish connection. Giving up");
            }
        };
        adminSocket.onopen = () => {
            reconnectionRetryCount = DEFAULT_RECONNECTION_RETRY_COUNT;
            console.log('Connection with game server has been established');
            $('#' + this.node.id + ' *').attr('disabled', false);
        };
        return adminSocket;
    }
}

class MainGroup {
    constructor() {
        this.startStopToggleInfo = new ToggleInfo(
            "Start Game",
            "start",
            "Stop Game",
            "stop",
        );
        this.startStopButton = document.createElement('button');
        this.startStopButton.onclick = this.toggle(this.startStopButton, this.startStopToggleInfo);

        this.pauseResumeToggleInfo = new ToggleInfo(
            "Resume Game",
            "pause_resume",
            "Pause Game",
            "pause_resume",
        );
        this.pauseResumeButton = document.createElement('button');
        this.pauseResumeButton.onclick = this.toggle(
            this.pauseResumeButton,
            this.pauseResumeToggleInfo
        );
        this.displayTimerButton = document.createElement('button');
    }

    update(isRunning, isPaused, timerValue) {
        if (isRunning) {
            this.startStopButton.innerText = this.startStopToggleInfo.offText
        } else {
            this.startStopButton.innerText = this.startStopToggleInfo.onText;
        }

        this.pauseResumeButton.disabled = !isRunning;
        this.displayTimerButton.disabled = !isRunning;

        if (isPaused) {
            this.pauseResumeButton.innerText = this.pauseResumeToggleInfo.onText
        } else {
            this.pauseResumeButton.innerText = this.pauseResumeToggleInfo.offText
        }
        this.displayTimerButton.innerText = timerValue;
    }

    get node() {
        let group = document.createElement('div');
        group.appendChild(this.startStopButton);
        group.appendChild(this.pauseResumeButton);
        group.appendChild(this.displayTimerButton);
        return group
    }

    toggle(element, toggleInfo) {
        return () => {
            let command, text;
            if (element.innerText === toggleInfo.onText) {
                command = toggleInfo.onCommand;
                text = toggleInfo.offText;
            } else {
                command = toggleInfo.offCommand;
                text = toggleInfo.onText;
            }
            sendAdminCommand(
                getCommandBody(command),
                () => {
                    element.innerText = text
                }
            )
        }
    }
}

class ToggleInfo {
    constructor(onText, onCommand, offText, offCommand) {
        this.onText = onText;
        this.onCommand = onCommand;
        this.offText = offText;
        this.offCommand = offCommand;
    }
}


class ControlGroup {
    constructor(groupArgs) {
        this.name = groupArgs.name;
        this.label = groupArgs.label;
        this.command = groupArgs.command;
        this.value = 0;
        this.minValue = groupArgs.minValue;
        this.maxValue = groupArgs.maxValue;
        this.stepValue = groupArgs.stepValue || groupArgs.minValue;
        this.valueButton = null;

        this.updateValue = this.updateValue.bind(this);
    }

    get node() {
        let group = document.createElement('div');
        let updateButton = document.createElement('button');
        updateButton.innerText = this.label;
        let valueButton = document.createElement('button');
        valueButton.innerText = this.value;
        this.valueButton = valueButton;

        updateButton.onclick = () => {
            sendAdminCommand(
                getCommandBody(
                    this.command,
                    parseInt(valueButton.innerText),
                )
            )
        };
        let decreaseButton = document.createElement('button');
        decreaseButton.innerText = '-';
        decreaseButton.onclick = () => {
            if (valueButton.innerText !== this.minValue.toString()) {
                valueButton.innerText = (
                    parseInt(valueButton.innerText) - this.stepValue
                ).toString();
            }
        };

        let increaseButton = document.createElement('button');
        increaseButton.innerText = '+';
        increaseButton.onclick = () => {
            if (valueButton.innerText !== this.maxValue.toString()) {
                valueButton.innerText = (
                    parseInt(valueButton.innerText) - this.stepValue
                ).toString();
            }
        };
        group.appendChild(updateButton);
        group.appendChild(valueButton);
        group.appendChild(decreaseButton);
        group.appendChild(increaseButton);

        return group
    }

    updateValue(value) {
        this.valueButton.innerText = value
    }
}

function getButtonWithImage(text, imageName) {
    return text + ' <img src=' + IMAGES_ROOT + imageName + '/>'
}

main();

// TODO: add images to buttons
// TODO: merge admin and spectator page
// TODO: Implement ReactJS