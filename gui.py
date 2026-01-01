import os
import sys
import threading
import time
from datetime import datetime

# --- 1. AUTO-FIX FOR "TclError" (CRITICAL) ---
# This forces Python to find the missing GUI files in your Windows folder
try:
    # Get the base Python directory (e.g., C:\Users\mohan\...\Python313)
    base_path = os.path.dirname(sys.executable)
    
    # Define standard paths for Tcl/Tk 8.6
    tcl_path = os.path.join(base_path, "tcl", "tcl8.6")
    tk_path = os.path.join(base_path, "tcl", "tk8.6")

    # Manually set the environment variables
    if os.path.exists(tcl_path) and os.path.exists(tk_path):
        os.environ['TCL_LIBRARY'] = tcl_path
        os.environ['TK_LIBRARY'] = tk_path
        print(f"✅ GUI Fix Applied: Found Tcl at {tcl_path}")
    else:
        # Fallback for some custom installations
        os.environ['TCL_LIBRARY'] = r"C:\Users\mohan\AppData\Local\Programs\Python\Python313\tcl\tcl8.6"
        os.environ['TK_LIBRARY'] = r"C:\Users\mohan\AppData\Local\Programs\Python\Python313\tcl\tk8.6"
        print("⚠️ GUI Fix: Using fallback paths.")

except Exception as e:
    print(f"⚠️ GUI Setup Warning: {e}")
# ---------------------------------------------

import customtkinter as ctk
from langchain_core.messages import HumanMessage
from voice import listener, speaker
from backend.core import app

# --- CONFIGURATION ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class JarvisGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window Setup
        self.title("JARVIS - AI Agent")
        self.geometry("900x700")
        
        # State
        self.running = False
        self.thread = None
        self.config = {"configurable": {"thread_id": "Gui-Session-1"}}

        # --- LAYOUT ---
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # 1. Sidebar (Controls)
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        self.logo_label = ctk.CTkLabel(self.sidebar, text="JARVIS", font=ctk.CTkFont(size=24, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        self.status_label = ctk.CTkLabel(self.sidebar, text="STATUS: OFFLINE", text_color="gray")
        self.status_label.grid(row=1, column=0, padx=20, pady=10)

        self.start_btn = ctk.CTkButton(self.sidebar, text="START SYSTEM", command=self.toggle_system, fg_color="green")
        self.start_btn.grid(row=2, column=0, padx=20, pady=20)
        
        self.clear_btn = ctk.CTkButton(self.sidebar, text="CLEAR LOG", command=self.clear_chat, fg_color="transparent", border_width=1)
        self.clear_btn.grid(row=3, column=0, padx=20, pady=10)
        
        self.mic_label = ctk.CTkLabel(self.sidebar, text="Microphone: Active", font=ctk.CTkFont(size=12))
        self.mic_label.grid(row=4, column=0, padx=20, pady=(40, 10))

        # 2. Main Chat Area
        self.chat_frame = ctk.CTkScrollableFrame(self, label_text="Live Interaction Log")
        self.chat_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")

    def toggle_system(self):
        if not self.running:
            # Start
            self.running = True
            self.start_btn.configure(text="STOP SYSTEM", fg_color="red")
            self.status_label.configure(text="STATUS: ONLINE", text_color="#00FF00")
            
            # Run the "While True" loop in a separate thread so UI doesn't freeze
            self.thread = threading.Thread(target=self.run_voice_loop, daemon=True)
            self.thread.start()
        else:
            # Stop
            self.running = False
            self.start_btn.configure(text="START SYSTEM", fg_color="green")
            self.status_label.configure(text="STATUS: STOPPED", text_color="orange")

    def add_message(self, sender, text):
        """Adds a bubble to the chat window"""
        # Align: User (Right/Blue), AI (Left/Gray)
        if sender == "You":
            align = "e" # East (Right)
            color = "#1f6aa5"
        else:
            align = "w" # West (Left)
            color = "#2b2b2b"

        bubble = ctk.CTkLabel(
            self.chat_frame, 
            text=f"{sender}: {text}", 
            fg_color=color, 
            corner_radius=10,
            wraplength=400, # Wrap long text
            padx=10, pady=10,
            justify="left",
            font=ctk.CTkFont(size=14)
        )
        bubble.pack(pady=5, padx=10, anchor=align)
        
        # Auto-scroll to bottom
        # We use a slight delay to ensure the widget is packed before scrolling
        self.after(10, self._scroll_to_bottom)

    def _scroll_to_bottom(self):
        try:
            self.chat_frame._parent_canvas.yview_moveto(1.0)
        except:
            pass

    def update_status(self, text):
        """Updates the status label safely"""
        try:
            self.status_label.configure(text=f"STATUS: {text}")
        except:
            pass

    def clear_chat(self):
        for widget in self.chat_frame.winfo_children():
            widget.destroy()

    # --- THE CORE LOOP (Background Thread) ---
    def run_voice_loop(self):
        MIC_INDEX = 1 # <--- Verify this matches check_mics.py
        
        # Initial Greeting
        try:
            speaker.speak("Systems Online.")
            self.after(0, self.add_message, "AI", "Systems Online. Listening...")
        except:
            pass

        while self.running:
            try:
                # 1. Listen
                self.after(0, self.update_status, "LISTENING...")
                user_text = listener.listen(mic_index=MIC_INDEX)
                
                if user_text:
                    # Update UI with User Text
                    self.after(0, self.add_message, "You", user_text)
                    
                    if "exit" in user_text.lower():
                        self.running = False
                        self.after(0, self.toggle_system)
                        break

                    # 2. Think
                    self.after(0, self.update_status, "THINKING...")
                    
                    # Use the "Turbo" app logic from backend/core.py
                    result = app.invoke(
                        {"messages": [HumanMessage(content=user_text)]}, 
                        config=self.config
                    )
                    ai_response = result['messages'][-1].content
                    
                    # Update UI with AI Response
                    self.after(0, self.add_message, "AI", ai_response)

                    # 3. Speak
                    self.after(0, self.update_status, "SPEAKING...")
                    speaker.speak(ai_response)
            
            except Exception as e:
                print(f"Loop Error: {e}")
                pass
            
            # Small delay to prevent CPU hogging
            time.sleep(0.1)

        self.after(0, self.update_status, "OFFLINE")

if __name__ == "__main__":
    app_ui = JarvisGUI()
    app_ui.mainloop()