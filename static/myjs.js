// like 부분 숫자 계산
function toggle_like(post_id, type) {
    console.log(post_id, type)
    let $a_like = $(`#${post_id} a[aria-label='${type}']`)
    let $i_like = $a_like.find("i")
    let like = {"heart":"fa-heart", "thumbs":"fa-thumbs-up", "thumbs_down":"fa-thumbs-down"}
    let no_like = {"heart":"fa-heart-o", "thumbs":"fa-thumbs-o-up", "thumbs_down":"fa-thumbs-o-down"}
    if ($i_like.hasClass(like[type])) {
        $.ajax({
            type: "POST",
            url: "/update_like",
            data: {
                post_id_give: post_id,
                type_give: type,
                action_give: "unlike"
            },
            success: function (response) {
                console.log("unlike")
                $i_like.addClass(no_like[type]).removeClass(like[type])
                $a_like.find("span.like-num").text(num2str(response["count"]))
            }
        })
    } else {
        $.ajax({
            type: "POST",
            url: "/update_like",
            data: {
                post_id_give: post_id,
                type_give: type,
                action_give: "like"
            },
            success: function (response) {
                console.log("like")
                $i_like.addClass(like[type]).removeClass(no_like[type])
                $a_like.find("span.like-num").text(response["count"])
            }
        })
    }
}

// {% if msg %}
//     alert("{{ msg }}")
// {% endif %}
function sign_in() {
    $.ajax({
        type: "POST",
        url: "/sign_in",
        data: {
            username_give: "",
            password_give: ""
        },
        success: function (response) {
            if (response['result'] == 'success') {
                $.cookie('mytoken', response['token'], {path: '/'});

                alert('로그인 완료!')
                window.location.href = '/'
            } else {
                // 로그인이 안되면 에러메시지를 띄웁니다.
                alert(response['msg'])
            }
        }
    })
}

function sign_up() {
    let username = ""
    let password = ""
    let password2 = ""

    $.ajax({
        type: "POST",
        url: "/sign_up/save",
        data: {
            username_give: username,
            password_give: password
        },
        success: function (response) {
            alert("회원가입을 축하드립니다!")
            window.location.replace("/login")
        }
    });

}

// post 작성
function post() {
    let name = $('#input-name-pic').val()
    let file = $('#input-picture')[0].files[0]
    let comment = $("#textarea-comment").val()
    let today = new Date().toISOString()
    // form_data 초기화
    let form_data = new FormData()
    form_data.append("file_give", file)
    form_data.append("name_give", name)
    form_data.append("comment_give", comment)
    form_data.append("date_give", today)
    console.log(name, file, comment, today, form_data)

    $.ajax({
        type: "POST",
        url: "/posting",
        data: form_data,
        cache: false,
        contentType: false,
        processData: false,
        success: function (response) {
            if (response["result"] == "success") {
                alert(response["msg"])
                window.location.reload()
            }
        }
    });
}


function edit() {
    let name = $('#input-name').val()
    let file = $('#input-pic')[0].files[0]
    let comment = $("#textarea-comment").val()
    let today = new Date().toISOString()
    // form_data 초기화
    let form_data = new FormData()
    form_data.append("file_give", file)
    form_data.append("name_give", name)
    form_data.append("comment_give", comment)
    form_data.append("today_give", today)
    console.log(name, file, comment, form_data)

    $.ajax({
        type: "POST",
        url: "/update_profile",
        data: form_data,
        cache: false,
        contentType: false,
        processData: false,
        success: function (response) {
            if (response["result"] == "success") {
                alert(response["msg"])
                window.location.reload()

            }
        }
    });
}

// 몇 시간 전 계산
function time2str(date) {
    let today = new Date()
    let time = (today - date) / 1000 / 60  // 분

    if (time < 60) {
        return parseInt(time) + "분 전"
    }
    time = time / 60  // 시간
    if (time < 24) {
        return parseInt(time) + "시간 전"
    }
    time = time / 24
    if (time < 7) {
        return parseInt(time) + "일 전"
    }
    return `${date.getFullYear()}년 ${date.getMonth() + 1}월 ${date.getDate()}일`
}

// like 개수 환산
function num2str(count) {
    if (count > 10000) {
        return parseInt(count / 1000) + "k"
    }
    if (count > 500) {
        return parseInt(count / 100) / 10 + "k"
    }
    if (count == 0) {
        return ""
    }
    return count
}

// 내가 쓴 post 박스 불러오기
function get_posts(username) {
    if (username == undefined) {
        username=""
    }
    $("#post-box").empty()
    $.ajax({
        type: "GET",
        url: `/get_posts?username_give=${username}`,
        data: {},
        success: function (response) {
            if (response["result"] == "success") {
                let posts = response["posts"]
                for (let i = 0; i < posts.length; i++) {
                    let post = posts[i]
                    let time_post = new Date(post["date"])
                    let time_before = time2str(time_post)
                    // 아래 삼항 연산자와 같은 의미
                    // let class_heart = ""
                    // if (post["heart_by_me"]) {
                    //     class_heart = "fa-heart"
                    // } else {
                    //     class_heart = "fa-heart-o"
                    // }
                    // 하트, 좋아요, 별로에요 부분
                    // 조건부 삼항 연산자 : true or false / true : false
                    let class_heart = post['heart_by_me'] ? "fa-heart": "fa-heart-o"
                    let class_thumbs = post['thumbs_by_me'] ? "fa-thumbs-up": "fa-thumbs-o-up"
                    let class_thumbs_down = post['thumbs_down_by_me'] ? "fa-thumbs-down": "fa-thumbs-o-down"
                    let count_heart = post['count_heart']
                    let count_thumbs = post['count_thumbs']
                    let count_thumbs_down = post['count_thumbs_down']
                    let html_temp = `<div class="card" id="${post["_id"]}" style="max-width: 300px; margin-top: 2rem">
                                         <div class="card-image">
                                             <figure class="image is-4by3">
                                                 <img src="../static/post_pics/${post.file}" class="card-img-top" alt="Placeholder image">
                                             </figure>
                                         </div>
                                         <div class="card-content">
                                             <div class="media">
                                                 <div class="media-left">
                                                     <figure class="image is-48x48">
                                                         <img src="/static/${post['profile_pic_real']}" class="card-img-top">
                                                     </figure>
                                                 </div>
                                                 <div class="media-content">
                                                     <p class="title is-4">${post['profile_name']}</p>
                                                     <p class="subtitle is-6">${post['username']}</p>
                                                     <p><small>${time_before}</small></p>
                                                 </div>
                                             </div>
                                             <div class="content">
                                                 ${post['comment']}
                                             </div>
                                             <nav class="level is-mobile">
                                                 <div class="level-left">
                                                     <a class="level-item is-sparta" aria-label="heart" onclick="toggle_like('${post['_id']}', 'heart')">
                                                         <span class="icon is-small"><i class="fa ${num2str(class_heart)}"
                                                                                aria-hidden="true"></i></span>&nbsp;<span class="like-num">${count_heart}</span>
                                                     </a>
                                                     <a class="level-item is-sparta" aria-label="thumbs" onclick="toggle_like('${post['_id']}', 'thumbs')">
                                                         <span class="icon is-small"><i class="fa ${num2str(class_thumbs)}"
                                                                                aria-hidden="true"></i></span>&nbsp;<span class="like-num">${count_thumbs}</span>
                                                     </a>
                                                     <a class="level-item is-sparta" aria-label="thumbs_down" onclick="toggle_like('${post['_id']}', 'thumbs_down')">
                                                         <span class="icon is-small"><i class="fa ${num2str(class_thumbs_down)}"
                                                                                aria-hidden="true"></i></span>&nbsp;<span class="like-num">${count_thumbs_down}</span>
                                                     </a>
                                                 </div>
                                             </nav>
                                         </div>
                                     </div>`
                    $("#post-box").append(html_temp)
                }
            }
        }
    })

}
