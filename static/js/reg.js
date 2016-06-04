function spectator() {
    $(location).attr("href", "/play");
}

function check_user_name() {
    var name = $("#user").val();
    $.get("/rest/check_user_name?" + name, function (data) {
        if (data == 'False') {
            $(location).attr("href", "/play?user=" + name);
        } else {
            alert("User name " + name + " is already registered");
            $("#user").val("");
        }
    });
}
