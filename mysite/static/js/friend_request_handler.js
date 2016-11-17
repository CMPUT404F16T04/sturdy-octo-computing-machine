// Handles ajax calls when follow and friend buttons are selected on a user's profile or manage friends/following page

$('.friend-anchor').click(function () {
    var id = $(this).attr('id');
    var status = $(this).data("status");
    var csrftoken = getCookie('csrftoken'); // From js/cookie.js
    var friendUUID = $(this).data("uuid");
    var is_local = $(this).data("islocal");

    // HANDLE UNFRIEND ACTION
    if (status == "unfriend") {
        console.log("Author wants to unfriend: "+$(this).data("username"));
        // Unfriend with ajax so we don't have to reload the page.
        var jsonData = {
            "action": "unfriend",
            "author": {
                "id": authorUUID
            },
            "friend": {
                "id": friendUUID,
                "is_local": is_local
            }
        };
        var jsonStr = JSON.stringify(jsonData)
        console.log(jsonStr);
        $.ajax({
            type: "POST",
            url: url,
            data: jsonStr,
            contentType: "application/json",
            success: function() { unfriendSuccess(id); },
            beforeSend: function(xhr) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        });
    }
    // HANDLE FOLLOW ACTION
    else if (status == "follow") {
        console.log("This author wants to follow: "+$(this).data('username'));
        // Follow with ajax so we don't have to reload the page.
        var jsonData = {
            "action": "follow",
            "author": {
                "id": authorUUID
            },
            "friend": {
                "id": friendUUID,
                "is_local": is_local
            }
        };
        var jsonStr = JSON.stringify(jsonData)
        console.log(jsonStr);
        $.ajax({
            type: "POST",
            url: url,
            data: jsonStr,
            contentType: "application/json",
            success: function () { followSuccess(id); },
            beforeSend: function(xhr) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        });
    }
    // HANDLE UNFOLLOW ACTION
    else if (status == "unfollow") {
        console.log("This author wants to unfollow: "+$(this).data('username'));
        // Unfollow with ajax so we don't have to reload the page.
        var jsonData = {
            "action": "unfollow",
            "author": {
                "id": authorUUID
            },
            "friend": {
                "id": friendUUID,
                "is_local": is_local
            }
        };
        var jsonStr = JSON.stringify(jsonData)
        console.log(jsonStr);
        $.ajax({
            type: "POST",
            url: url,
            data: jsonStr,
            contentType: "application/json",
            success: function() { unfollowSuccess(id); },
            beforeSend: function(xhr) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        });
    }
    // HANDLE ACCEPT FRIEND request
    else if (status == "accept_friend_request") {
        console.log("This author wants to accept the friend request of: "+$(this).data('username'));
        // Accept friend request with ajax so we don't have to reload the page.
        var jsonData = {
            "action": "accept_friend_request",
            "author": {
                "id": authorUUID
            },
            "friend": {
                "id": friendUUID,
                "is_local": is_local
            }
        };
        var jsonStr = JSON.stringify(jsonData)
        console.log(jsonStr);
        $.ajax({
            type: "POST",
            url: url,
            data: jsonStr,
            contentType: "application/json",
            success: function() { acceptFriendRequestSuccess(id); },
            beforeSend: function(xhr) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        });
    }

});

function unfriendSuccess(id) {
    console.log("Unfriend successful!");
    $('#'+id).text("Accept Friend Request");
    $('#'+id).data("status" , "accept_friend_request");
}

function followSuccess(id) {
    console.log("Follow successful!");
    $('#'+id).text("Unfollow");
    $('#'+id).data("status" , "unfollow");
}

function unfollowSuccess(id) {
    console.log("Unfollow successful!");
    $('#'+id).text("Follow");
    $('#'+id).data("status" , "follow");
}

function acceptFriendRequestSuccess(id) {
    console.log("Accept friend request successful!");
    $('#'+id).text("Unfriend");
    $('#'+id).data("status" , "unfriend");
}
