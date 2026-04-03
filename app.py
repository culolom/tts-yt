import streamlit as st
import asyncio
import edge_tts
import io

# 設定頁面標題
st.set_page_config(page_title="倉鼠語音實驗室", page_icon="🐹")

st.title("🐹 倉鼠語音實驗室")
st.caption("輸入文案，一鍵轉換成 Podcast 或 YouTube 配音")

# --- 側邊欄設定 ---
st.sidebar.header("設定參數")

# 整理出台灣常用的優質聲音
VOICE_OPTIONS = {
    "曉臻 (女 - 溫柔/新聞)": "zh-TW-HsiaoChenNeural",
    "雲哲 (男 - 專業/Podcast)": "zh-TW-YunJheNeural",
    "曉雨 (女 - 輕快)": "zh-TW-HsiaoYuNeural",
}

selected_voice_label = st.sidebar.selectbox("選擇配音員", list(VOICE_OPTIONS.keys()))
selected_voice = VOICE_OPTIONS[selected_voice_label]

rate = st.sidebar.slider("語速 (Rate)", -50, 50, 0, format="%d%%")
pitch = st.sidebar.slider("音高 (Pitch)", -50, 50, 0, format="%d%%")

# --- 主要介面 ---
text_input = st.text_area("請輸入文案內容：", height=300, placeholder="在這裡貼上你的腳本...")

# 轉換邏輯
async def generate_speech(text, voice, rate_val, pitch_val):
    # 格式化語速與音高 (例如: +0%, -10%)
    r = f"{rate_val:+d}%"
    p = f"{pitch_val:+d}%"
    
    communicate = edge_tts.Communicate(text, voice, rate=r, pitch=p)
    
    # 使用 BytesIO 在記憶體中處理檔案
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return audio_data

if st.button("🚀 開始生成語音", use_container_width=True):
    if not text_input.strip():
        st.error("請先輸入一些文字喔！")
    else:
        with st.spinner("倉鼠正在努力配音中..."):
            try:
                # 執行異步任務
                audio_bytes = asyncio.run(generate_speech(text_input, selected_voice, rate, pitch))
                
                # 顯示音軌播放器
                st.audio(audio_bytes, format="audio/mp3")
                
                # 提供下載按鈕
                st.download_button(
                    label="💾 下載 MP3 檔案",
                    data=audio_bytes,
                    file_name="hamster_voice.mp3",
                    mime="audio/mp3",
                    use_container_width=True
                )
                st.success("✅ 生成成功！")
            except Exception as e:
                st.error(f"發生錯誤：{e}")

# 底部小撇步
st.markdown("---")
st.info("💡 **小撇步**：\n- **雲哲** 的聲音非常適合你的《鼠辣觀點》Podcast。\n- 如果覺得太機械感，可以嘗試將語速調成 **-5%**，聽起來會更自然。")
