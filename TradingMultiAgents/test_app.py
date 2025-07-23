import streamlit as st

st.title("Streamlit テストアプリ")
st.write("これはテスト用のシンプルなStreamlitアプリです。")
st.write("正常に動作しています！")

if st.button("クリックしてテスト"):
    st.success("ボタンが正常に動作しました！")