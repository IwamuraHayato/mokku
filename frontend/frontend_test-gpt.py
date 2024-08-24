import streamlit as st
import pandas as pd

# CSVファイルを読み込む（必要に応じて#コメントアウトしてください）
# ↓デプロイ用
# df = pd.read_csv('frontend/mbti_personalities.csv')
# df2 = pd.read_csv('frontend/output.csv')

# ↓ローカル用
df = pd.read_csv('mbti_personalities.csv')
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
user_name = st.selectbox('名前を選択:', df2['Slack表示名'])

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

# こっちがデプロイ環境用のコード
# OPENAI_API_KEYを含むとPushできないため実行時は有効にしてください
# api_key = st.secrets["OPENAI_API_KEY"]


# こっちがローカル環境で確認する用のコード
# OPENAI_API_KEYを含むとPushできないため実行時は有効にしてください

api_key = os.getenv("OPEN_API_KEY")
# api_key = st.secrets["OPENAI_API_KEY"]

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
        # persons = persons + \
            # str(f"【名前】 {person['Slack表示名']}).replace, \
            #     【自己紹介】 {person['自己紹介']}, \
            #     【得意な業界】 {person['業界']}, \
            #     【関心のある領域】 {person['関心のある領域']}, \
            #     【協働で大切にしたいこと】 {person['Tech0のPJTで8期の仲間と協働する際に大切にしたいと思うこと']}, \
            #     【プロジェクト推進で得意なこと/苦手なこと】 {person['PJTをする上で自分が得意なこと・苦手なこと']}, \
            #     【参加動機や達成したいこと】 {person['Tech0の参加動機と１年後に到達したい・達成したいこと']},") + "\n"
            persons = persons + str(f"【名前】 {person['Slack表示名']} \
                【自己紹介】 {person['自己紹介']}, \
                【得意な業界】 {person['業界']}, \
                【関心のある領域】 {person['関心のある領域']}, \
                【協働で大切にしたいこと】 {person['Tech0のPJTで8期の仲間と協働する際に大切にしたいと思うこと']}, \
                【プロジェクト推進で得意なこと/苦手なこと】 {person['PJTをする上で自分が得意なこと・苦手なこと']}, \
                【参加動機や達成したいこと】 {person['Tech0の参加動機と１年後に到達したい・達成したいこと']}").replace("\n","").replace(" ","") + "\n\n"     

    # print(persons)

    prompt = f"名前{user_name}のMBTIタイプは{user_mbti}です。\
            プロジェクトチームを組む際に{user_name}と相性が良いと思われる人物を、対象者全員の中から3名選び、それぞれのMBTIタイプを推測してください。\
            また、選んだ人物とペアでプロレスをする際の必殺技の名前も提案してください。\
            以下の条件に従ってください。\n \
                選ぶ3名に{user_name}を含めないでください\n \
                選ぶ3名は、重複させないでください\n \
                **対象者の順番に関係なく、全ての対象者をシャッフルして平等に評価し、最適な3名を選んでください。\n \
                対象者リストの順序に影響されないよう、全対象者を独立して評価した結果、3名を選んでください。**\n \
                できるだけ異なる特性を持った人物を選び、チーム全体のバランスを考慮してください。\n \
                **ランダム性を持たせて選び、特定の順序に依存しないようにしてください。**\n \
                項目には余計な記号や装飾（**など）をつけないでください\n \
                {user_name}および選んだ人物の名前を出力する際は、\
                **一切の変換（漢字、カタカナ、ひらがな、アルファベットの大小文字変換など）を行わず、\
                元の文字列をそのまま使用してください**。\n \
                指定した形式に正確に従って出力してください\n \
                淡々と提案内容を述べるのではなく、熱血プロレスラーの熱のこもった口調でお願いします\n \
                いわゆる「ですます」口調の丁寧な言葉遣いではなく、「オラオラ」感があふれる感じの口調でお願いします\n \
                全ての解答の最後に、選んだ人物の推定MBTIタイプと、自分が入力したMBTIタイプとの相性についての説明を追加してください。この説明の中では改行しないでください\n \
            対象者は、次の形式に従って、出力してください。\n \
            形式の指定はじまり\n\
                【名前】[名前をそのまま出力]\n \
                【選定理由】[選定理由をそのまま出力]\n \
                【推定MBTI】[推定MBTIタイプをアルファベット4桁のみで出力]\n \
                【必殺技】[必殺技の名前をそのまま出力]\n \
            形式の指定終わり\n \
            対象者の情報はじまり\n" + persons + "\n対象者の情報終わり"

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
    pattern = r"【名前】\s*(.*?)\s*【選定理由】\s*(.*?)\s*【推定MBTI】\s*(.*?)\s*【必殺技】\s*(.*?)\s*(?=【名前】|$)"
    matches = re.findall(pattern, content, re.DOTALL)

    # 結果を配列に格納
    result = [{"名前": match[0], "選定理由": match[1], "推定MBTI": match[2], "必殺技": match[3]} for match in matches]

    return result

# API呼び出しと結果表示
if st.button('相性の良いメンバーを提案'):
    st.write("APIを呼び出しています...")
    best_matches = find_best_matches(people, user_name, selected_type)
    # dummy for test
    # best_matches = [{'名前': 'Tnaka Yasuhiro-8', '選定理由': '彼の全力投入フルスロットルの姿勢に惹かれるんだ！気合いが入ったプロジェクトは彼と決まり！商談や事業創出のストーリー作りが得意な彼は、チームの力に絶対なる。', '推定MBTI': 'ENFJ', '必殺技': 'フルスロットルストーリーサイクロン'}, {'名前': 'Takahashi Hiroaki-8', '選定理由': '資料作りのプロ！プレゼンを盛り上げる力は抜群だ。チームのビジョンを一緒に描いて、成功の秘訣を分かち合う仲間にうってつけだ！', '推定MBTI': 'ESFJ', '必殺技': 'ピッチパワフルスラップ'}, {'名前': 'Sugiyama Shoichi-8', '選定理由': '彼は決断力があり、リアルな視点で進行ができる力量がある。エンジニアとのコミュニケーション強化に彼の経験が役立つはずだ！', '推定MBTI': 'ENTJ', '必殺技': 'デシジョンメイキングスラム  \n\nてなわけで、この3人、Nakamura Taijiとガッチリと組んだら相乗効果が抜群だぜ！ENFJ、ESFJ、ENTJの組み合わせは、計画的な戦略を立てて目標に向かうのにピッタリだ！INTJのNakamura Taijiとの相性も良くて、思考の深さと行動のバランスがとれる連携が生まれるぜ！これから、熱い戦いを繰り広げる準備が整った！いざ、プロジェクトの成功へ突き進もう！'}]
    # best_matches = [{'名前': 'Inoue Kai', '選定理由': 'お前の情熱はガンガン伝わってくるぞ！事業企画で新しいアイデアを生み出そうとしてる。Mikiの自由な発想と、Kaiの新規事業魂が相まって、斬新なプロジェクトが生まれること間違いなしだ ！', '推定MBTI': 'ENFJ', '必殺技': '「未来へのダッシュアッパー」\n\nここで相性を見てみると、KaiはENFJと推測してるけど、ENTPときたらまさに反発し合う特性もありつつ、お互いに引き立て合うってわけだ！みんなが集まりたくなる熱いチームになるぜ！\n\n次は行くぜ！'}, {'名前': 'Takahashi Hiroaki-8', '選定理由': 'テクノロジーへの関心があり、行動力もある！新規事業の立ち上げに向けての意欲も感じる。Mikiの討論力と、Hiroakiの論理的思考が合わされば、どんな難題も解決できる壮絶なコンビになるだろう！', '推定MBTI': 'INTJ', '必殺技': '「論理の砲撃」\n\n相性的には、INTJの冷静さとENTPの柔軟性がぶつかり合いながらも、尊重し合うことでさらなる発展があるだろう！ここでのやりとりは面白くなりそうだぜ！\n\n最後の一人だ、ラストスパートだ！'}, {'名前': 'Murai Kosuke-8', '選定理由': '幅広い経験とラテラルシンキングが得意だ！じっくり考察して、今を見つめ直す力を持っているから、Mikiの発想力と合わさって、革新的なアイデアが巻き起こるに違いない！', '推定MBTI': 'ENTJ', '必殺技': '「発想のトルネード」\n\n相性を見ると、ENTJとENTPは同じく外向的で、エネルギッシュな関係が築ける！一緒にプロレスのリングの上で新しいプロジェクトをつかみ取る姿が目に浮かぶぜ！\n\nこれで決まりだ！Miki Yukako-8には以下の3名がフィットする！  \n1. Inoue Kai  \n2. Takahashi Hiroaki-8  \n3. Murai Kosuke-8  \n\n心強い仲間達と共に、烈火の如く盛り上がってくれよな！プロジェクトの成功を目指して、以上だ！'}]
    # best_matches = [{'名前': 'Tnaka Yasuhiro-8', '選定理由': 'Yasuhiroは新規事業にリスペクトを持つ営業担当。彼の情熱と挑戦心はTiaji-8の冒険心と噛み合い、柔軟な発想を引き出すはずだ！', '推定MBTI': 'ENFP', '必殺技': 'フルスロットル・ストーリーキック'}, {'名前': 'Takahashi Hiroaki-8', '選定理由': 'Hiroakiは資料作りが得意なサービス業のプロだ！彼の論理的なアプローチとYasuhiroのクリエイティブな視点が合わさることで、プロジェクトは大いに盛り上がるだろう！', '推定MBTI': 'INFJ', '必殺技': 'ライトニングプレゼンテーション'}, {'名前': 'Sugiyama Shoichi-8', '選定理由': 'Shoichiはコンサルタントとしての枠を超え、幅広い知識を持っている。バランスの取れた思考でメンバー間のコミュニケーションを円滑にし、大きな力を発揮するだろう！', '推定MBTI': 'INTJ', '必殺技': '完璧な進行管理ラッシュ\n\nさて、Nakamura Taiji-8との相性についてだが、彼のISFPタイプは感情に基づく柔軟で創造的な思考を持っている。YasuhiroのENFPは情熱的で、協調性が高い。HiroakiのINFJは深い洞察力を持ち、珍しい視点を提供できる。ShoichiのINTJは戦略的で効率的なプランニングが得意。各メンバーがそれぞれのスキルを持ち寄ることで、チーム全体の創造性が未知の領域へと広がるのだ！\n\nこれで、熱いプロジェクトチームが組まれたぜ！みんな、準備はいいか？一緒に最高の冒険に飛び込もうぜ！'}]

    print(best_matches)

    if len(best_matches) == 0:
        st.error("結果が取得できませんでした。")
        exit
    
    st.write("結果を取得しました。")
    st.subheader('相性の良いメンバー')

    # 結果表示
    col = st.columns(3)
    resComment = ""

    for idx, match in enumerate(best_matches):
        resName = match['名前']
        resReason = match['選定理由']
        resMbti = match["推定MBTI"]
        resSpecial = match["必殺技"]
        #最終行に含まれるコメント抽出
        if(idx == 2):
            temp = resSpecial.split("\n\n")    
            resSpecial = temp[0]
            resComment = temp[1]

        # 出力イメージパス ※MBTIタイプ.jpgで保存される想定
        pathImage = f"../picture/{resMbti}.jpg" # ローカル用
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
            st.write(resReason)
            st.write(f"必殺技:{resSpecial}")
            # 自己紹介LP
            if resLP:
                strWrite = f"[自己紹介LP]({resLP})"
                st.markdown(strWrite)

    # コメント出力
    st.header(resComment)



    