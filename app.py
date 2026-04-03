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

# --- 2. 核心生成邏輯 (標準安全版) ---
async def generate_speech_safe(text_list, voice, rate_val, pitch_val, progress_bar, status_text):
    combined_audio = b""
    total = len(text_list)
    
    # 格式化語速與音高
    r = f"{rate_val:+d}%"
    p = f"{pitch_val:+d}%" if pitch_val != 0 else "+0Hz"
    
    for i, line in enumerate(text_list):
        if not line.strip():
            continue
            
        progress_bar.progress((i + 1) / total)
        status_text.text(f"⏳ 正在處理第 {i+1}/{total} 段語音...")
        
        # 💡 去機器人感的關鍵：自動在每一行結尾加上「...」來強制 AI 停頓換氣
        processed_line = line.strip() + "..." 
        
        # 使用內建參數，絕對不會讀出代碼
        communicate = edge_tts.Communicate(processed_line, voice, rate=r, pitch=p)
        
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                combined_audio += chunk["data"]
                
    return combined_audio

# --- 3. 主程式介面 ---
if check_password():
    st.title("🐹 倉鼠語音實驗室")
    st.caption("已修復讀出代碼的錯誤，現在可以安心生成了。")

    # --- 側邊欄設定 ---
    st.sidebar.header("🎙️ 聲音參數設定")
    
    VOICE_OPTIONS = {
"雲哲 (男 - 台灣專業首選)": "zh-TW-YunJheNeural",
        "曉臻 (女 - 台灣溫柔說書)": "zh-TW-HsiaoChenNeural",
        "雲希 (男 - 深度說書感)": "zh-CN-YunxiNeural",
        "曉曉 (女 - 情感最豐富)": "zh-CN-XiaoxiaoNeural",
        "雲健 (男 - 沉穩導師感)": "zh-CN-YunjianNeural",
        "曉雨 (女 - 台灣活潑廣播)": "zh-TW-HsiaoYuNeural",
        "Jenny (英 - 專業國際感)": "en-US-JennyNeural",
    }
    
    selected_voice = VOICE_OPTIONS[st.sidebar.selectbox("選擇配音員", list(VOICE_OPTIONS.keys()))]
    
    # 推薦參數：語速稍慢更有質感
    rate = st.sidebar.slider("語速 (Rate)", -50, 50, -10, format="%d%%")
    pitch = st.sidebar.slider("音高 (Pitch)", -20, 20, 0, format="%d%%")
    
    st.sidebar.markdown("---")
    if st.sidebar.button("登出"):
        st.session_state["password_correct"] = False
        st.rerun()

    # --- 主要輸入區 ---
    text_input = st.text_area(
        "請輸入文案內容：", 
        height=300, 
        placeholder="把你的文案貼在這裡...\n每一行都會自動加上呼吸停頓。"
    )

    if st.button("🚀 開始生成語音", use_container_width=True):
        if not text_input.strip():
            st.error("請先輸入文字內容！")
        else:
            # 依行拆分
            text_lines = [l.strip() for l in text_input.split('\n') if l.strip()]
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                # 執行生成
                audio_bytes = asyncio.run(
                    generate_speech_safe(
                        text_lines, selected_voice, rate, pitch, progress_bar, status_text
                    )
                )
                
                if audio_bytes:
                    status_text.success(f"🎉 生成完成！")
                    st.audio(audio_bytes, format="audio/mp3")
                    
                    st.download_button(
                        label="💾 下載 MP3",
                        data=audio_bytes,
                        file_name="money_book_voice.mp3",
                        mime="audio/mp3",
                        use_container_width=True
                    )
            except Exception as e:
                st.error(f"錯誤：{str(e)}")
                progress_bar.empty()
                status_text.empty()

    st.markdown("---")
    st.info("💡 **倉鼠的去機器人感秘訣**：\n1. 推薦 **雲哲**，語速設為 **-10%** 到 **-15%**。\n2. 你的文案寫得很棒！在「你相信嗎？」後面多留一個空行，聽起來會更有懸念感。")
