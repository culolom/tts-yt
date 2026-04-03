import streamlit as st
import asyncio
import edge_tts
import io

# 1. 頁面配置
st.set_page_config(page_title="倉鼠語音實驗室", page_icon="🐹")

# --- 1. 密碼驗證功能 ---
def check_password():
    def password_entered():
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.title("🔐 倉鼠專屬工具箱")
        st.text_input("請輸入專屬密碼：", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.title("🔐 倉鼠專屬工具箱")
        st.text_input("密碼不正確，請再試一次：", type="password", on_change=password_entered, key="password")
        st.error("😕 密碼不對喔！")
        return False
    return True

# --- 2. 核心生成邏輯 (支援進度追蹤) ---
async def generate_speech_with_progress(text_list, voice, rate_val, pitch_val, progress_bar, status_text):
    combined_audio = b""
    total = len(text_list)
    
    # 格式化語速與音高
    r = f"{rate_val:+d}%"
    p = f"{pitch_val:+d}%" if pitch_val != 0 else "+0Hz"
    
    for i, line in enumerate(text_list):
        if not line.strip():
            continue
            
        # 更新進度條
        percent_complete = (i + 1) / total
        progress_bar.progress(percent_complete)
        status_text.text(f"⏳ 正在處理第 {i+1}/{total} 段文字...")
        
        # 生成該段語音
        communicate = edge_tts.Communicate(line, voice, rate=r, pitch=p)
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                combined_audio += chunk["data"]
                
    return combined_audio

# --- 3. 主程式介面 ---
if check_password():
    st.title("🐹 倉鼠語音實驗室")
    
    # --- 側邊欄設定 ---
    st.sidebar.header("🎙️ 聲音參數設定")
    VOICE_OPTIONS = {
        "曉臻 (女 - 溫柔/新聞)": "zh-TW-HsiaoChenNeural",
        "雲哲 (男 - 專業/Podcast)": "zh-TW-YunJheNeural",
        "曉雨 (女 - 輕快)": "zh-TW-HsiaoYuNeural",
    }
    selected_voice = VOICE_OPTIONS[st.sidebar.selectbox("選擇配音員", list(VOICE_OPTIONS.keys()))]
    rate = st.sidebar.slider("語速 (Rate)", -50, 50, 0, format="%d%%")
    pitch = st.sidebar.slider("音高 (Pitch)", -50, 50, 0, format="%d%%")
    
    if st.sidebar.button("登出"):
        st.session_state["password_correct"] = False
        st.rerun()

    # --- 主要輸入區 ---
    text_input = st.text_area("請輸入文案內容：", height=300, placeholder="建議按行分隔文案，進度條會更精準...")

    if st.button("🚀 開始生成語音", use_container_width=True):
        if not text_input.strip():
            st.error("請先輸入文字內容！")
        else:
            # 將文字按行拆分，並過濾掉空行
            text_lines = [line.strip() for line in text_input.split('\n') if line.strip()]
            
            # 建立進度條元件
            progress_bar = st.progress(0)
            status_text = st.empty() # 用來動態更新文字
            
            try:
                # 執行語音生成
                audio_bytes = asyncio.run(
                    generate_speech_with_progress(
                        text_lines, selected_voice, rate, pitch, progress_bar, status_text
                    )
                )
                
                # 完成後清除進度文字並顯示結果
                status_text.success("🎉 語音生成完成！")
                st.audio(audio_bytes, format="audio/mp3")
                st.download_button(
                    label="💾 下載 MP3 檔案",
                    data=audio_bytes,
                    file_name="hamster_voice.mp3",
                    mime="audio/mp3",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"發生錯誤：{str(e)}")
                progress_bar.empty()
                status_text.empty()

    st.markdown("---")
    st.info("💡 **小撇步**：\n- 文案建議 **一段話換一行**，這樣生成時進度條會動得最自然。")
