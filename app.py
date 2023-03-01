import streamlit as st
import os
import openai
# from docopt import docopt
# from google.cloud import storage as gcs
import pandas as pd
#from io import BytesIO

openai.api_key = st.secrets["openai_api_key"]

params = {
    'product':'', # 商品名
    'extract':'', # 抽出したい事項
    'tweets':'', # 抽出対象のツイート群
}

def submit_prompt(params):
    product = params['product']
    extract = params['extract']
    tweets = params['tweets']
    
    if extract == "要望":
        question = f'{product}に対して求めていること'
    if extract == "利点":
        question = f'{product}の利点'
    if extract == "併買商品":
        question = f'{product}と併買される商品'
    
    start_prompt = f'以下の文章から、{question}を箇条書きで教えてください。\n'
    end_prompt = f'\n\n{question}：'
    prompt = start_prompt + tweets + end_prompt
    print(prompt)
    
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=prompt,
        temperature=0.4,
        max_tokens=256,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
            )
    answer = response["choices"][0]['text']
    return answer

        
def main(): 
    with st.form("my_form", clear_on_submit=False):
        st.title("Demo")
        menu = st.selectbox("メニューリスト", ("要望","利点", "併買商品"))  
        item = st.text_input("商品名を入力してください。") 
        text = st.text_area("テキストエリア")
        submitted = st.form_submit_button("Submit")
        if submitted:
            st.session_state["menu"] = menu
            st.session_state["item"] = item
            st.session_state["text"] = text
            change_page()
            
            
def change_page():
    # ページ切り替えボタンコールバック
    st.session_state["page_control"]=1
    
def back_page():
    # ページ切り替えボタンコールバック
    st.session_state["page_control"]=0

def next_page():

    params = {
        'product': st.session_state["item"], # 商品名
        'extract': st.session_state["menu"], # 抽出したい事項
        'tweets': st.session_state["text"], # 抽出対象のツイート群
    }
    answer = submit_prompt(params)
    st.title(params['extract'])
    st.write(answer)   
    submitted = st.button("Back",on_click=back_page)

# 状態保持する変数を作成して確認
if ("page_control" in st.session_state and
   st.session_state["page_control"] == 1):
    next_page()
else:
    st.session_state["page_control"] = 0
    main()
    
