import streamlit as st
import pandas as pd

# CSVファイルを読み込む
df = pd.read_csv('frontend/mbti_personalities.csv')
df2 = pd.read_csv('frontend/output.csv')

# 'タイプ' と '名称' を組み合わせた表示用のリストを作成
df['タイプ名称'] = df['タイプ'] + ' - ' + df['名称']

# タイトル
st.title('MBTIで新しい班決めをサポート！')
st.write('')
st.write('Tech0の新しい班を決める時、誰に声をかければよいか悩んだ経験はありませんか？')
st.write('このアプリはあなたのMBTIタイプから最適なチーム編成をご提案します！')
st.write('')
st.write('')

# 説明
st.subheader('あなたのMBTIタイプを選択してください。')

# MBTIタイプを選択
selected_type = st.selectbox('MBTIタイプを選択:', df['タイプ名称'])

# 選択したタイプの詳細情報を取得
selected_personality = df[df['タイプ名称'] == selected_type].iloc[0]

# 選択されたタイプの詳細を表示
st.subheader(f"{selected_personality['タイプ']} - {selected_personality['名称']}")
st.write(f"**特徴:** {selected_personality['特徴']}")
st.write(f"**強み:** {selected_personality['強み']}")
st.write(f"**弱み:** {selected_personality['弱み']}")
st.write(f"**組織内で向いている役割:** {selected_personality['組織内で向いている役割']}")

st.write('')
st.write('')
st.write('')

# 説明
st.subheader('あなたのお名前を選択してください。')

# 名前を選択
selected_type = st.selectbox('名前を選択:', df2['Slack表示名'])

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
                             'Tech0の参加動機と１年後に到達したい・達成したいこと']]

# OPENAI_API_KEYを含むとPushできないため実行時は有効にしてください
api_key = st.secrets("OPEN_API_KEY")

# openAIの機能をclientに代入
#client = OpenAI()

# OpenAIのAPIキーを設定
openai.api_key = api_key


# 対象者のMBTIタイプ
# user_mbti = "INTP"

# CSVファイルを読み込み ＝＝＝＞　データフレームから読み込みに変更
# with open('output.csv', newline='', encoding='utf-8') as csvfile:
reader = df_for_GPT.to_dict(orient='records')
people = list(reader)

def find_best_matches(people, selected_type, top_n=3):
    prompts = []
    persons = ""
    for person in people:
        persons = persons + str(f"名前: {person['Slack表示名']} 関心領域: {person['関心のある領域']}, 得意・不得意: {person['PJTをする上で自分が得意なこと・苦手なこと']},")
    prompt = f"MBTIタイプが{selected_type}の人物と合う人物を以下から3名選んでください。 " + persons + "。対象者は、名前：,選定理由:形式で出力してください"
    response =  openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": prompt },
        ],
    )
        
    # コンテンツを抽出
    content = response.choices[0].message.content.strip()
    print(content)

    # 対象者と選定理由を抽出するための正規表現パターン
    pattern = r"\*\*名前\*\*: ([\w\s-]+)\s+\*\*選定理由\*\*: ([\s\S]+?)(?=\n\d|$)"
    # 正規表現による抽出
    matches = re.findall(pattern, content)
    # 結果を配列に格納
    result = [{"名前": match[0], "選定理由": match[1].strip()} for match in matches]

    return result

# API呼び出しと結果表示
if st.button('相性の良いメンバーを提案'):
    st.write("APIを呼び出しています...")
    best_matches = find_best_matches(people, selected_type)
    print(best_matches)

    if best_matches:
        st.write("結果を取得しました。")
        st.subheader('相性の良いメンバー')
        for match in best_matches:
            st.write(f"名前: {match['名前']}, 選定理由: {match['選定理由']}")
    else:
        st.error("結果が取得できませんでした。")
