# --- 核心生成邏輯 (加入呼吸停頓感) ---
async def generate_speech_with_progress(text_list, voice, rate_val, pitch_val, progress_bar, status_text):
    combined_audio = b""
    total = len(text_list)
    
    r = f"{rate_val:+d}%"
    p = f"{pitch_val:+d}%" if pitch_val != 0 else "+0Hz"
    
    for i, line in enumerate(text_list):
        if not line.strip():
            continue
            
        progress_bar.progress((i + 1) / total)
        status_text.text(f"⏳ 正在處理第 {i+1}/{total} 段文字...")
        
        # --- 這裡加入 SSML 包裝，讓每一行結尾都有呼吸感 ---
        # 加入 300ms 的停頓，聽起來會自然很多
        ssml_text = f"""
        <speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='zh-TW'>
            <voice name='{voice}'>
                <prosody rate='{r}' pitch='{p}'>
                    {line}
                    <break time='300ms' />
                </prosody>
            </voice>
        </speak>
        """
        
        # 使用 Communicate 直接傳入 SSML
        communicate = edge_tts.Communicate(ssml_text, voice) 
        # 注意：雖然傳入了 voice，但 SSML 內的 voice 設定權限更高
        
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                combined_audio += chunk["data"]
                
    return combined_audio
