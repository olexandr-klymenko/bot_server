function spectator() {
    $(location).attr("href", "/play");
}

function check_user_name() {
    $.get("https://8080-dot-6949214-dot-devshell.appspot.com/labeling-sets/", function (data) {
        console.log(data)
    });
    // $.get("http://127.0.0.1:8000/labeling-sets", function (data) {
    //     console.log(data)
    // });
    // let name = $("#user").val();
    // $.post("/admin", {"command": "check_user_name",
    //                   "args":  name}, function (data) {
    //     if (data === 'False') {
    //         $(location).attr("href", "/play?user=" + name);
    //     } else {
    //         alert(data);
    //         alert("User name " + name + " is already registered");
    //         $("#user").val("");
    //     }
    // });
}

// TODO: Move html elements creation to js
// TODO: Add admin button link