import streamlit as st
import google.generativeai as genai
import datetime

# --- ページ設定 ---
st.set_page_config(page_title="カロりん", layout="centered")

# --- タイトルと説明 ---
st.title("**カロりん！今これ食べていい？😋**")
st.markdown("""
やさしい栄養士AI「**カロりん**」があなたの食事をサポートします🍓  
気になる食べ物を食べていいか、やさしくアドバイスしてくれます！

---

### 🌟 このアプリでできること
- 食べたいものが今の自分に合っているかをAIがチェック
- 体重目標と期限から、1日あたりのカロリー目安を自動計算
- 今日の食事・運動量をふまえて、やさしく判断してくれます♪

---

### 📝 使い方
1. 左のサイドバーに **体重・目標・運動量・今日の食事** を入力
2. 下の入力欄に「食べたいもの」（例：チョコ、ラーメンなど）を入力
3. AI栄養士「カロりん」が判断して、コメントしてくれます💬
4. チャット形式でやりとりでき、何度でも聞けます♪

---

> 🍀 「○○食べてもいい？」という不安、カロりんがやさしく答えます！
""")

# --- APIキー入力 ---
api_key = st.sidebar.text_input("🔑 Gemini APIキーを入力", type="password")
if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.0-flash-lite")

# --- ユーザー情報 ---
st.sidebar.header("📋 あなたの情報")
weight = st.sidebar.number_input("現在の体重 (kg)", 30, 150, 60)
goal_weight = st.sidebar.number_input("目標体重 (kg)", 30, 150, 55)
deadline = st.sidebar.date_input("目標達成期限", value=datetime.date.today() + datetime.timedelta(weeks=8))
exercise = st.sidebar.selectbox("今日の運動量", ["少ない", "普通", "多い"])
food_today = st.sidebar.text_area("🍱 今日食べたもの", placeholder="例：朝 トーストと卵 / 昼 ラーメン / 夜 唐揚げ定食")

# --- ユーザー入力 ---
user_question = st.chat_input("🍩 今食べたいものをカロりんに聞いてみよう！")

# --- セッション履歴初期化 ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- カロリー計算 ---
def calculate_target_calories(weight, goal_weight, deadline):
    days = (deadline - datetime.date.today()).days
    if days <= 0:
        return None
    diff_kg = weight - goal_weight
    kcal_per_kg = 7200
    total_kcal_to_lose = diff_kg * kcal_per_kg
    daily_kcal_deficit = total_kcal_to_lose / days
    estimated_maintenance = weight * 30
    return round(estimated_maintenance - daily_kcal_deficit)

# --- プロンプト生成 ---
def build_prompt(food_today, exercise, user_question, target_kcal):
    return f"""
あなたはやさしく親しみやすい栄養士AI「カロりん」です。

# 今日食べたもの:
{food_today}
# 今日の運動量:
{exercise}
# 目標摂取カロリー:
{target_kcal} kcal
# 質問:
「{user_question}」を今食べてもいいですか？

以下を守ってください：
- 食べ物の推定カロリーを考慮
- カロリー目標と比較して、やさしいアドバイス
- 可能なら「代替案」も提案
"""

# --- 回答処理 ---
if api_key and user_question:
    target_kcal = calculate_target_calories(weight, goal_weight, deadline)
    
    if target_kcal is None:
        with st.chat_message("assistant", avatar="🍓"):
            st.error("⚠️ 達成期限が過ぎています。未来の日付を選んでね。")
    else:
        with st.spinner("カロりんが考え中..."):
            try:
                prompt = build_prompt(food_today, exercise, user_question, target_kcal)
                response = model.generate_content(prompt)
                answer = response.text.strip()

                # 履歴に保存
                st.session_state.chat_history.append({"role": "user", "content": user_question})
                st.session_state.chat_history.append({"role": "assistant", "content": answer})

            except Exception as e:
                with st.chat_message("assistant", avatar="🍓"):
                    st.error("エラー発生: " + str(e))

# --- チャット履歴表示 ---
for chat in st.session_state.chat_history:
    with st.chat_message(chat["role"], avatar="🧑" if chat["role"] == "user" else "🍓"):
        st.markdown(chat["content"])

# --- リセットボタン ---
if st.button("🧹 チャット履歴をリセット"):
    st.session_state.chat_history = []
    st.success("リセットしました！✨")
