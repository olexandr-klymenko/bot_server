const ADMIN_URL = '/admin';

function spectator() {
    $(location).attr("href", "/play");
}

function check_user_name() {
    let name = document.getElementById("user").value;
    sendAdminCommand(
        getCommandBody("check_user_name", name),
        (data) => {
            if (data === 'False') {
                $(location).attr("href", "/play?user=" + name);
            } else {
                alert(data);
                alert("User name " + name + " is already registered");
            }
        }
    );
}

function sendAdminCommand(body, callback) {
    fetch(ADMIN_URL, {
        method: "POST",
        mode: "cors",
        headers: {
            'Content-Type': 'application/json',
        },
        body: body
    }).then(
        response => {
            return response.text()
        }
    ).then(response => {
        if (callback !== undefined) {
            callback(response)
        }
    }).catch(error => {
        if (error) {
            console.error(error)
        }
    })
}

function getCommandBody(command, args) {
    return JSON.stringify({
        "command": command,
        "args": args
    })
}