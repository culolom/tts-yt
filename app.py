import streamlit as st
import asyncio
import edge_tts
import io
import re

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

# --- 2. 核心生成邏輯 (SSML 注入版) ---
async def generate_speech_with_ssml(text_list, voice, rate_val, pitch_val, pause_ms, progress_bar, status_text):
    combined_audio = b""
    total = len(text_list)
    
    # 格式化語速與音高
    r = f"{rate_val:+d}%"
    p = f"{pitch_val:+d}%" if pitch_val != 0 else "+0Hz"
    
    for i, line in enumerate(text_list):
        if not line.strip():
            continue
            
        progress_bar.progress((i + 1) / total)
        status_text.text(f"⏳ 正在調教第 {i+1}/{total} 段語氣...")
        
        # 使用 SSML 注入停頓與語調控制
        # 我們將每一行包裝成一個獨立的語音片段，並在結尾加上強制停頓
        ssml_content = f"""
        <speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='zh-TW'>
            <voice name='{voice}'>
                <prosody rate='{r}' pitch='{p}'>
                    {line}
                </prosody>
                <break time='{pause_ms}ms' />
            </voice>
        </speak>
        """
        
        try:
            communicate = edge_tts.Communicate(ssml_content, voice)
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    combined_audio += chunk["data"]
        except Exception as e:
            st.warning(f"第 {i+1} 段生成失敗，已跳過。錯誤：{e}")
                
    return combined_audio

# --- 3. 主程式介面 ---
if check_password():
    st.title("🐹 倉鼠語音實驗室 `V3`")
    st.caption("透過 SSML 注入呼吸感，讓 AI 聽起來更像真人。")

    # --- 側邊欄設定 ---
    st.sidebar.header("🎙️ 語音美化參數")
    
    VOICE_OPTIONS = {
        "雲哲 (男 - 專業 Podcast)": "zh-TW-YunJheNeural",
        "曉臻 (女 - 溫柔新聞)": "zh-TW-HsiaoChenNeural",
        "曉雨 (女 - 活潑輕快)": "zh-TW-HsiaoYuNeural",
    }
    
    selected_voice = VOICE_OPTIONS[st.sidebar.selectbox("選擇配音員", list(VOICE_OPTIONS.keys()))]
    
    # 調速與音高
    rate = st.sidebar.slider("語速 (Rate)", -50, 50, -10, format="%d%%", help="建議調低至 -10% 會更沉穩。")
    pitch = st.sidebar.slider("音高 (Pitch)", -20, 20, 0, format="%d%%")
    
    # 呼吸感控制
    pause_ms = st.sidebar.slider("段落停頓 (ms)", 0, 2000, 500, step=100, help="每一行結束後的停頓時間，500ms = 0.5秒。")
    
    st.sidebar.markdown("---")
    if st.sidebar.button("登出系統"):
        st.session_state["password_correct"] = False
        st.rerun()

    # --- 主要輸入區 ---
    text_input = st.text_area(
        "請輸入文案內容：", 
        height=300, 
        placeholder="小提醒：\n1. 每一個『換行』都會觸發上面設定的停頓時間。\n2. 善用『，』和『。』能讓 AI 自動調整語氣。"
    )

    if st.button("🚀 開始注入靈魂生成語音", use_container_width=True):
        if not text_input.strip():
            st.error("請先輸入文字內容！")
        else:
            # 預處理：過濾掉空行
            text_lines = [l.strip() for l in text_input.split('\n') if l.strip()]
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                # 執行帶有 SSML 的語音生成
                audio_bytes = asyncio.run(
                    generate_speech_with_ssml(
                        text_lines, selected_voice, rate, pitch, pause_ms, progress_bar, status_text
                    )
                )
                
                if audio_bytes:
                    status_text.success(f"🎉 生成完成！總長度約 {len(audio_bytes)//1024} KB")
                    st.audio(audio_bytes, format="audio/mp3")
                    
                    st.download_button(
                        label="💾 下載成品 MP3",
                        data=audio_bytes,
                        file_name="hamster_pro_voice.mp3",
                        mime="audio/mp3",
                        use_container_width=True
                    )
            except Exception as e:
                st.error(f"系統崩潰：{str(e)}")
                progress_bar.empty()
                status_text.empty()

    # 底部攻略
    st.markdown("---")
    with st.expander("🎨 如何讓語音更自然？（倉鼠心得）"):
        st.markdown("""
        * **文字加料**：遇到想強調的地方，可以加個空格或換行。
        * **標點符號**：AI 看到『？』會自動上揚，看到『...』會略微沉思。
        * **雲哲專屬**：將語速調至 **-15%**，停頓設為 **800ms**，非常適合《鼠辣觀點》那種深夜 Podcast 感。
        * **終極招式**：生成後，在剪輯軟體放上一段 **Lofi 背景音樂**，機器味會瞬間消失 80%！
        """)
