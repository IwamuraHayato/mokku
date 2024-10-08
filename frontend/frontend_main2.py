import streamlit as st
import pandas as pd
import os
import base64
import streamlit.components.v1 as components
import pathlib
import shutil
from bs4 import BeautifulSoup

GA_TRACKING_ID = "G-C61D8H9VCJ"  # ここにGA4のトラッキングIDを入力

# Google Analytics 4のトラッキングコード
ga4_code = f"""
<!-- Google tag (gtag.js) -->
<script src="https://www.googletagmanager.com/gtag/js?id={GA_TRACKING_ID}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());

  gtag('config', '{GA_TRACKING_ID}');
</script>
"""
st.markdown(ga4_code, unsafe_allow_html=True)


# 背景画像の設定
def get_base64(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def set_background(png_file):
    bin_str = get_base64(png_file)
    page_bg_img = f"""
    <style>
    .stApp {{
        background: linear-gradient(rgba(255, 255, 255, 0.8), rgba(255, 255, 255, 0.8)), url("data:image/png;base64,{bin_str}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
    }}
    </style>
    """
    st.markdown(page_bg_img, unsafe_allow_html=True)


# 画像の相対パスを指定
image_path = 'picture/prowres_background.jpg'
set_background(image_path)


# カスタムCSSを定義
button_css = """
<style>
div.stButton > button:first-child {
    background-color: #FFA500;  /* 背景色をオレンジ色に設定 */
    color: white;  /* テキストの色を白に設定 */
    padding: 14px 20px;  /* パディングを設定 */
    margin: 8px 0;  /* マージンを設定 */
    border: none;  /* ボーダーをなしに設定 */
    cursor: pointer;  /* カーソルをポインターに設定 */
    width: 100%;  /* 幅を100%に設定 */
    font-size: 100px;
}
div.stButton > button:first-child:hover {
    opacity: 0.8;  /* ホバー時の不透明度を設定 */
}
</style>
"""

# カスタムCSSを適用
st.markdown(button_css, unsafe_allow_html=True)

# CSVファイルを読み込む（必要に応じて#コメントアウトしてください）
# ↓デプロイ用
df = pd.read_csv('frontend/mbti_personalities.csv')
df2 = pd.read_csv('frontend/output.csv')

# ↓ローカル用
# df = pd.read_csv('mbti_personalities.csv')
# df2 = pd.read_csv('output.csv')


# 'タイプ' と '名称' を組み合わせた表示用のリストを作成
df['タイプ名称'] = df['タイプ'] + ' - ' + df['名称']

# タイトル
st.image('picture/Exploder_Logo.png', width=300)
st.title('タッグチーム・エクスプロイダー')
st.write('')
st.write('Tech0で新しい班を決める際、誰に声をかければよいか悩んだ経験はありませんか？')
st.write('このWebアプリはあなたのMBTIタイプから最適なチーム編成を"プロレス風"にご提案します！')
st.write('左のサイドバーからあなたのMBTIタイプとお名前を選択していただいた後に、<br>「タッグ・パートナーを探す！」ボタンを押してください。', unsafe_allow_html=True)
st.write('')
st.write('')

# 説明
st.sidebar.subheader('あなたのMBTIタイプを選択してください。')

# MBTIタイプを選択
selected_type = st.sidebar.selectbox('MBTIタイプを選択:', df['タイプ名称'])

# 選択したタイプの詳細情報を取得
selected_personality = df[df['タイプ名称'] == selected_type].iloc[0]

# 選択されたタイプの詳細を表示
st.sidebar.subheader(f"{selected_personality['タイプ']} - {selected_personality['名称']}")
st.sidebar.write(f"**特徴:** {selected_personality['特徴']}")
st.sidebar.write(f"**強み:** {selected_personality['強み']}")
st.sidebar.write(f"**弱み:** {selected_personality['弱み']}")
st.sidebar.write(f"**組織内で向いている役割:** {selected_personality['組織内で向いている役割']}")

st.sidebar.write('')
st.sidebar.write('')
st.sidebar.write('')

# 説明
st.sidebar.subheader('あなたのお名前を選択してください。')

# 名前を選択
user_name = st.sidebar.selectbox('名前を選択:', df2['Slack表示名'])

# ---------------

import csv
from openai import OpenAI
import openai
import os
import re
import requests  # HTTPリクエストを送信するためのモジュールをインポート
import json  # JSONデータを扱うためのモジュールをインポート
import pandas as pd  # pandasライブラリをインポート

# Notion APIキーを設定
NOTION_API_KEY = "secret_5BRVYRZT2WMmyWJOpS5EyrIal92hmXbKR7ublWsVoRh"

# 対象のデータベースIDを設定
DATABASE_ID = "48b945dacfa64355a4a8bb62ce6a506b"

# Notion APIのエンドポイントURLを設定
url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"

# APIリクエストのヘッダー情報を設定
headers = {
    "Notion-Version": "2022-06-28",  # Notion APIのバージョンを指定
    'Authorization': 'Bearer ' + NOTION_API_KEY,  # APIキーを含む認証情報
    'Content-Type': 'application/json',  # リクエストのコンテンツタイプをJSONに設定
}

# Notion APIにPOSTリクエストを送信し、レスポンスを取得
response = requests.post(url, headers=headers)

# レスポンスのJSONデータから 'results' 部分を取得
data = response.json().get('results')

# 'results' 内の各項目の 'properties' を抽出してリストにまとめる
contents = [i['properties'] for i in data]

# 抽出した 'properties' のデータをDataFrameに変換
df = pd.DataFrame(contents)

# 'plain_text' だけを抽出する関数を定義
def extract_plain_text(cell):
    if isinstance(cell, dict):  # cellが辞書であるか確認
        text_content = cell.get('rich_text', cell.get('title', []))  # 'rich_text' または 'title' を取得
        if isinstance(text_content, list) and len(text_content) > 0:  # リストであり、空でないか確認
            return text_content[0].get('plain_text', None)  # 'plain_text' を取得して返す
    return None  # 該当がない場合は None を返す

# DataFrameの全セルに 'plain_text' を適用し、新しいDataFrameを作成
df_plain_text = df.map(extract_plain_text)

# 特定の列だけを抽出して新しいDataFrameを作成
df_for_GPT = df_plain_text[['Slack表示名','自己紹介', '業界', '関心のある領域', 
                             'Tech0のPJTで8期の仲間と協働する際に大切にしたいと思うこと', 
                             'PJTをする上で自分が得意なこと・苦手なこと', 
                             'Tech0の参加動機と１年後に到達したい・達成したいこと',
                             '自己紹介LP']]
# 行をランダムに入れ替える
df_for_GPT = df_for_GPT.sample(frac=1).reset_index(drop=True)
# こっちがデプロイ環境用のコード
# OPENAI_API_KEYを含むとPushできないため実行時は有効にしてください
api_key = st.secrets["OPENAI_API_KEY"]


# こっちがローカル環境で確認する用のコード
# OPENAI_API_KEYを含むとPushできないため実行時は有効にしてください
# api_key = os.getenv("OPEN_API_KEY")

api_key = st.secrets["OPENAI_API_KEY"]

# openAIの機能をclientに代入
# client = OpenAI()

# OpenAIのAPIキーを設定 Push時はAPIキーを削除して　変数api_keyを有効にしてください　
#ローカル用　openai.api_key = "******"
openai.api_key = api_key

# 対象者のMBTIタイプ
# user_mbti = "INTP"

# CSVファイルを読み込み ＝＝＝＞　データフレームから読み込みに変更
# with open('output.csv', newline='', encoding='utf-8') as csvfile:
reader = df_for_GPT.to_dict(orient='records')
people = list(reader)

def find_best_matches(people, user_name, user_mbti):

    persons = ""
    for person in people:
        persons = persons + str(f"【名前】 {person['Slack表示名']} \
                【自己紹介】 {person['自己紹介']}, \
                【得意な業界】 {person['業界']}, \
                【関心のある領域】 {person['関心のある領域']}, \
                【協働で大切にしたいこと】 {person['Tech0のPJTで8期の仲間と協働する際に大切にしたいと思うこと']}, \
                【プロジェクト推進で得意なこと/苦手なこと】 {person['PJTをする上で自分が得意なこと・苦手なこと']}, \
                【参加動機や達成したいこと】 {person['Tech0の参加動機と１年後に到達したい・達成したいこと']}").replace("\n","").replace(" ","") + "\n\n"
    
    prompt = f"MBTIタイプは{user_mbti}の{user_name}がチームを組む際にターゲットと相性が良いと思われる人物を、以下の手順で選んでください。\
            手順始まり \
                対象者全員のMBTIタイプを推定してください \
                対象者全員の順番をランダムに変更してください \
                推定MBTIタイプやその他の情報をもとに対象者全員の中から、{user_name}のMBTIタイプ{user_mbti}との合致度合いをスコアリングしてください \
                全ての対象者のスコアから最もスコアが高い3名を選んでください。 \
                選んだ3名と{user_name}とのMBTI以外の相性も、あらためて確認し選定理由を更新してください。\
                この選定理由には対象者情報の【自己紹介】【得意な業界】【関心のある領域】【協働で大切にしたいこと】【プロジェクト推進で得意なこと/苦手なこと】 【参加動機や達成したいこと】の内容も含めてください \
                選んだ3名それぞれの選定理由とペアでプロレスをする際の必殺技名を提案してください \
                全ての解答の最後に、選んだ人物の推定MBTIタイプと、自分が入力したMBTIタイプとの相性についての説明を追加してください。\
                この説明は固定文字列\"__\"から始めてください。この説明には改行\nを含めないでください。 \
            手順終わり \
            以下の条件に従ってください。\n \
                選ぶ3名に{user_name}を含めないでください\n \
                選ぶ3名は、重複させないでください\n \
                **対象者の順番に関係なく、全ての対象者をシャッフルして平等に評価し、最適な3名を選んでください。\n \
                対象者リストの順序に影響されないよう、全対象者を独立して評価した結果、3名を選んでください。**\n \
                できるだけ異なる特性を持った人物を選び、チーム全体のバランスを考慮してください。\n \
                **ランダム性を持たせて選び、特定の順序に依存しないようにしてください。**\n \
                項目には余計な記号や装飾（**など）をつけないでください\n \
                【名前】や【選定理由】その他の項目に、人物の名前を使う際は提供されたアルファベットの名前のみを用い、\
                **一切の変換（漢字、カタカナ、ひらがな、アルファベットの大小文字変換など）を行わず、\
                インプットされた文字列をそのまま使用してください**。\n \
                指定した形式に正確に従って出力してください\n \
                全ての回答は淡々と提案内容を述べるのではなく、「熱血プロレスラー」になり切り、熱のこもった口調でお願いします\n \
                熱のこもった口調とは、いわゆる「ですます」口調の丁寧な言葉遣いではなく、「オラオラ」感があふれる感じの口調です\n \
                プロレスラーが試合終了後のリング上でマイクパフォーマンスを行う時と同じくらいの高いテンションでお願いします\n \
            **結果は、次の形式に忠実に従って、出力してください。この形式以外の情報は一切出力しないでください**\n \
            形式の指定はじまり\n\
                【名前】[名前をそのまま出力]\n \
                【選定理由】[選定理由をそのまま出力]\n \
                【推定MBTI】[推定MBTIタイプをアルファベット4桁のみで出力]\n \
                【必殺技】[必殺技の名前をそのまま出力]\n \
            形式の指定終わり\n \
            対象者の情報はじまり\n" + persons + "\n対象者の情報終わり"

    response =  openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "user", "content": prompt },
        ],
    )
    
    # コンテンツを抽出
    content = response.choices[0].message.content.strip()
    print(content)
    
    # 対象者と選定理由を抽出するための正規表現パターン
    pattern = r"【名前】\s*(.*?)\s*【選定理由】\s*(.*?)\s*【推定MBTI】\s*(.*?)\s*【必殺技】\s*(.*?)\s*(?=【名前】|$)"
    matches = re.findall(pattern, content, re.DOTALL)

    # 結果を配列に格納
    result = [{"名前": match[0], "選定理由": match[1], "推定MBTI": match[2], "必殺技": match[3]} for match in matches]

    return result

# API呼び出しと結果表示
if st.button('タッグ・パートナーを探す！'):
    st.write("OpenAI APIを呼び出しています...")
    best_matches = find_best_matches(people, user_name, selected_type)
    # dummy
    # best_matches = [{'名前': 'Tnaka Yasuhiro-8', '選定理由': '彼の全力投入フルスロットルの姿勢に惹かれるんだ！気合いが入ったプロジェクトは彼と決まり！商談や事業創出のストーリー作りが得意な彼は、チームの力に絶対なる。', '推定MBTI': 'ENFJ', '必殺技': 'フルスロットルストーリーサイクロン'}, {'名前': 'Takahashi Hiroaki-8', '選定理由': '資料作りのプロ！プレゼンを盛り上げる力は抜群だ。チームのビジョンを一緒に描いて、成功の秘訣を分かち合う仲間にうってつけだ！', '推定MBTI': 'ESFJ', '必殺技': 'ピッチパワフルスラップ'}, {'名前': 'Sugiyama Shoichi-8', '選定理由': '彼は決断力があり、リアルな視点で進行ができる力量がある。エンジニアとのコミュニケーション強化に彼の経験が役立つはずだ！', '推定MBTI': 'ENTJ', '必殺技': 'デシジョンメイキングスラム  \n\nてなわけで、この3人、Nakamura Taijiとガッチリと組んだら相乗効果が抜群だぜ！ENFJ、ESFJ、ENTJの組み合わせは、計画的な戦略を立てて目標に向かうのにピッタリだ！INTJのNakamura Taijiとの相性も良くて、思考の深さと行動のバランスがとれる連携が生まれるぜ！これから、熱い戦いを繰り広げる準備が整った！いざ、プロジェクトの成功へ突き進もう！'}]
    print(best_matches)

    if len(best_matches) == 0:
        st.error("結果が取得できませんでした。")
        exit
    
    st.write("結果を取得しました。")
    st.subheader('あなたにピッタリなタッグ・パートナーはこちら！')

    # 結果表示
    col = st.columns(3)
    resComment = ""

    for idx, match in enumerate(best_matches):
        resName = match['名前']
        resReason = match['選定理由']
        resMbti = match["推定MBTI"]
        resSpecial = match["必殺技"]
        print("選定者：" + resName)

        #最終行に含まれるコメント抽出
        if(idx == 2):
            try:
                temp = resSpecial.split("__")    
                resSpecial = str(temp[0]).replace("\n","")
                resComment = temp[1]
            except:
                resComment = "split Error:" + resSpecial

        # 出力イメージパス ※MBTIタイプ.jpgで保存される想定
        pathImage = f"picture/{resMbti}.jpg" # ローカル用
        
        # 自己紹介LPの取得
        resLP = None
        for temp in people:
            if str(temp.get('Slack表示名')).replace(" ","") == resName:
                resLP = temp.get('自己紹介LP')
                print(resLP)
                break
                
        with col[idx]:
            st.header(resName)
            st.image(pathImage)
            st.write(f"(推定MBTIタイプ: 「{resMbti}」)")
            st.write(resReason)
            st.write(f"必殺技:{resSpecial}")
            # 自己紹介LP
            if resLP:
                strWrite = f"[自己紹介LP]({resLP})"
                st.markdown(strWrite)
    
    # コメント出力
    st.header(resComment)
    # --- ここにSlackワークスペースを開くボタンを追加します ---
    st.link_button("SlackでDMを送る", "https://app.slack.com/client/T03L9C10DJR/C03LC9SRN0J")
