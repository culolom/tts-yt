import streamlit as st
import asyncio
import edge_tts
import io

# 1. 必須是 Streamlit 的第一個指令
st.set_page_config(page_title="倉鼠語音實驗室", page_icon="🐹")

# --- 密碼驗證功能 ---
def check_password():
    """如果密碼正確則返回 True，否則顯示輸入框。"""
    def password_entered():
        # 將密碼改為你想設定的字串
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # 驗證後刪除暫存密碼避免洩露
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # 第一次進入頁面
        st.title("🔐 倉鼠專屬工具箱")
        st.text_input("請輸入專屬密碼以解鎖工具：", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        # 密碼輸入錯誤
        st.title("🔐 倉鼠專屬工具箱")
        st.text_input("密碼不正確，請再試一次：", type="password", on_change=password_entered, key="password")
        st.error("😕 密碼不對喔，請檢查後再輸入。")
        return False
    else:
        # 密碼正確
        return True

# --- 語音生成核心邏輯 ---
async def generate_speech(text, voice, rate_val, pitch_val):
    # 格式化語速與音高 (例如: +0%, -10%)
    r = f"{rate_val:+d}%"
    p = f"{pitch_val:+d}%"
    
    communicate = edge_tts.Communicate(text, voice, rate=r, pitch=p)
    
    # 使用 BytesIO 在記憶體中處理檔案，避免產生實體暫存檔
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return audio_data

# --- 主程式進入點 ---
if check_password():
    # 密碼通過後才顯示的內容
    st.title("🐹 倉鼠語音實驗室")
    st.caption("輸入文案，一鍵轉換成 Podcast 或 YouTube 配音")

    # --- 側邊欄設定 ---
    st.sidebar.header("🎙️ 聲音參數設定")

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
    
    st.sidebar.markdown("---")
    if st.sidebar.button("登出 / 重新鎖定"):
        st.session_state["password_correct"] = False
        st.rerun()

    # --- 主要介面 ---
    text_input = st.text_area("請輸入文案內容：", height=300, placeholder="在這裡貼上你的腳本...")

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

    # 底部提示
    st.markdown("---")
    st.info("💡 **小撇步**：\n- **雲哲** 的聲音非常適合你的《鼠辣觀點》Podcast。\n- 如果覺得太機械感，可以嘗試將語速調成 **-5%**，聽起來會更自然。")
