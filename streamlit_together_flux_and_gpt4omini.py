import streamlit as st
import requests
from PIL import Image
from io import BytesIO
import json
import time

# OpenAI API 功能
def connectGPT(openai_model, system_prompt, user_prompt, temperature):
    openai_api_key = st.secrets["openai_api_key"]
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {openai_api_key}"
    }
    url = "https://api.openai.com/v1/chat/completions"

    data = {
        "model": openai_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": temperature
    }
    start_time = time.time()
    response = requests.post(url, headers=headers, data=json.dumps(data))
    end_time = time.time()
    response_data = response.json()
    response_content = response_data['choices'][0]['message']['content']
    
    # Calculate spent time
    spent_time = end_time - start_time
    
    return response_content, response_data['usage']['prompt_tokens'], response_data['usage']['completion_tokens'], spent_time

# 圖像生成功能
def generate_image(prompt, api_key, width, height, steps):
    url = "https://api.together.xyz/v1/images/generations"
    payload = {
        "prompt": prompt,
        "model": "black-forest-labs/FLUX.1-schnell-Free",
        "steps": steps,
        "n": 1,
        "height": height,
        "width": width
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Bearer {api_key}"
    }

    response = requests.post(url, json=payload, headers=headers)
    return response

# Streamlit 頁面配置
st.set_page_config(page_title="AI 圖像生成器", layout="wide")
st.title("AI 圖像生成器")

# 從 Streamlit Secrets 取得 API 金鑰
api_key = st.secrets["together_api_key"]

# 使用者輸入
coll1, coll2 = st.columns([2, 1])
with coll1:
    user_input = st.text_input("輸入您的描述", "貓咪漂浮在太空中，太空中寫著'YES'，電影風格")

# 新增選項讓用戶選擇處理方式
with coll2:
    process_option = st.radio(
        "字句後製處理的方式",
        ("轉換為適合圖片的 prompt", "單純翻譯成英文")
    )

# 參數調整
col1, col2, col3 = st.columns(3)
with col1:
    width = st.slider("圖像寬度", min_value=256, max_value=1440, value=1024, step=64)
with col2:
    height = st.slider("圖像高度", min_value=256, max_value=1440, value=1024, step=64)
with col3:
    steps = st.slider("生成步數", min_value=1, max_value=4, value=4)

# 生成按鈕
if st.button("處理並生成圖像", use_container_width=True, icon="😃", type="secondary"):
    # 根據用戶選擇設置 system prompt
    if process_option == "轉換為適合圖片的 prompt":
        system_prompt = "You are a helpful assistant that translates Chinese image descriptions into detailed English prompts suitable for image generation. Enhance the description with additional details that would make the image more vivid and interesting."
    else:
        system_prompt = "You are a helpful assistant that accurately translates Chinese text into English. Provide a direct and precise translation without adding extra details or embellishments."

    openai_model = "gpt-4o-mini"
    temperature = 0.7

    with st.spinner("正在處理文本..."):
        english_prompt, prompt_tokens, completion_tokens, processing_time = connectGPT(openai_model, system_prompt, user_input, temperature)

    st.write(f"處理後的英文文本：{english_prompt}")
    st.write(f"處理耗時：{processing_time:.2f} 秒")

    # 生成圖片
    with st.spinner("正在生成圖像..."):
        response = generate_image(english_prompt, api_key, width, height, steps)

    if response.status_code == 200:
        data = response.json()
        if 'data' in data and len(data['data']) > 0 and 'url' in data['data'][0]:
            image_url = data['data'][0]['url']
            
            # 下載並顯示圖像
            image_response = requests.get(image_url)
            if image_response.status_code == 200:
                image = Image.open(BytesIO(image_response.content))
                st.image(image, caption="生成的圖像", use_column_width=True)
            else:
                st.error("無法下載圖像")
        else:
            st.error("API 回應中未找到圖像 URL")
    else:
        st.error(f"API 請求失敗。狀態碼: {response.status_code}")
        st.error(f"錯誤訊息: {response.text}")

# 新增使用說明
st.markdown("""
## 使用說明
1. 在文字框中輸入您想要處理的文本描述（可以使用中文）。
2. 選擇處理方式：
   - "轉換為適合圖片的 prompt"：將描述轉換為更詳細的英文圖像生成提示。
   - "單純翻譯成英文"：直接將中文翻譯成英文，不添加額外細節。
3. 使用滑桿調整圖像的寬度和高度（256 到 1440 像素）。
4. 選擇生成步數（1 到 4 步）。
5. 點擊「處理並生成圖像」按鈕。
6. 系統會先處理您的文字描述，然後顯示處理後的英文文本。
7. 系統會使用處理後的文本來生成圖像，完成後會顯示在頁面上。

注意：
- 較大的圖像尺寸可能會增加生成時間。
- 生成步數越多，圖像品質可能會更好，但也會增加生成時間。
- 選擇"轉換為適合圖片的 prompt"可能會產生更詳細、更有創意的圖像。
- 選擇"單純翻譯成英文"會產生更直接、更接近原始描述的圖像。
""")
