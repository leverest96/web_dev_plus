from pymongo import MongoClient
from flask import Flask, render_template, jsonify, request, redirect, url_for
import jwt
import hashlib
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config['UPLOAD_FOLDER'] = "./static/profile_pics"
app.config['UPLOAD_FOLDER'] = "./static/post_pics"

SECRET_KEY = 'HIMALAYA'

client = MongoClient('13.125.123.145', 27017, username="test", password="test")
db = client.himalaya

###################################################### 시작화면 관련 ######################################################

# 기본 페이지 / index 페이지로 갈지 login 페이지로 갈지 (토큰 필요)
@app.route('/')
def home():
    # 쿠키로부터 토큰을 받아온다.
    token_receive = request.cookies.get('mytoken')
    # except 사항이 아니라면 index.html 페이지로 이동
    try:
        # payload에 token을 해독한 것을 저장 / ID를 찾는다.
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"username": payload["id"]})
        return render_template('index.html', user_info=user_info)
    # 예외 사항(아래와 같이)이라면 login.html 페이지로 이동
    # 로그인 시간이 만료되면
    except jwt.ExpiredSignatureError:
        # login url로 msg를 띄우고 이동
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    # 로그인 정보가 없으면
    except jwt.exceptions.DecodeError:
        # login url로 msg를 띄우고 이동
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))

# login 페이지로 이동
@app.route('/login')
def login():
    # 확인 필요
    # msg를 받아와서 msg와 함께 login.html 페이지로 이동
    msg = request.args.get("msg")
    return render_template('login.html', msg=msg)

####################################################### 로그인 관련 #######################################################

# 각 사용자의 프로필과 글을 모아볼 수 있는 공간(토큰 필요)
@app.route('/user/<username>')
def user(username):
    token_receive = request.cookies.get('mytoken')
    try:
        # 해독한 토큰의 ID값과 현재 url의 ID값이 같은지 판단
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        status = (username == payload["id"])  # 내 프로필이면 True, 다른 사람 프로필 페이지면 False
        # 확인 필요
        # ID 값 자체는 필요 없이 username을 users에서 받아와서 user_info에 넣자
        user_info = db.users.find_one({"username": username}, {"_id": False})
        return render_template('user.html', user_info=user_info, status=status)
    # 로그인 시간이 만료되거나 로그인 정보가 존재하지 않으면 홈으로 돌아간다.
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))

# 로그인(토큰 생성)
@app.route('/sign_in', methods=['POST'])
def sign_in():
    # 로그인 (ID : username / PW : password)
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']
    # password 암호화
    pw_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    # username(id)과 암호화된 password를 users에서 찾는다.
    result = db.users.find_one({'username': username_receive, 'password': pw_hash})
    # result가 none이 아니라면 즉 result가 있다면
    if result is not None:
        # payload 생성 (payload에서 로그인 때 적은 username을 id로 그리고 로그인이 지속될 expiration time을 저장)
        payload = {
         'id': username_receive,
         'exp': datetime.utcnow() + timedelta(seconds=60 * 60 * 24)  # 로그인 24시간 유지
        }
        # 위의 payload를 토큰으로 암호화
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
        # response(result, token)를 json으로 변경하여 return
        return jsonify({'result': 'success', 'token': token})
    # 찾지 못하면 즉 result가 없다면
    else:
        return jsonify({'result': 'fail', 'msg': '아이디/비밀번호가 일치하지 않습니다.'})

# 로그인 직후
@app.route('/sign_up/save', methods=['POST'])
def sign_up():
    # 입력된 username(id)와 password를 받아오고 password는 암호화한다.
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']
    password_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    doc = {
        "username": username_receive,                               # 받아온 username > 아이디
        "password": password_hash,                                  # 암호화된 password > 비밀번호
        "profile_name": username_receive,                           # 받아온 username > 프로필 이름 기본값
        "profile_pic": "",                                          # 프로필 사진 파일 이름 (추가될 이미지)
        "profile_pic_real": "profile_pics/profile_placeholder.png", # 프로필 사진 기본 이미지 (시작 이미지)
        "profile_info": ""                                          # 프로필 한 마디 (적힐 코멘트)
    }
    # users에 doc을 넣어준다.
    db.users.insert_one(doc)
    return jsonify({'result': 'success'})

# ID 중복검사
@app.route('/sign_up/check_dup', methods=['POST'])
def check_dup():
    username_receive = request.form['username_give']
    # ID 값이 users에 있다면 True 없으면 False
    exists = bool(db.users.find_one({"username": username_receive}))
    return jsonify({'result': 'success', 'exists': exists})

####################################################### 프로필 관련 #######################################################

# 프로필 업데이트(토큰 필요)
@app.route('/update_profile', methods=['POST'])
def save_img():
    token_receive = request.cookies.get('mytoken')
    try:
        # 토큰 해독해서 id 값을 username이라 하고 입력된 name과 about을 각각 name_receive, about_receive로 받아온다.
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        username = payload["id"]
        name_receive = request.form["name_give"]
        about_receive = request.form["about_give"]
        # 받아온 name과 about을 프로필 이름과 정보로 각각 저장
        new_doc = {
            "profile_name": name_receive,
            "profile_info": about_receive
        }
        # 첨부한 사진에서
        if 'file_give' in request.files:
            # 첨부된 file을 불러오고
            file = request.files["file_give"]
            # file의 이름과 확장자를 각각 따로 받아온다.
            filename = secure_filename(file.filename)
            extension = filename.split(".")[-1]
            # file의 이름을 (유저 ID).(확장자)로 변경하고 profile_pics 폴더 안에 넣어준다.
            file_path = f"profile_pics/{username}.{extension}"
            # 위 profile_pics를 static 폴더 안에 넣어준다.
            file.save("./static/" + file_path)
            # file 이름과 file의 경로를 new_doc라는 set을 만든다.
            new_doc["profile_pic"] = filename
            new_doc["profile_pic_real"] = file_path
        # users에 저장될 id와 프로필의 set을 users에 업데이트시킨다.
        db.users.update_one({'username': payload['id']}, {'$set': new_doc})
        return jsonify({"result": "success", 'msg': '프로필을 업데이트했습니다.'})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))

####################################################### 포스팅 관련 #######################################################

# 포스팅 게시 (토큰 필요)
@app.route('/posting', methods=['POST'])
def posting():
    token_receive = request.cookies.get('mytoken')
    try:
        # 토큰 해독 후 username이 토큰의 id값인 녀석을 찾아 user_info라고 한다.
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"username": payload["id"]})

        # 코멘트에 적힌 글과 현재 날짜를 불러온다.
        today = datetime.now()
        name_receive = request.form["name_give"]
        file = request.files["file_give"]
        comment_receive = request.form["comment_give"]
        date_receive = request.form["date_give"]
        today_receive = today.strftime('%Y-%m-%d-%H-%M-%S')
        filename = f'file-{today_receive}'
        # 파일 형식을 따오는 코드
        extension = file.filename.split('.')[-1]
        # 따온 파일 이름과 형식을 저장해주는 코드
        save_to = f'static/post_pics/{filename}.{extension}'
        file.save(save_to)
        # username(id), 닉네임, 프로필 사진, 코멘트, 날짜 doc dictionary에 저장
        doc = {
            "username": user_info["username"],
            "profile_name": user_info["profile_name"],
            "profile_pic_real": user_info["profile_pic_real"],
            "name": name_receive,
            'file': f'{filename}.{extension}',
            "comment": comment_receive,
            "date": date_receive
        }
        db.posts.insert_one(doc)
        # 성공하면 '포스팅 성공!'을 띄우자!
        return jsonify({"result": "success", 'msg': '포스팅 성공'})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))

# 포스팅 불러오기 (토큰 필요)
@app.route("/get_posts", methods=['GET'])
def get_posts():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        # 확인 필요
        # 포스팅을 읽어올건데 조건에 상관없이 최신 20개만 불러온다.
        username_receive = request.args.get("username_give")
        if username_receive == "":
            posts = list(db.posts.find({}).sort("date", -1).limit(20))
        else:
            posts = list(db.posts.find({"username": username_receive}).sort("date", -1).limit(20))
        # 각 포스트들의 id들을 문자열로 바꾼다!
        for post in posts:
            post["_id"] = str(post["_id"])
            post["count_heart"] = db.likes.count_documents({"post_id": post["_id"], "type": "heart"})
            post["heart_by_me"] = bool(db.likes.find_one({"post_id": post["_id"], "type": "heart", "username": payload['id']}))
            post["count_star"] = db.likes.count_documents({"post_id": post["_id"], "type": "star"})
            post["star_by_me"] = bool(db.likes.find_one({"post_id": post["_id"], "type": "star", "username": payload['id']}))
            post["count_thumbs"] = db.likes.count_documents({"post_id": post["_id"], "type": "thumbs"})
            post["thumbs_by_me"] = bool(db.likes.find_one({"post_id": post["_id"], "type": "thumbs", "username": payload['id']}))
        return jsonify({"result": "success", "msg": "포스팅을 가져왔습니다.", "posts":posts})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))

# like(하트, 별, 좋아요) 업데이트 (토큰 필요)
@app.route('/update_like', methods=['POST'])
def update_like():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        # 해독된 토큰에서 id 값을 username에 넣고 users에서 찾아서 user_info에 넣어라
        user_info = db.users.find_one({"username": payload["id"]})
        # 아래 세개는 꼭 줘야한다.
        post_id_receive = request.form["post_id_give"]
        type_receive = request.form["type_give"]
        action_receive = request.form["action_give"]
        # doc dictionary에 받아온 post_id와 type를 post_id와 type 각각에 맞게 넣고 username에 user_info의 username을 가져온다.
        doc = {
            "post_id": post_id_receive,
            "username": user_info["username"],
            "type": type_receive
        }
        # like를 한다면 doc을 likes에 넣어라.
        if action_receive == "like":
            db.likes.insert_one(doc)
        # like 하지 않는다면 doc을 likes에서 지워라.
        else:
            db.likes.delete_one(doc)
        # like의 타입에 따라 입력된 개수를 likes에서 찾아서 count로 설정
        count = db.likes.count_documents({"post_id": post_id_receive, "type": type_receive})
        return jsonify({"result": "success", 'msg': 'updated', "count": count})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))

########################################################################################################################

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)