# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, redirect, url_for
import numpy as np
import datetime
import pytz
import json
import os

app = Flask(__name__)

# JSONファイルのパス
DATA_FILE = "gacha_data.json"

# Main
class VO(object):
    def __init__(self):
        self._count = 0
        self._price = 0
        self.srplus_list = ["景品1", "景品2", "景品3", "景品4", "景品5", 
                            "景品6", "景品7", "景品8", "景品9", "景品10"]
        self.srplus_collected = []  # 引いたSR+を保持
        self.load_data()  # JSONファイルからデータを読み込む

    def getcount(self):
        return self._count

    def setcount(self, count):
        self._count = count

    def getprice(self):
        return self._price

    def setprice(self, price):
        self._price = price

    def reset(self):
        self._count = 0
        self._price = 0
        self.srplus_list = ["景品1", "景品2", "景品3", "景品4", "景品5", 
                            "景品6", "景品7", "景品8", "景品9", "景品10"]
        self.srplus_collected = []  # リセット時にクリア
        self.delete_data()

    count = property(getcount, setcount)
    price = property(getprice, setprice)

    def save_data(self):
      """データをJSONファイルに保存"""
      data = {
          "count": self._count,
          "price": self._price,
          "srplus_list": self.srplus_list,
          "srplus_collected": self.srplus_collected
      }
      with open(DATA_FILE, "w") as f:
          json.dump(data, f)

    def load_data(self):
      """JSONファイルからデータを読み込む"""
      if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
          data = json.load(f)
          self._count = data["count"]
          self._price = data["price"]
          self.srplus_list = data["srplus_list"]
          self.srplus_collected = data["srplus_collected"]

    def delete_data(self):
      """JSONファイルを削除する"""
      if os.path.exists(DATA_FILE):
        os.remove(DATA_FILE)



vo = VO()

# 各レアリティに対応する画像リスト (仮定：ファイル名は f001.jpg ～ fXXX.jpg)
images = {
    "N": [f"/static/img/N/f{i:03d}.jpg" for i in range(1, 44)],  # 43種類
    "N+": [f"/static/img/N+/f{i:03d}.jpg" for i in range(1, 44)],  # 43種類
    "R": [f"/static/img/R/f{i:03d}.jpg" for i in range(1, 135)],  # 134種類
    "R+": [f"/static/img/R+/f{i:03d}.jpg" for i in range(1, 100)],  # 99種類
    "SR": [f"/static/img/SR/f{i:03d}.jpg" for i in range(1, 26)],  # 25種類
    "SR+": [f"/static/img/SR+/f{i:03d}.jpg" for i in range(1, 27)]  # 26種類
}

def check_srplus(premium):
    """SR+景品が揃ったかどうかをチェックする"""
    if premium in vo.srplus_list:
        vo.srplus_list.remove(premium)  # 未取得のSR+を削除
        vo.srplus_collected.append(premium)

    # すべてのSR+が揃ったかどうかを返す
    return len(vo.srplus_list) == 0

def pickup_premium():
    """SR+の景品を確定して排出する"""
    """SR+と表記できない為srsrと表記する"""
    srsr = ["景品1", "景品2", "景品3", "景品4", "景品5", "景品6", "景品7",
          "景品8", "景品9", "景品10"]
    return np.random.choice(srsr)

def pickup_rare(weight):
    """重みに応じてレアガチャを排出する"""
    rarities = ["N", "N+", "R", "R+", "SR", "SR+"]
    picked_rarity = np.random.choice(rarities, p=weight)
    picked_rarity = str(picked_rarity)

    # レアリティに応じた画像をランダムに選択
    picked_image = np.random.choice(images[picked_rarity])

    if picked_rarity == "SR+":
        premium = pickup_premium()
        picked_rarity = "".join((picked_rarity, "(", premium, ")"))
        if check_srplus(premium):
           return picked_rarity, picked_image  # SR+が揃ったらTrueを返す
        else:
          return picked_rarity, picked_image

    return picked_rarity, picked_image  # 揃っていなければFalseを返す


def pickup11_rare(weight11):
    """重みに応じて11連レアガチャを排出する"""
    rarities = ["R", "R+", "SR", "SR+"]
    picked_rarity = np.random.choice(rarities, p=weight11)
    picked_rarity = str(picked_rarity)

    # レアリティに応じた画像をランダムに選択
    picked_image = np.random.choice(images[picked_rarity])

    if picked_rarity == "SR+":
        premium = pickup_premium()
        picked_rarity = "".join((picked_rarity, "(", premium, ")"))
        if check_srplus(premium):
            return picked_rarity, picked_image  # SR+が揃ったらTrueを返す
        else:
          return picked_rarity, picked_image

    return picked_rarity, picked_image  # 揃っていなければFalseを返す



def turn_rare():
    """レアガチャを回す"""
    result = []
    weight = [0.33, 0.25, 0.20, 0.15, 0.05, 0.02]
    rarity, image = pickup_rare(weight)
    result.append((rarity, image))

    if rarity.startswith("SR+") and check_srplus(rarity.split("(")[1][:-1]):
        message = f"SR+が全て揃いました！合計 {vo.count} 回、{vo.price} 円"
        vo.save_data()
        return result, message

    # resultが空の場合はダミーの値を設定して返す
    if not result:
        vo.save_data()
        return [("None", "/static/img/N/f001.jpg")]

    vo.save_data()
    return result

def turn_11rare():
    """11連レアガチャを回す"""
    result = []
    weight11 = [0.57, 0.30, 0.10, 0.03]
    srplus_complete = False
    for v in range(0, 10):
        rarity, image = pickup11_rare(weight11)  # SR+排出をチェック
        result.append((rarity, image))
        if rarity.startswith("SR+") and check_srplus(rarity.split("(")[1][:-1]):
          srplus_complete = True


    result.append(("SR", "/static/img/SR/f001.jpg"))  # 11回目はSR固定
    if srplus_complete or len(vo.srplus_list) == 0:  # SR+が揃ったかチェック
        message = f"SR+が全て揃いました！合計 {vo.count} 回、{vo.price} 円"
        vo.save_data()
        return result, message

    # resultが空の場合はダミーの値を設定して返す
    if not result:
        vo.save_data()
        return [("None", "/static/img/N/f001.jpg")] * 11

    vo.save_data()
    return result


# Routing
@app.route('/')
def index():
    title = "ようこそ"
    message = "ガチャを回すにはボタンをクリックしてください"
    return render_template('index.html',
                           message=message, title=title)

@app.route('/post', methods=['POST', 'GET'])
def post():
    jst = pytz.timezone('Asia/Tokyo')
    time = datetime.datetime.now(jst).strftime("%H:%M:%S")  # 日本時間で時刻を取得
    message = ""
    if request.method == 'POST':
        result = []
        if 'rare' in request.form:
            title = "ガチャを回しました！"
            vo.price = vo.price + 100
            vo.count = vo.count + 1
            result = turn_rare()
        if '11rare' in request.form:
            title = "ガチャを回しました！"
            vo.price = vo.price + 1000
            vo.count = vo.count + 11
            result = turn_11rare()
        if 'reset' in request.form:
            title = "リセットしました"
            vo.reset()  # リセット機能でSR+の進捗もリセット
            result = None # 空のリストではなく、Noneを渡すように変更
            message = "リセットしました"
        return render_template('index.html',
                               result=result, title=title,
                               time=time, vo=vo,
                               message=message)
    else:
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0')

"""
# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, redirect, url_for
import numpy as np
import datetime
import pytz

app = Flask(__name__)

# Main
class VO(object):
    def __init__(self):
        self._count = 0
        self._price = 0
        self.srplus_list = ["景品1", "景品2", "景品3", "景品4", "景品5", 
                            "景品6", "景品7", "景品8", "景品9", "景品10"]
        self.srplus_collected = []  # 引いたSR+を保持

    def getcount(self):
        return self._count

    def setcount(self, count):
        self._count = count

    def getprice(self):
        return self._price

    def setprice(self, price):
        self._price = price

    def reset(self):
        self._count = 0
        self._price = 0
        self.srplus_list = ["景品1", "景品2", "景品3", "景品4", "景品5", 
                            "景品6", "景品7", "景品8", "景品9", "景品10"]
        self.srplus_collected = []  # リセット時にクリア

    count = property(getcount, setcount)
    price = property(getprice, setprice)


vo = VO()

# 各レアリティに対応する画像リスト (仮定：ファイル名は f001.jpg ～ fXXX.jpg)
images = {
    "N": [f"/static/img/N/f{i:03d}.jpg" for i in range(1, 44)],  # 43種類
    "N+": [f"/static/img/N+/f{i:03d}.jpg" for i in range(1, 44)],  # 43種類
    "R": [f"/static/img/R/f{i:03d}.jpg" for i in range(1, 135)],  # 134種類
    "R+": [f"/static/img/R+/f{i:03d}.jpg" for i in range(1, 100)],  # 99種類
    "SR": [f"/static/img/SR/f{i:03d}.jpg" for i in range(1, 26)],  # 25種類
    "SR+": [f"/static/img/SR+/f{i:03d}.jpg" for i in range(1, 27)]  # 26種類
}

def check_srplus(premium):
    # SR+景品が揃ったかどうかをチェックする
    if premium in vo.srplus_list:
        vo.srplus_list.remove(premium)  # 未取得のSR+を削除
        vo.srplus_collected.append(premium)

    # すべてのSR+が揃ったかどうかを返す
    return len(vo.srplus_list) == 0

def pickup_premium():
    # SR+の景品を確定して排出する
    # SR+と表記できない為srsrと表記する
    srsr = ["景品1", "景品2", "景品3", "景品4", "景品5", "景品6", "景品7",
          "景品8", "景品9", "景品10"]
    return np.random.choice(srsr)

def pickup_rare(weight):
    # 重みに応じてレアガチャを排出する
    rarities = ["N", "N+", "R", "R+", "SR", "SR+"]
    picked_rarity = np.random.choice(rarities, p=weight)
    picked_rarity = str(picked_rarity)

    # レアリティに応じた画像をランダムに選択
    picked_image = np.random.choice(images[picked_rarity])

    if picked_rarity == "SR+":
        premium = pickup_premium()
        picked_rarity = "".join((picked_rarity, "(", premium, ")"))
        if check_srplus(premium):
           return picked_rarity, picked_image  # SR+が揃ったらTrueを返す
        else:
          return picked_rarity, picked_image

    return picked_rarity, picked_image  # 揃っていなければFalseを返す


def pickup11_rare(weight11):
    # 重みに応じて11連レアガチャを排出する
    rarities = ["R", "R+", "SR", "SR+"]
    picked_rarity = np.random.choice(rarities, p=weight11)
    picked_rarity = str(picked_rarity)

    # レアリティに応じた画像をランダムに選択
    picked_image = np.random.choice(images[picked_rarity])

    if picked_rarity == "SR+":
        premium = pickup_premium()
        picked_rarity = "".join((picked_rarity, "(", premium, ")"))
        if check_srplus(premium):
            return picked_rarity, picked_image  # SR+が揃ったらTrueを返す
        else:
          return picked_rarity, picked_image

    return picked_rarity, picked_image  # 揃っていなければFalseを返す



def turn_rare():
    # レアガチャを回す
    result = []
    weight = [0.33, 0.25, 0.20, 0.15, 0.05, 0.02]
    rarity, image = pickup_rare(weight)
    result.append((rarity, image))

    if rarity.startswith("SR+") and check_srplus(rarity.split("(")[1][:-1]):
        message = f"SR+が全て揃いました！合計 {vo.count} 回、{vo.price} 円"
        return result, message

    # resultが空の場合はダミーの値を設定して返す
    if not result:
        return [("None", "/static/img/N/f001.jpg")], ""

    return result

def turn_11rare():
    # 11連レアガチャを回す
    result = []
    weight11 = [0.57, 0.30, 0.10, 0.03]
    srplus_complete = False
    for v in range(0, 10):
        rarity, image = pickup11_rare(weight11)  # SR+排出をチェック
        result.append((rarity, image))
        if rarity.startswith("SR+") and check_srplus(rarity.split("(")[1][:-1]):
          srplus_complete = True


    result.append(("SR", "/static/img/SR/f001.jpg"))  # 11回目はSR固定
    if srplus_complete or len(vo.srplus_list) == 0:  # SR+が揃ったかチェック
        message = f"SR+が全て揃いました！合計 {vo.count} 回、{vo.price} 円"
        return result, message

    # resultが空の場合はダミーの値を設定して返す
    if not result:
        return [("None", "/static/img/N/f001.jpg")] * 11, ""

    return result


# Routing
@app.route('/')
def index():
    title = "ようこそ"
    message = "ガチャを回すにはボタンをクリックしてください"
    return render_template('index.html',
                           message=message, title=title)

@app.route('/post', methods=['POST', 'GET'])
def post():
    jst = pytz.timezone('Asia/Tokyo')
    time = datetime.datetime.now(jst).strftime("%H:%M:%S")  # 日本時間で時刻を取得
    message = ""
    title = "ガチャを回すにはボタンをクリックしてください"
    if request.method == 'POST':
        result = []
        if 'rare' in request.form:
            title = "ガチャを回しました！"
            vo.price = vo.price + 100
            vo.count = vo.count + 1
            result = turn_rare()
        if '11rare' in request.form:
            title = "ガチャを回しました！"
            vo.price = vo.price + 1000
            vo.count = vo.count + 11
            result = turn_11rare()
        if 'reset' in request.form:
            title = "リセットしました"
            vo.reset()  # リセット機能でSR+の進捗もリセット
            result = None # 空のリストではなく、Noneを渡すように変更
            message = "リセットしました"
        return render_template('index.html',
                               result=result, title=title,
                               time=time, vo=vo,
                               message=message)
    else:
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0')
"""