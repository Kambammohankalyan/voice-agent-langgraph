import flet as ft
import threading
import time
from voice import listener, speaker
from backend.core import app
from langchain_core.messages import HumanMessage

# --- CONFIGURATION ---
MIC_INDEX = 1  # <--- ENSURE THIS MATCHES YOUR MIC ID

def main(page: ft.Page):
    # --- PAGE SETUP ---
    page.title = "JARVIS | Neural Interface"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20
    page.window_width = 1000
    page.window_height = 700
    page.bgcolor = ft.Colors.BLACK

    # --- STATE VARIABLES ---
    state = {"running": False}

    # --- UI COMPONENTS ---
    
    # 1. THE ORB (Animated Core)
    orb = ft.Container(
        width=150,
        height=150,
        border_radius=ft.BorderRadius.all(100),
        gradient=ft.RadialGradient(
            colors=[ft.Colors.CYAN_ACCENT, ft.Colors.BLUE_900],
        ),
        shadow=ft.BoxShadow(
            spread_radius=10,
            blur_radius=50,
            color=ft.Colors.CYAN_900,
        ),
        animate_scale=ft.Animation(600, ft.AnimationCurve.BOUNCE_OUT),
        animate_opacity=300,
    )

    orb_status = ft.Text("OFFLINE", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_500)

    # 2. CHAT LOG (Scrollable)
    chat_list = ft.ListView(
        expand=True,
        spacing=10,
        padding=20,
        auto_scroll=True,
    )

    # 3. CHAT BUBBLE BUILDER
    def create_bubble(sender, text):
        align = ft.MainAxisAlignment.END if sender == "You" else ft.MainAxisAlignment.START
        bg_color = ft.Colors.BLUE_GREY_900 if sender == "You" else ft.Colors.CYAN_900
        
        return ft.Row(
            [
                ft.Container(
                    content=ft.Text(text, size=15, color=ft.Colors.WHITE),
                    padding=15,
                    border_radius=ft.BorderRadius.all(15),
                    bgcolor=bg_color,
                    width=400 if len(text) > 50 else None, 
                )
            ],
            alignment=align,
        )

    # --- ANIMATION CONTROLLER ---
    def set_status(mode):
        if mode == "LISTENING":
            orb.scale = 1.2 
            orb.gradient.colors = [ft.Colors.CYAN_ACCENT, ft.Colors.BLUE_900]
            orb.shadow.color = ft.Colors.CYAN_500
            orb_status.value = "LISTENING..."
            orb_status.color = ft.Colors.CYAN_ACCENT
        
        elif mode == "THINKING":
            orb.scale = 0.9 
            orb.gradient.colors = [ft.Colors.PURPLE_ACCENT, ft.Colors.DEEP_PURPLE_900]
            orb.shadow.color = ft.Colors.PURPLE_500
            orb_status.value = "PROCESSING..."
            orb_status.color = ft.Colors.PURPLE_ACCENT
            
        elif mode == "SPEAKING":
            orb.scale = 1.1
            orb.gradient.colors = [ft.Colors.GREEN_ACCENT, ft.Colors.GREEN_900]
            orb.shadow.color = ft.Colors.GREEN_500
            orb_status.value = "SPEAKING..."
            orb_status.color = ft.Colors.GREEN_ACCENT
            
        elif mode == "IDLE":
            orb.scale = 1.0
            orb.gradient.colors = [ft.Colors.BLUE_GREY_700, ft.Colors.BLACK]
            orb.shadow.color = ft.Colors.BLACK
            orb_status.value = "ONLINE"
            orb_status.color = ft.Colors.GREY
            
        page.update()

    # --- CORE LOGIC (Background Thread) ---
    def run_voice_loop():
        config = {"configurable": {"thread_id": "Flet-Session-1"}}
        
        # Initial Welcome
        set_status("IDLE")
        time.sleep(0.5)
        try:
            speaker.speak("Interface Initialized.")
        except:
            pass
        
        while state["running"]:
            try:
                # 1. LISTEN
                set_status("LISTENING")
                user_text = listener.listen(mic_index=MIC_INDEX)
                
                if user_text:
                    chat_list.controls.append(create_bubble("You", user_text))
                    set_status("THINKING") 
                    page.update() 
                    
                    if "exit" in user_text.lower():
                        state["running"] = False
                        speaker.speak("Shutting down.")
                        page.window_close()
                        break
                    
                    # 2. THINK
                    result = app.invoke(
                        {"messages": [HumanMessage(content=user_text)]}, 
                        config=config
                    )
                    ai_response = result['messages'][-1].content
                    
                    # 3. SPEAK
                    chat_list.controls.append(create_bubble("AI", ai_response))
                    page.update()
                    
                    set_status("SPEAKING") 
                    speaker.speak(ai_response)
                
                else:
                    set_status("IDLE")
                    time.sleep(0.1)
                    
            except Exception as e:
                print(f"Error: {e}")
                set_status("IDLE")
        
        set_status("OFFLINE")

    # --- BUTTON ACTIONS ---
    def toggle_system(e):
        if not state["running"]:
            state["running"] = True
            btn_text.value = "STOP SYSTEM"
            btn_start.style = ft.ButtonStyle(bgcolor=ft.Colors.RED_900)
            threading.Thread(target=run_voice_loop, daemon=True).start()
        else:
            state["running"] = False
            btn_text.value = "START SYSTEM"
            btn_start.style = ft.ButtonStyle(bgcolor=ft.Colors.GREEN_900)
            set_status("IDLE")
        page.update()

    def clear_log(e):
        chat_list.controls.clear()
        page.update()

    # --- LAYOUT BUILD ---
    
    # Text inside button
    btn_text = ft.Text("START SYSTEM", color=ft.Colors.WHITE)
    
    # Modern FilledButton
    btn_start = ft.FilledButton(
        content=btn_text,
        style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_900),
        height=50,
        width=200,
        on_click=toggle_system
    )
    
    btn_clear = ft.TextButton(
        content=ft.Text("Clear Log"), 
        on_click=clear_log
    )

    # Left Panel
    left_panel = ft.Container(
        width=300,
        bgcolor=ft.Colors.BLUE_GREY_900,
        padding=20,
        content=ft.Column(
            [
                ft.Container(height=50), 
                # FIXED: Using ft.Alignment(0,0) explicitly. No 'center' shortcut.
                ft.Container(content=orb, alignment=ft.Alignment(0, 0)),
                ft.Container(height=30),
                ft.Container(content=orb_status, alignment=ft.Alignment(0, 0)),
                ft.Container(height=100), 
                ft.Container(content=btn_start, alignment=ft.Alignment(0, 0)),
                ft.Container(height=10),
                ft.Container(content=btn_clear, alignment=ft.Alignment(0, 0)),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )
    )

    # Right Panel
    right_panel = ft.Container(
        expand=True,
        padding=20,
        content=ft.Column(
            [
                ft.Text("LIVE LOG", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.CYAN_100),
                ft.Divider(color=ft.Colors.BLUE_GREY_800),
                chat_list
            ]
        )
    )

    # Add to Page
    page.add(
        ft.Row(
            [left_panel, right_panel],
            expand=True,
            spacing=0
        )
    )

# --- RUN APP ---
if __name__ == "__main__":
    ft.app(target=main)