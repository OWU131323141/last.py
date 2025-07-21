import streamlit as st
import google.generativeai as genai
import datetime

# --- APIキー入力 ---
api_key = st.sidebar.text_input("🔑 Gemini APIキーを入力", type="password")
if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.0-flash-lite")

# --- タイトル・UI ---
st.title("🧡 カロりんに聞いてみよう")
st.write("栄養士AI『カロりん』があなたの食事判断をお手伝いします😊")

# --- サイドバー：ユーザー情報 ---
st.sidebar.header("📋 あなたの情報")
weight = st.sidebar.number_input("現在の体重 (kg)", 30, 150, 60)
goal_weight = st.sidebar.number_input("目標体重 (kg)", 30, 150, 55)

# 改善③：過去の日付を選ばせないよう制限
min_date = datetime.date.today() + datetime.timedelta(days=1)
deadline = st.sidebar.date_input("目標達成期限", value=min_date + datetime.timedelta(weeks=8), min_value=min_date)

exercise = st.sidebar.selectbox("今日の運動量", ["少ない", "普通", "多い"])
food_today = st.sidebar.text_area("🍱 今日食べたもの", placeholder="朝：トーストと卵、昼：ラーメン、夜：唐揚げ定食")

# --- 入力欄：今食べたいもの ---
user_question = st.text_input("🍩 今食べたいものをカロりんに相談しよう")

# --- セッションチャット履歴 ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- チャット履歴のリセットボタン（改善⑤） ---
if st.button("🧹 チャット履歴をリセット"):
    st.session_state.chat_history = []
    st.experimental_rerun()

# --- チャットUI表示関数 ---
def show_chat():
    for chat in st.session_state.chat_history:
        role = chat["role"]
        msg = chat["content"]
        if role == "user":
            st.markdown(f'<div style="background-color:#DCF8C6;padding:10px;border-radius:10px;margin:5px 0;text-align:right">{msg}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div style="background-color:#FFF;padding:10px;border-radius:10px;margin:5px 0;border:1px solid #ccc;"><b>カロりん 🍓</b><br>{msg}</div>', unsafe_allow_html=True)

# --- 摂取目標カロリーの計算 ---
def calculate_target_calories(weight, goal_weight, deadline):
    days = (deadline - datetime.date.today()).days
    if days <= 0:
        return None
    diff_kg = weight - goal_weight
    kcal_per_kg = 7200  # 体脂肪1kgあたりのカロリー
    total_kcal_to_lose = diff_kg * kcal_per_kg
    daily_kcal_deficit = total_kcal_to_lose / days
    estimated_maintenance = weight * 30
    target_kcal = estimated_maintenance - daily_kcal_deficit
    return round(target_kcal)

# --- 改善①：運動量に応じた調整 ---
def adjust_for_exercise(base_kcal, exercise_level):
    adjustment = {"少ない": -100, "普通": 0, "多い": +150}
    return base_kcal + adjustment.get(exercise_level, 0)

# --- Gemini用プロンプト作成 ---
def build_prompt(food_today, exercise, user_question, target_kcal):
    prompt = f"""
あなたはやさしく親しみやすい栄養士AI「カロりん」です。
以下の内容から、ユーザーが今食べたいものを食べても良いかを判断してください。

# 今日食べたもの:
{food_today}

# 今日の運動量:
{exercise}

# 目標摂取カロリー（1日）:
{target_kcal} kcal

# 質問:
「{user_question}」を今食べてもいいですか？

以下のことを守ってください:
・推定される摂取カロリーをカロりんが予測
・目標カロリーと比較して判断
・理由も添えて、やさしくて親しみやすい口調で答えてください
・食べてもいい場合：「〜してみてね♪」など
・控えた方がいい場合：「代わりに〇〇はどう？」など
"""
    return prompt.strip()

# --- メイン実行 ---
if api_key and user_question:
    st.session_state.chat_history.append({"role": "user", "content": user_question})

    target_kcal = calculate_target_calories(weight, goal_weight, deadline)
    if target_kcal is None:
        st.error("⚠️ 達成期限が過ぎています。未来の日付を選んでください。")
    else:
        # 改善①：運動量を反映したカロリーに補正
        target_kcal = adjust_for_exercise(target_kcal, exercise)

        # 改善④：目標カロリーのサイドバー表示
        st.sidebar.markdown(f"🔵 **目標摂取カロリー**: {target_kcal} kcal")

        with st.spinner("カロりんが考え中..."):
            try:
                prompt = build_prompt(food_today, exercise, user_question, target_kcal)

                if st.sidebar.checkbox("🛠 プロンプトを表示", value=False):
                    st.write("🔍 送信プロンプト：", prompt)

                response = model.generate_content(prompt)

                if st.sidebar.checkbox("🛠 Geminiの返答を表示", value=False):
                    st.write("✅ Geminiの返答：", response)

                answer = response.text.strip()
                st.session_state.chat_history.append({"role": "kalorin", "content": answer})

                st.experimental_rerun()  # ✅ 成功時だけ再読み込み

            except Exception as e:
                st.error("エラー発生: " + str(e))  # ❌ rerunしない（これが重要）

# --- チャット表示 ---
show_chat()

if not api_key:
    st.info("🔑 左のサイドバーで Gemini APIキーを入力してください。")
