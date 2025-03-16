function getList() {
    $.ajax({
        url: "/socialnetwork/get-global",
        dataType : "json",
        success: updateList,
        error: updateError
    });
}

function getFollowerList() {
    $.ajax({
        url: "/socialnetwork/get-follower",
        dataType : "json",
        success: updateList,
        error: updateError
    });
}

function updateError(xhr) {
    if (xhr.status === 0) {
        displayError("Cannot connect to server")
        return
    }

    if (!xhr.getResponseHeader('content-type') === 'application/json') {
        displayError("Received status=" + xhr.status)
        return
    }

    let response = JSON.parse(xhr.responseText)
    if (response.hasOwnProperty('error')) {
        displayError(response.error)
        return
    }

    displayError(response)
}

function displayError(message) {
    $("#error").html(message);
}

function updateList(items) {
    // Removes the old todolist items
    // $("li").remove()
    /*
        
    */

    // Removes items from todolist if they not in items
    // $("li").each(function() {
    //     let existing_item_id = this.id
    //     let delete_it = true
    //     items.forEach(item => {
    //         if (existing_item_id === `id_item_${item.id}`) delete_it = false
    //     })
    //     if (delete_it) this.remove()
    // })

    // Adds each to do list item received from the server to the displayed list
    items['posts'].forEach(post => {
        if (document.getElementById(`id_post_div_${post.id}`) == null) {
            $("#post-content").prepend(makePostHTML(post))
        }
    })

    items['comments'].forEach(comment => {
        if (document.getElementById(`id_comment_div_${comment.id}`) == null) {
            $(`#comment_container_${comment.post}`).append(makeCommentHTML(comment))
        }
    })
}

// Builds a new HTML "li" element for the to do list
function makePostHTML(post) {
    console.log(post)
    let postHTML = $(`
        <div id = "post_container_${post.id}" class = "comment_container">
            <div class = "post" id="id_post_div_${post.id}"> 
                <a id="id_post_profile_${post.id}" class="user-link" href="/socialnetwork/other-profile-page/${post.user_id}">
                    Post by ${sanitize(post.user)} - 
                </a>
                <span id = "id_post_text_${post.id}">${sanitize(post.text)}</span>
                -
                <span class = "post-date-time" id = "id_post_date_time_${post.id}">
                    ${new Date(post.creation_time).toLocaleDateString()} ${new Date(post.creation_time).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                </span> 
            </div>

            <div id = "comment_container_${post.id}"></div>

            <div class = "make_new_comment">
                <div class = "comment-input-container">
                    <input id = "id_comment_input_text_${post.id}">
                    <button id = "id_comment_button_${post.id}" onclick="addComment(${post.id})"> Submit </button>
                </div>
            </div>
        </div>
    `)
    return postHTML
}

/*
    <div class = "post" id = "id_post_div_${comment.id}"> 
        <a id="id_post_profile_${comment.id}" class="user-link" href="{% url 'other-profile-page' comment.user.id %}">
            Comment by ${comment.user.first_name} ${comment.user.last_name} - 
        </a>
        <span id = "id_post_text_${comment.id}">${comment.text}</span>
        -
        <span class = "post-date-time" id = "id_post_date_time_${comment.id}">
            {{ post.creation_time|date:"n/j/Y g:i A" }}
        </span> 
    </div>
*/

function makeCommentHTML(comment) {
    console.log(comment,"making comment")
    let commentHTML = $(`
        <div class = "comment-post" id = "id_comment_div_${comment.id}"> 
            <a id="id_comment_profile_${comment.id}" class="user-link" href="/socialnetwork/other-profile-page/${comment.user_id}">
                Comment by ${comment.user} - 
            </a>
            <span id = "id_comment_text_${comment.id}">${comment.text}</span>
            -
            <span class = "post-date-time" id = "id_comment_date_time_${comment.id}">
                ${new Date(comment.creation_time).toLocaleDateString()} ${new Date(comment.creation_time).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
            </span> 
        </div>
    `)
    return commentHTML
}

function sanitize(s) {
    // Be sure to replace ampersand first
    return s.replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
}

function addPost() {
    let postTextElement = $("#id_post_input_text")
    let postTextValue   = postTextElement.val()
    console.log("adding post !!!!")
    // Clear input box and old error message (if any)
    postTextElement.val('')
    displayError('');

    $.ajax({
        url: "/socialnetwork/add-post",
        type: "POST",
        data: { post: postTextValue, csrfmiddlewaretoken: getCSRFToken() },
        dataType : "json",
        success: is_follower ? updateList : getList,
        error: updateError
    });
}

function addComment(post_id) {
    let commentTextElement = $(`#id_comment_input_text_${post_id}`)
    let commentTextValue   = commentTextElement.val()

    let page_name_element = $(`#id_page_name`)
    let page_name = page_name_element.html()
    console.log(page_name)
    console.log("adding comment !!!!")
    let is_follower = page_name.includes("Follower")
    // Clear input box and old error message (if any)
    commentTextElement.val('')
    displayError('');

    $.ajax({
        url: "/socialnetwork/add-comment",
        type: "POST",
        data: { post_id: post_id, comment_text: commentTextValue, is_follower_stream: is_follower, csrfmiddlewaretoken: getCSRFToken() },
        dataType : "json",
        success: is_follower ? updateList : getList,
        error: updateError
    });
}

// function deleteItem(id) {
//     $.ajax({
//         url: `/jquery_todolist/delete-item/${id}`,
//         type: "POST",
//         data: { csrfmiddlewaretoken: getCSRFToken() },
//         dataType : "json",
//         success: updateList,
//         error: updateError
//     });
// }

function getCSRFToken() {
    let cookies = document.cookie.split(";")
    for (let i = 0; i < cookies.length; i++) {
        let c = cookies[i].trim()
        if (c.startsWith("csrftoken=")) {
            return c.substring("csrftoken=".length, c.length)
        }
    }
    return "unknown";
}