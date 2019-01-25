function spectator() {
    $(location).attr("href", "/play");
}

function check_user_name() {
    let name = $("#user").val();
    $.post("/admin", {"command": "check_user_name",
                      "args":  name}, function (data) {
        if (data === 'False') {
            $(location).attr("href", "/play?user=" + name);
        } else {
            alert(data);
            alert("User name " + name + " is already registered");
            $("#user").val("");
        }
    });
}

// TODO: Move html elements creation to js
// TODO: Add admin button link