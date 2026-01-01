import flet as ft
import threading
import time
import os
from pypdf import PdfReader
from voice import listener, speaker
from backend.core import app
from backend import rag_engine
from langchain_core.messages import HumanMessage

# --- CONFIGURATION ---
MIC_INDEX = 1  # <--- Set this to your correct mic index (0, 1, or 2)

def main(page: ft.Page):
    # --- WINDOW SETUP ---
    page.title = "JARVIS | Pro Neural Interface"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    page.window_width = 1000
    page.window_height = 700
    page.bgcolor = "black"

    # --- STATE ---
    state = {
        "running": False,
        "current_pdf": None
    }

    # --- PDF PROCESSING FUNCTION ---
    def process_pdf(e: ft.FilePickerResultEvent):
        if e.files:
            file_path = e.files[0].path
            filename = e.files[0].name
            
            # Update UI to show busy
            pdf_status.value = f"Reading {filename}..."
            pdf_status.color = "yellow"
            page.update()
            
            try:
                # 1. Read PDF
                reader = PdfReader(file_path)
                text = ""
                for page_obj in reader.pages:
                    text += page_obj.extract_text() or ""
                
                # 2. Ingest to Memory (Chunked)
                chunk_size = 1000
                chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
                
                # Clear old memory roughly (optional, or just add to it)
                # rag_engine.clear() # If you implemented clear method
                
                for chunk in chunks:
                    rag_engine.ingest_text(f"SOURCE_PDF: {filename} | CONTENT: {chunk}")
                
                state["current_pdf"] = filename
                pdf_status.value = f"✅ Learned: {filename}"
                pdf_status.color = "green"
                speaker.speak(f"I have read {filename}. You can ask me about it.")
                
            except Exception as ex:
                pdf_status.value = f"Error: {ex}"
                pdf_status.color = "red"
            
            page.update()

    # --- UI COMPONENTS ---
    
    # 1. File Picker (Invisible helper)
    file_picker = ft.FilePicker(on_result=process_pdf)
    page.overlay.append(file_picker)

    # 2. The Orb
    orb = ft.Container(
        width=180,
        height=180,
        border_radius=ft.border_radius.all(100),
        gradient=ft.RadialGradient(colors=["cyan", "blue900"]),
        shadow=ft.BoxShadow(spread_radius=15, blur_radius=60, color="cyan900"),
        animate_scale=ft.Animation(500, ft.AnimationCurve.EASE_OUT),
    )
    
    status_text = ft.Text("OFFLINE", size=18, weight="bold", color="grey")
    pdf_status = ft.Text("No PDF Loaded", size=12, color="grey")

    # 3. Chat Log
    chat_list = ft.ListView(expand=True, spacing=15, padding=20, auto_scroll=True)

    def add_bubble(sender, text):
        align = ft.MainAxisAlignment.END if sender == "You" else ft.MainAxisAlignment.START
        color = "blueGrey900" if sender == "You" else "cyan900"
        
        chat_list.controls.append(
            ft.Row([
                ft.Container(
                    content=ft.Text(text, size=15, color="white"),
                    padding=15,
                    border_radius=15,
                    bgcolor=color,
                    width=450 if len(text) > 60 else None
                )
            ], alignment=align)
        )
        page.update()

    # --- VOICE LOOP (Background Brain) ---
    def run_voice_loop():
        # Clean start
        speaker.speak("Online.")
        
        while state["running"]:
            try:
                # 1. LISTEN
                update_status("LISTENING", "cyan")
                user_text = listener.listen(mic_index=MIC_INDEX)
                
                if user_text:
                    add_bubble("You", user_text)
                    
                    if "exit" in user_text.lower():
                        state["running"] = False
                        speaker.speak("Goodbye.")
                        page.window_close()
                        break
                    
                    # 2. THINK
                    update_status("PROCESSING", "purple")
                    
                    # Construct Prompt with PDF Awareness
                    prompt = user_text
                    if state["current_pdf"]:
                         # If PDF loaded, prompt the AI to look at memory
                         prompt = f"Context: I uploaded {state['current_pdf']}. Question: {user_text}"

                    result = app.invoke(
                        {"messages": [HumanMessage(content=prompt)]}, 
                        config={"configurable": {"thread_id": "Desktop-Pro"}}
                    )
                    ai_reply = result['messages'][-1].content
                    
                    # 3. SPEAK
                    add_bubble("AI", ai_reply)
                    update_status("SPEAKING", "green")
                    speaker.speak(ai_reply)
                
                else:
                    # Silence
                    update_status("IDLE", "grey")
                    time.sleep(0.1)

            except Exception as e:
                print(e)
                update_status("ERROR", "red")

        update_status("OFFLINE", "grey")

    def update_status(text, color):
        orb.scale = 1.2 if text == "LISTENING" else (0.9 if text == "PROCESSING" else 1.0)
        
        if color == "cyan":
            orb.gradient.colors = ["cyanAccent", "blue900"]
            orb.shadow.color = "cyan"
        elif color == "purple":
            orb.gradient.colors = ["purpleAccent", "deepPurple900"]
            orb.shadow.color = "purple"
        elif color == "green":
            orb.gradient.colors = ["greenAccent", "green900"]
            orb.shadow.color = "green"
        else:
            orb.gradient.colors = ["blueGrey700", "black"]
            orb.shadow.color = "black"
            
        status_text.value = text
        status_text.color = color
        page.update()

    # --- CONTROLS ---
    def toggle_system(e):
        if not state["running"]:
            state["running"] = True
            btn_start.text = "STOP SYSTEM"
            btn_start.bgcolor = "red900"
            threading.Thread(target=run_voice_loop, daemon=True).start()
        else:
            state["running"] = False
            btn_start.text = "START SYSTEM"
            btn_start.bgcolor = "green900"
            update_status("IDLE", "grey")
        page.update()

    def upload_click(e):
        file_picker.pick_files(allow_multiple=False, allowed_extensions=["pdf"])

    # --- LAYOUT ---
    btn_start = ft.ElevatedButton("START SYSTEM", bgcolor="green900", color="white", height=50, width=200, on_click=toggle_system)
    btn_upload = ft.ElevatedButton("UPLOAD PDF", bgcolor="blue900", color="white", height=40, width=200, on_click=upload_click)

    left_panel = ft.Container(
        width=350, bgcolor="blueGrey900", padding=30,
        content=ft.Column([
            ft.Container(height=40),
            ft.Container(content=orb, alignment=ft.alignment.center),
            ft.Container(height=30),
            ft.Container(content=status_text, alignment=ft.alignment.center),
            ft.Container(height=80),
            ft.Container(content=btn_start, alignment=ft.alignment.center),
            ft.Container(height=20),
            ft.Container(content=btn_upload, alignment=ft.alignment.center),
            ft.Container(height=10),
            ft.Container(content=pdf_status, alignment=ft.alignment.center),
        ], horizontal_alignment="center")
    )

    right_panel = ft.Container(
        expand=True, padding=20,
        content=ft.Column([
            ft.Text("LIVE CONVERSATION", size=20, weight="bold", color="cyan100"),
            ft.Divider(color="blueGrey800"),
            chat_list
        ])
    )

    page.add(ft.Row([left_panel, right_panel], expand=True, spacing=0))

if __name__ == "__main__":
    ft.app(target=main)