import streamlit as st
import google.generativeai as genai
import datetime

# --- ページ設定 ---
st.set_page_config(page_title="カロりん", layout="centered")
st.markdown("##カロりん！<br>今これ食べてもいいかな？", unsafe_allow_html=True)

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

---

> 🍀 「○○食べてもいい？」という不安、カロりんがやさしく答えます！
""")


# --- Gemini APIキー入力（必須） ---
api_key = st.sidebar.text_input("🔑 Gemini APIキーを入力", type="password")
if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.0-flash-lite")

# --- サイドバー：ユーザー情報入力 ---
st.sidebar.header("📋 あなたの情報")
weight = st.sidebar.number_input("現在の体重 (kg)", 30, 150, 60)
goal_weight = st.sidebar.number_input("目標体重 (kg)", 30, 150, 55)
deadline = st.sidebar.date_input("目標達成期限", value=datetime.date.today() + datetime.timedelta(weeks=8))
exercise = st.sidebar.selectbox("今日の運動量", ["少ない", "普通", "多い"])
food_today = st.sidebar.text_area("🍱 今日食べたもの", placeholder="朝：トーストと卵、昼：ラーメン、夜：唐揚げ定食")

# --- 入力欄：ユーザーが今食べたいものを相談 ---
user_question = st.text_input("今食べたいものをカロりんに相談しよう😋")

# --- セッション状態の初期化 ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "last_question" not in st.session_state:
    st.session_state.last_question = ""
if "target_kcal" not in st.session_state:
    st.session_state.target_kcal = None
if "estimated_food_kcal" not in st.session_state:
    st.session_state.estimated_food_kcal = None

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
    target_kcal = estimated_maintenance - daily_kcal_deficit
    return round(target_kcal)

# --- 食事のカロリー推定（簡易版） ---
def estimate_food_kcal(food_text):
    if not food_text:
        return 0
    items = food_text.split("、")
    return len(items) * 400  # 仮で1品約400kcal

# --- 初期化処理：初回のみ計算・保存 ---
if api_key:
    if st.session_state.target_kcal is None:
        st.session_state.target_kcal = calculate_target_calories(weight, goal_weight, deadline)
    if st.session_state.estimated_food_kcal is None and food_today:
        st.session_state.estimated_food_kcal = estimate_food_kcal(food_today)

# --- UIで表示 ---
if st.session_state.target_kcal:
    st.markdown(f"🎯 **今日の目標摂取カロリー**: `{st.session_state.target_kcal} kcal`")
if st.session_state.estimated_food_kcal is not None:
    st.markdown(f"🍱 **今日食べた量（推定）**: `{st.session_state.estimated_food_kcal} kcal`")

# --- プロンプト作成 ---
def build_prompt(food_today, exercise, user_question, target_kcal, food_kcal):
    history_text = ""
    for chat in st.session_state.chat_history:
        if chat["role"] == "user":
            history_text += f"ユーザー: {chat['content']}\n"
        else:
            history_text += f"カロりん: {chat['content']}\n"

    prompt = f"""
あなたはやさしく親しみやすい栄養士AI「カロりん」です。
以下の情報をもとに、質問に丁寧に回答してください。

# 今日の運動量:
{exercise}

# 今日食べたもの:
{food_today}
（推定摂取カロリー: 約 {food_kcal} kcal）

# 今日の目標摂取カロリー:
{target_kcal} kcal

# チャット履歴:
{history_text}

# 今の質問:
「{user_question}」を今食べてもいいですか？

※やさしい口調で、カロリー目安も使いながら丁寧に判断してください。
"""
    return prompt.strip()

# --- メイン処理 ---
if api_key and user_question and st.session_state.last_question != user_question:
    if st.session_state.target_kcal is None:
        st.error("⚠️ 達成期限が過ぎています。未来の日付を選んでください。")
    else:
        with st.spinner("カロりんが考え中..."):
            try:
                prompt = build_prompt(
                    food_today,
                    exercise,
                    user_question,
                    st.session_state.target_kcal,
                    st.session_state.estimated_food_kcal
                )
                response = model.generate_content(prompt)
                answer = response.text.strip()
                st.session_state.chat_history.append({"role": "user", "content": user_question})
                st.session_state.chat_history.append({"role": "kalorin", "content": answer})
                st.session_state.last_question = user_question
            except Exception as e:
                st.error("エラー発生: " + str(e))

# --- チャット履歴の表示 ---
def show_chat():
    for chat in st.session_state.chat_history:
        role = chat["role"]
        msg = chat["content"]
        if role == "user":
            st.markdown(f'<div style="background-color:#DCF8C6;padding:10px;border-radius:10px;margin:5px 0;text-align:right">{msg}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div style="background-color:#FFF;padding:10px;border-radius:10px;margin:5px 0;border:1px solid #ccc;"><b>カロりん 🍓</b><br>{msg}</div>', unsafe_allow_html=True)

show_chat()

if not api_key:
    st.info("🔑 左のサイドバーで Gemini APIキーを入力してください。")
