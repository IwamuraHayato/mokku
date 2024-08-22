import streamlit as st
import pandas as pd

# CSVファイルを読み込む
df = pd.read_csv('mbti_personalities.csv', delimiter='\t')
df2 = pd.read_csv('output.csv')

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
import os
import re

# OPENAI_API_KEYを含むとPushできないため実行時は有効にしてください
api_key = os.getenv("OPEN_API_KEY")

# openAIの機能をclientに代入
client = OpenAI()

# 対象者のMBTIタイプ
# user_mbti = "INTP"

# CSVファイルを読み込み
with open('output.csv', newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    people = list(reader)

def find_best_matches(people, selected_type, top_n=3):
    prompts = []
    persons = ""
    for person in people:
        persons = persons + str(f"名前: {person['Slack表示名']} 関心領域: {person['関心のある領域']}, 得意・不得意: {person['PJTをする上で自分が得意なこと・苦手なこと']},")
    prompt = f"MBTIタイプが{selected_type}の人物と合う人物を以下から3名選んでください。 " + persons + "。対象者は、名前：,選定理由:形式で出力してください"
    response =  client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": prompt },
        ],
    )
        
    # コンテンツを抽出
    content = response.choices[0].message.content.strip()
    print(content)

    # 対象者と選定理由を抽出するための正規表現パターン
    pattern = r"対象者は、名前：([^,]+), 選定理由: ([^\n]+)"
    # 正規表現による抽出
    matches = re.findall(pattern, content)
    # 結果を配列に格納
    result = [{"名前": match[0], "選定理由": match[1]} for match in matches]

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
