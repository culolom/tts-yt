import streamlit as st
import asyncio
import edge_tts
import io

# 1. 頁面配置（必須是第一個 Streamlit 指令）
st.set_page_config(page_title="倉鼠語音實驗室", page_icon="🐹")

# --- 1. 密碼驗證功能 (使用 Secrets) ---
def check_password():
    """使用 Streamlit Secrets 進行密碼驗證"""
    def password_entered():
        # 從 st.secrets 中讀取名為 "password" 的設定
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # 驗證後刪除暫存密碼
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.title("🔐 倉鼠專屬工具箱")
        st.text_input("請輸入專屬密碼以解鎖工具：", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.title("🔐 倉鼠專屬工具箱")
        st.text_input("密碼不正確，請再試一次：", type="password", on_change=password_entered, key="password")
        st.error("😕 密碼不對喔，請檢查後再輸入。")
        return False
    else:
        return True

# --- 2. 語音生成核心邏輯 (已修正 pitch 錯誤) ---
async def generate_speech(text, voice, rate_val, pitch_val):
    # 格式化語速：使用 +d% 格式
    r = f"{rate_val:+d}%"
    
    # 修正：當 pitch 為 0 時，避免輸出 "+0%" 導致伺服器噴錯
    # 使用 "+0Hz" 是最穩定的相容寫法
    p = f"{pitch_val:+d}%" if pitch_val != 0 else "+0Hz"
    
    communicate = edge_tts.Communicate(text, voice, rate=r, pitch=p)
    
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return audio_data

# --- 3. 主程式介面 ---
if check_password():
    st.title("🐹 倉鼠語音實驗室")
    st.caption("輸入文案，一鍵轉換成 Podcast 或 YouTube 配音")

    # --- 側邊欄設定 ---
    st.sidebar.header("🎙️ 聲音參數設定")

    VOICE_OPTIONS = {
        "曉臻 (女 - 溫柔/新聞)": "zh-TW-HsiaoChenNeural",
        "雲哲 (男 - 專業/Podcast)": "zh-TW-YunJheNeural",
        "曉雨 (女 - 輕快)": "zh-TW-HsiaoYuNeural",
    }

    selected_voice_label = st.sidebar.selectbox("選擇配音員", list(VOICE_OPTIONS.keys()))
    selected_voice = VOICE_OPTIONS[selected_voice_label]

    # 設定滑桿
    rate = st.sidebar.slider("語速 (Rate)", -50, 50, 0, format="%d%%")
    pitch = st.sidebar.slider("音高 (Pitch)", -50, 50, 0, format="%d%%")
    
    st.sidebar.markdown("---")
    if st.sidebar.button("登出 / 重新鎖定"):
        st.session_state["password_correct"] = False
        st.rerun()

    # --- 主要輸入區 ---
    text_input = st.text_area("請輸入文案內容：", height=300, placeholder="在這裡貼上你的腳本...")

    if st.button("🚀 開始生成語音", use_container_width=True):
        if not text_input.strip():
            st.error("請先輸入一些文字喔！")
        else:
            with st.spinner("倉鼠正在努力配音中..."):
                try:
                    # 執行異步任務
                    audio_bytes = asyncio.run(generate_speech(text_input, selected_voice, rate, pitch))
                    
                    # 顯示播放器與下載按鈕
                    st.audio(audio_bytes, format="audio/mp3")
                    
                    st.download_button(
                        label="💾 下載 MP3 檔案",
                        data=audio_bytes,
                        file_name="hamster_voice.mp3",
                        mime="audio/mp3",
                        use_container_width=True
                    )
                    st.success("✅ 生成成功！")
                except Exception as e:
                    # 這裡會捕捉到所有異常，並顯示在介面上
                    st.error(f"發生錯誤：{str(e)}")

    # 底部提示區
    st.markdown("---")
    st.info("💡 **小撇步**：\n- **雲哲** 的聲音非常適合你的《鼠辣觀點》Podcast。\n- 如果覺得太機械感，可以嘗試將語速調成 **-5%**，聽起來會更自然。")
