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

# --- 2. 核心生成邏輯 (支援精確停頓秒數) ---
async def generate_speech_with_pause(text_list, voice, rate_val, pitch_val, pause_seconds, progress_bar, status_text):
    combined_audio = b""
    total = len(text_list)
    
    # 格式化語速與音高
    r = f"{rate_val:+d}%"
    p = f"{pitch_val:+d}%" if pitch_val != 0 else "+0Hz"
    
    # 將秒轉換為毫秒 (ms)
    pause_ms = int(pause_seconds * 1000)
    
    for i, line in enumerate(text_list):
        if not line.strip():
            continue
            
        progress_bar.progress((i + 1) / total)
        status_text.text(f"⏳ 正在處理第 {i+1}/{total} 段語音...")
        
        # 使用極簡 SSML 確保不被誤讀，同時注入停頓
        # break time 指令會讓 AI 在這段文字讀完後安靜指定的時間
        ssml = (
            f"<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='zh-TW'>"
            f"<voice name='{voice}'>"
            f"<prosody rate='{r}' pitch='{p}'>"
            f"{line.strip()}"
            f"</prosody>"
            f"<break time='{pause_ms}ms' />"
            f"</voice>"
            f"</speak>"
        )
        
        communicate = edge_tts.Communicate(ssml, voice)
        
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                combined_audio += chunk["data"]
                
    return combined_audio

# --- 3. 主程式介面 ---
if check_password():
    st.title("🐹 倉鼠語音實驗室")
    st.caption("現在你可以自由調整每一行文案之間的空白時間了。")

    # --- 側邊欄設定 ---
    st.sidebar.header("🎙️ 聲音參數設定")
    
    VOICE_OPTIONS = {
        "雲哲 (男 - 專業 Podcast)": "zh-TW-YunJheNeural",
        "曉臻 (女 - 溫柔新聞)": "zh-TW-HsiaoChenNeural",
        "曉雨 (女 - 活潑輕快)": "zh-TW-HsiaoYuNeural",
    }
    
    selected_voice = VOICE_OPTIONS[st.sidebar.selectbox("選擇配音員", list(VOICE_OPTIONS.keys()))]
    
    # 參數滑桿
    rate = st.sidebar.slider("語速 (Rate)", -50, 50, -10, format="%d%%")
    pitch = st.sidebar.slider("音高 (Pitch)", -20, 20, 0, format="%d%%")
    
    # ✨ 新功能：行間停頓滑桿
    pause_duration = st.sidebar.slider(
        "行間停頓 (秒)", 
        min_value=0.0, 
        max_value=5.0, 
        value=0.8, 
        step=0.1,
        help="每一行結束後，AI 會安靜多久再讀下一行。推薦 0.5s - 1.2s。"
    )
    
    st.sidebar.markdown("---")
    if st.sidebar.button("登出系統"):
        st.session_state["password_correct"] = False
        st.rerun()

    # --- 主要輸入區 ---
    text_input = st.text_area(
        "請輸入文案內容：", 
        height=300, 
        placeholder="文案範例：\n第一行（停頓）\n第二行（停頓）..."
    )

    if st.button("🚀 開始生成語音", use_container_width=True):
        if not text_input.strip():
            st.error("請先輸入文字內容！")
        else:
            # 依換行拆分
            text_lines = [l.strip() for l in text_input.split('\n') if l.strip()]
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                # 執行生成
                audio_bytes = asyncio.run(
                    generate_speech_with_pause(
                        text_lines, selected_voice, rate, pitch, pause_duration, progress_bar, status_text
                    )
                )
                
                if audio_bytes:
                    status_text.success(f"🎉 生成完成！")
                    st.audio(audio_bytes, format="audio/mp3")
                    
                    st.download_button(
                        label="💾 下載成品 MP3",
                        data=audio_bytes,
                        file_name="hamster_podcast.mp3",
                        mime="audio/mp3",
                        use_container_width=True
                    )
            except Exception as e:
                st.error(f"錯誤：{str(e)}")
                progress_bar.empty()
                status_text.empty()

    st.markdown("---")
    st.info("💡 **倉鼠指南**：\n- **0.5s**：節奏緊湊，適合短影音。\n- **0.8s - 1.2s**：最自然的說話節奏，適合 Podcast。\n- **2.0s+**：適合需要給觀眾思考時間的深刻金句。")
