import streamlit as st
import os
import openai
# from docopt import docopt
# from google.cloud import storage as gcs
import pandas as pd
#from io import BytesIO

openai.api_key =  st.secrets["openai_api_key"]
####################設定####################
item_dict = {"ヤクルト":"yakuruto","カヌレ":"kanure", "マリトッツォ":"maritotwo"} 
menu_dict = {"要望":"yobo","利点":"riten"} 

params = {
    'product':'', # 商品名
    'extract':'', # 抽出したい事項
    'tweets':'', # 抽出対象のツイート群
}

####################関数####################
##########prompt作成##########
def submit_prompt(prompt,use_chatGPT=True):
    
    print('--------------------送信したプロンプト----------------------')
    print(prompt)
    
    if use_chatGPT:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{
                "role": "user",
                "content":prompt,
            }],
            temperature=0,
            max_tokens=256,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
        answer = response["choices"][0]["message"]["content"]
        
    else:
        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=prompt,
            temperature=0,
            max_tokens=256,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
            )
        answer = response["choices"][0]['text']
    print('\n以下、回答\n')
    print(answer)
    print('\n','-'*50)
    return answer

def create_prompt(params):
    product = params['product']
    extract = params['extract']
    tweets = params['tweets']
    
    if extract == "商品名抽出":
        prompt = f"""
    以下の各々独立した文章群から、コンビニまたはセブンで取り扱いを希望されている商品の名前を各商品に言及した文章数, 理由とともに重複なく全て列挙せよ。
    ※ 商品名は文書間で表記揺れがあるため、表記揺れを直した上で一つに集約しなさい。
    ※ 理由は文章中に含まれない場合がある。その場合は「無し」としなさい。
    ※ 理由は短い文章で答えなさい。
    【文章群】
    {tweets}
    """
        st.session_state["question"] = ""
    else:
        if extract == "要望":
            #question = f'{product}に対して今はない特徴でこれから必要とする特徴'
            question = f'{product}に対してこれから改善してほしい要望'
        if extract == "利点":
            question = f'{product}の利点'
    #    if extract == "併買商品":
    #        question = f'{product}と併買される商品'
    #    if extract == "流行理由":
    #        question = f'{product}が流行している理由'
        st.session_state["question"] = question
        start_prompt = f"""
        以下のそれぞれ独立した文章群から、{question}を箇条書きで教えてください。
        ただし、全ての文章に{question}が記載されているとは限らないので、生成確信度が高い項目だけ列挙してください。
        """
        end_prompt = f'\n\n{question}：'
        prompt = start_prompt + tweets + end_prompt
    
    return prompt

def create_tag_prompt(answer):
    start_prompt = """
    次の2つの手順を踏まえて処理を行ってください。

    手順1: フレーズ群のうち、似たものをグルーピングしてください。(グルーピング結果が1フレーズのみのグループも出力してください)
    手順2: 手順1の結果をもとに、各グループのNRIタグを生成して箇条書きで出力してください。
           ただし、もし手順1でグルーピングができなかった場合は、フレーズ群に対してNRIタグを箇条書きで出力してください。

    NRIタグとは以下のように1単語で重要な特徴をまとめたものを意味します。

    ・「花粉症を抑える」、「花粉症対策に最適」、「花粉症防止」⇒花粉症対策
    ・「よく眠れる」、「睡眠の質向上」⇒睡眠改善
    
    #####フレーズ群#####
    """
    
    end_prompt = """
    #################
    
    各グループのNRIタグの箇条書き:
    
    """
    #prompt = f'以下のフレーズを、似たものをグルーピングして、さらにグループの特徴を教えてください。\n'+answer
    prompt = start_prompt + answer + end_prompt
    return prompt

def read_data(item,menu):
    item_name = item_dict[item]
    menu_name = menu_dict[menu]
    print(item_name)
    df = pd.read_csv(f"./data/{item_name}_{menu_name}_sample.csv")        
    return df["text"].to_list()


####################ページ作成####################

def main(): 
    st.title("Demo")
    st.write("メニューに合わせて、タグを生成します。")
    text_style = st.radio("入力テキストを選択してください。",("フリーテキスト", "ツイートサンプル"), horizontal=True)
    #text_style = st.radio("メニューに合わせて、タグを生成します。\n入力テキストを選択してください。", ("フリーテキスト", "ツイートサンプル"), horizontal=True)    
    if text_style == "フリーテキスト":
        free_text_area()
    elif text_style == "ツイートサンプル":
        sample_area()
    st.write("※入力テキストの説明※")    
    st.write("フリーテキスト:ご自身でメニューに合わせた文章を入力していただきます。")
    st.write("ツイートサンプル:ツイートサンプルを提示するので、メニューに合わせてツイートを選択していただきます。")

def free_text_area(): 
    menu = st.selectbox("メニューリスト", ("要望","利点","商品名抽出"))  
    #menu = st.selectbox("メニューリスト", ("要望","利点", "併買商品","流行理由"))
    with st.form("my_form", clear_on_submit=False):
        if menu == "商品名抽出":
            item = "" 
        else:
            item = st.text_input("商品名を入力してください。")
        text = st.text_area("テキストエリア")
        submitted = st.form_submit_button("Submit")
        if submitted:
            st.session_state["menu"] = menu
            st.session_state["text"] = text
            st.session_state["item"] = item
            change_page()
            
def sample_area(): 
    menu = st.selectbox("メニューリスト", ("要望","利点"))
    item = st.radio("商品を選択してください。",("ヤクルト", "カヌレ","マリトッツォ"), horizontal=True)
    text_list = read_data(item,menu)
    with st.form("my_form", clear_on_submit=False):
        st.write("以下のツイートサンプルから対象ツイートを選択してください。")
        all_text = ""
        for no,text in enumerate(text_list):
            check = st.checkbox(text)
            if check:
                all_text = all_text + text + "\n"     
        submitted = st.form_submit_button("Submit")
        if submitted:
            st.session_state["menu"] = menu
            st.session_state["item"] = item
            st.session_state["text"] = all_text
            change_page()           

def extract_results_page():

    params = {
        'product': st.session_state["item"], # 商品名
        'extract': st.session_state["menu"], # 抽出したい事項
        'tweets': st.session_state["text"] # 抽出対象のツイート群
    }
    #####各menu(要望・利点・商品名抽出)の結果出力#####
    prompt = create_prompt(params)
    answer = submit_prompt(prompt)
    st.session_state["answer"] = answer
    #####################画面出力####################
    if params['extract'] == "商品名抽出":
        st.header(params['extract'])
        text = f'商品名抽出の結果、コンビニまたはセブンで取り扱いを希望されている商品名と、言及ツイート数、商品化希望理由は以下の通りです。'
        st.write(text) 
        st.write("結果：")
        st.write(answer)
        st.write("入力ツイート:")
        st.markdown(params['tweets'].replace('\n','  \n'))
    
    else:
        #タグ生成
        tag_prompt = create_tag_prompt(answer)
        tag_answer = submit_prompt(tag_prompt) 
        #画面出力
        st.title("タグ生成結果")
        text = f'確定したタグは下記になります。'
        st.write(text) 
        st.write(tag_answer)
        st.header(params['extract'])
        text = f'{st.session_state["question"]}は下記になります。'
        st.write(text)
        st.write("結果：")
        st.write(answer)
        st.write("入力ツイート:")
        st.markdown(params['tweets'].replace('\n','  \n')) 
        #st.write("結果：")
        #st.write(answer)
    st.button("Home",on_click=back_page)
        #st.button("Create Tags",on_click=change_tag_page)

def tag_page():
    
    answer = st.session_state["answer"]
    prompt = create_tag_prompt(answer)
    tag_answer = submit_prompt(prompt)
    st.title("タグ生成結果")
    st.write("入力")
    st.write(answer)
    text = f'確定したタグは下記になります。'
    st.write(text) 
    st.write("結果：\n",tag_answer)    
    st.button("Home",on_click=back_page)   
    
             
####################ページ遷移のためのセッション情報####################          
#2ページ目に遷移           
def change_page():
    # ページ切り替えボタンコールバック
    st.session_state["page_control"]=1
#1ページ目に遷移     
def back_page():
    # ページ切り替えボタンコールバック
    st.session_state["page_control"]=0
#タグ生成ページ目に遷移     
def change_tag_page():
    # ページ切り替えボタンコールバック
    st.session_state["page_control"]=2

    
#########################ページ遷移コントロール########################### 
if ("page_control" in st.session_state and
   st.session_state["page_control"] == 1):
    extract_results_page()
elif  ("page_control" in st.session_state and
   st.session_state["page_control"] == 2):
    tag_page()   
else:
    st.session_state["page_control"] = 0
    main()
    
