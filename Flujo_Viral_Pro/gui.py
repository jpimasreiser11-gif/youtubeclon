import os
import subprocess
import threading
import json
import customtkinter as ctk
from tkinter import filedialog, messagebox

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class ViralApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Ensure we are running from the script's directory
        os.chdir(os.path.dirname(os.path.abspath(__file__)))

        self.title("Flujo Viral Pro V2 - Estudio Documental")
        self.geometry("1000x700")

        # Config
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Data
        self.channels = self.load_channels()

        # Build UI
        self.create_sidebar()
        self.create_main_view()
        
        # State
        self.current_idea = {}

    def load_channels(self):
        if os.path.exists("channels.json"):
            try:
                with open("channels.json", "r", encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []

    def save_channels(self):
        with open("channels.json", "w", encoding='utf-8') as f:
            json.dump(self.channels, f, indent=2)

    def create_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        self.logo_label = ctk.CTkLabel(self.sidebar, text="Viral Pro V2", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        self.btn_shorts = ctk.CTkButton(self.sidebar, text="1. Shorts (Rápido)", command=self.show_shorts)
        self.btn_shorts.grid(row=1, column=0, padx=20, pady=10)
        
        self.btn_channels = ctk.CTkButton(self.sidebar, text="2. Canales", command=self.show_channels)
        self.btn_channels.grid(row=2, column=0, padx=20, pady=10)
        
        self.btn_docs = ctk.CTkButton(self.sidebar, text="3. Documental (15m)", command=self.show_docs)
        self.btn_docs.grid(row=3, column=0, padx=20, pady=10)
        
        self.btn_settings = ctk.CTkButton(self.sidebar, text="Configuración (.env)", command=self.show_settings)
        self.btn_settings.grid(row=4, column=0, padx=20, pady=10)

    def create_main_view(self):
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        
        # --- SHORTS UI ---
        self.shorts_ui = ctk.CTkFrame(self.main_frame)
        self.setup_shorts_ui()

        # --- CHANNELS UI ---
        self.channels_ui = ctk.CTkFrame(self.main_frame)
        self.setup_channels_ui()

        # --- DOCS UI ---
        self.docs_ui = ctk.CTkFrame(self.main_frame)
        self.setup_docs_ui()

        self.show_shorts()

    def setup_shorts_ui(self):
        ctk.CTkLabel(self.shorts_ui, text="Generador de Shorts Rapidos", font=("Arial", 18)).pack(pady=10)
        
        self.idea_btn = ctk.CTkButton(self.shorts_ui, text="Generar Idea (Gemini)", command=self.run_ideation_thread, fg_color="green")
        self.idea_btn.pack(pady=10)
        
        self.nicho_entry = ctk.CTkEntry(self.shorts_ui, placeholder_text="Nicho/Tema")
        self.nicho_entry.pack(pady=5, padx=20, fill="x")
        self.keywords_entry = ctk.CTkEntry(self.shorts_ui, placeholder_text="Keywords (Inglés)")
        self.keywords_entry.pack(pady=5, padx=20, fill="x")
        self.script_text = ctk.CTkTextbox(self.shorts_ui, height=150)
        self.script_text.pack(pady=10, padx=20, fill="both", expand=True)
        
        self.prod_btn = ctk.CTkButton(self.shorts_ui, text="Producir Short", command=self.run_production_shorts_thread, fg_color="red")
        self.prod_btn.pack(pady=10)
        self.shorts_log = ctk.CTkTextbox(self.shorts_ui, height=100)
        self.shorts_log.pack(pady=10, padx=20, fill="x")

    def setup_channels_ui(self):
        ctk.CTkLabel(self.channels_ui, text="Gestión de Canales", font=("Arial", 18)).pack(pady=10)
        
        self.channel_list = ctk.CTkTextbox(self.channels_ui, height=200)
        self.channel_list.pack(pady=10, padx=20, fill="both")
        self.refresh_channel_list()
        
        form_frame = ctk.CTkFrame(self.channels_ui)
        form_frame.pack(pady=10, padx=20, fill="x")
        
        self.new_channel_name = ctk.CTkEntry(form_frame, placeholder_text="Nombre del Canal")
        self.new_channel_name.pack(pady=5, fill="x")
        self.new_channel_topic = ctk.CTkEntry(form_frame, placeholder_text="Tema / Nicho")
        self.new_channel_topic.pack(pady=5, fill="x")
        self.new_channel_tone = ctk.CTkEntry(form_frame, placeholder_text="Tono (ej: Serio, Divertido, Academico)")
        self.new_channel_tone.pack(pady=5, fill="x")
        
        ctk.CTkButton(form_frame, text="Añadir Canal", command=self.add_channel).pack(pady=10)

    def setup_docs_ui(self):
        ctk.CTkLabel(self.docs_ui, text="Productora de Documentales (Long Form 15m)", font=("Arial", 18)).pack(pady=10)
        
        ctk.CTkLabel(self.docs_ui, text="Selecciona Canal:").pack()
        self.channel_selector = ctk.CTkComboBox(self.docs_ui, values=[c["name"] for c in self.channels] if self.channels else ["Sin Canales"])
        self.channel_selector.pack(pady=5)
        
        self.doc_topic = ctk.CTkEntry(self.docs_ui, placeholder_text="Tema del Documental (ej: El origen del universo)")
        self.doc_topic.pack(pady=10, padx=20, fill="x")
        
        self.btn_start_doc = ctk.CTkButton(self.docs_ui, text="Iniciar Producción Documental", command=self.run_doc_thread, fg_color="purple")
        self.btn_start_doc.pack(pady=20)
        
        self.doc_log = ctk.CTkTextbox(self.docs_ui)
        self.doc_log.pack(pady=10, padx=20, fill="both", expand=True)

    # --- Actions ---
    
    def show_shorts(self):
        self.channels_ui.pack_forget(); self.docs_ui.pack_forget(); self.shorts_ui.pack(fill="both", expand=True)
    def show_channels(self):
        self.shorts_ui.pack_forget(); self.docs_ui.pack_forget(); self.channels_ui.pack(fill="both", expand=True)
    def show_docs(self):
        self.shorts_ui.pack_forget(); self.channels_ui.pack_forget(); self.docs_ui.pack(fill="both", expand=True)
        if self.channels:
            self.channel_selector.configure(values=[c["name"] for c in self.channels])
            self.channel_selector.set(self.channels[0]["name"])

    def show_settings(self):
        subprocess.Popen(["notepad", ".env"])

    def refresh_channel_list(self):
        self.channel_list.delete("1.0", "end")
        text = json.dumps(self.channels, indent=2, ensure_ascii=False)
        self.channel_list.insert("1.0", text)

    def add_channel(self):
        name = self.new_channel_name.get()
        if not name: return
        new_c = {
            "name": name,
            "topic": self.new_channel_topic.get(),
            "tone": self.new_channel_tone.get(),
            "target_audience": "General",
            "frequency_per_day": 1
        }
        self.channels.append(new_c)
        self.save_channels()
        self.refresh_channel_list()
        self.new_channel_name.delete(0, 'end')
        self.new_channel_topic.delete(0, 'end')
        self.new_channel_tone.delete(0, 'end')
        messagebox.showinfo("Canal Añadido", f"Canal {new_c['name']} guardado.")

    def run_ideation_thread(self): threading.Thread(target=self.run_ideation).start()
    def run_production_shorts_thread(self): threading.Thread(target=self.run_production_shorts).start()
    def run_doc_thread(self): threading.Thread(target=self.run_production_doc).start()

    # --- Logic Implementations ---
    
    def run_ideation(self):
        self.idea_btn.configure(state="disabled", text="Generando...")
        try:
             res = subprocess.run(["python", "scripts/ideation.py"], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
             if res.returncode == 0:
                 data = json.loads(res.stdout)
                 self.nicho_entry.delete(0, "end"); self.nicho_entry.insert(0, data.get("nicho", ""))
                 self.keywords_entry.delete(0, "end"); self.keywords_entry.insert(0, data.get("keywords", ""))
                 self.script_text.delete("1.0", "end"); self.script_text.insert("1.0", data.get("script_text", ""))
             else: messagebox.showerror("Error", res.stderr)
        except Exception as e: messagebox.showerror("Error", str(e))
        finally: self.idea_btn.configure(state="normal", text="Generar Nueva Idea")

    def run_production_shorts(self):
        self.prod_btn.configure(state="disabled"); self.shorts_log.insert("end", "Iniciando...\n")
        
        script = self.script_text.get("1.0", "end-1c")
        keywords = self.keywords_entry.get()
        
        os.makedirs("temp", exist_ok=True)
        audio_file = "temp/gui_audio.mp3"
        video_stock = "temp/gui_stock.mp4"
        final_video = "gui_output.mp4"
        
        # TTS
        self.shorts_log.insert("end", "TTS...\n")
        subprocess.run(["python", "scripts/tts.py", "--text", script, "--output", audio_file], creationflags=subprocess.CREATE_NO_WINDOW)
        
        # Fetch
        self.shorts_log.insert("end", "Fetching Video...\n")
        subprocess.run(["python", "scripts/fetch_video.py", "--keywords", keywords, "--output", video_stock], creationflags=subprocess.CREATE_NO_WINDOW)
        
        # Render
        self.shorts_log.insert("end", "Rendering...\n")
        res = subprocess.run(["python", "scripts/render.py", "--audio", audio_file, "--video", video_stock, "--output", final_video], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
        
        if res.returncode == 0:
            self.shorts_log.insert("end", "Hecho!\n")
            subprocess.Popen(["explorer", "/select,", os.path.abspath(final_video)])
        else:
            self.shorts_log.insert("end", f"Error: {res.stderr}\n")
            
        self.prod_btn.configure(state="normal")

    def run_production_doc(self):
        topic = self.doc_topic.get()
        channel_name = self.channel_selector.get()
        if not topic or not channel_name:
            self.log_doc("Error: Selecciona canal y tema.")
            return

        self.btn_start_doc.configure(state="disabled")
        self.log_doc(f"Iniciando Documental: {topic} para {channel_name}")
        
        # 1. Analyze Channel Style
        channel = next((c for c in self.channels if c["name"] == channel_name), None)
        if not channel:
            self.log_doc("Error: Canal no encontrado.")
            return
            
        style_prompt = f"Tono: {channel.get('tone', 'Generico')}. Audiencia: {channel.get('target_audience', 'General')}."
        
        # 2. Generate Long Form Script
        self.log_doc("Generando Estructura del Documental (Paso 1/2)...")
        # We invoke the script as a module or subprocess? 
        # Ideally subprocess to keep UI responsive and separate envs if needed, 
        # but importing writes logic easier. Let's use subprocess to trigger a wrapper or just use the existing script if it had a CLI.
        # scripts/long_form_writer.py currently has a __main__ test block but not CLI args.
        # I should probably update long_form_writer.py to accept CLI args or call it here.
        # Let's import it for now as I can't easily add CLI args without another edit.
        # WAIT: modifying long_form_writer.py would be better.
        
        # Let's try to import dynamically to avoid top-level easy errors
        try:
             # Add scripts to path
             import sys
             sys.path.append("scripts")
             import long_form_writer
             
             script_json = long_form_writer.generate_full_script(topic, style_prompt)
             if not script_json:
                 self.log_doc("Error generando guion.")
                 self.btn_start_doc.configure(state="normal")
                 return
                 
             script_path = f"temp/doc_script_{channel_name}.json"
             with open(script_path, "w", encoding='utf-8') as f:
                 json.dump(script_json, f, indent=2)
                 
             self.log_doc("Guion generado. Iniciando Renderizado (Paso 2/2)...")
             self.log_doc(f"Titulo: {script_json['meta']['title']}")
             
             # 3. Render
             output_file = f"doc_{channel_name}_{topic.replace(' ', '_')}.mp4"
             cmd = ["python", "scripts/render_long.py", "--script", script_path, "--output", output_file]
             
             proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
             stdout, stderr = proc.communicate()
             
             if proc.returncode == 0:
                 self.log_doc(f"EXITO! Video guardado: {output_file}")
                 subprocess.Popen(["explorer", "/select,", os.path.abspath(output_file)])
             else:
                 self.log_doc(f"Error Render: {stderr}\n{stdout}")
                 
        except Exception as e:
            self.log_doc(f"Error Critico: {str(e)}")
            import traceback
            self.log_doc(traceback.format_exc())
            
        self.btn_start_doc.configure(state="normal")

    def log_doc(self, msg):
        self.doc_log.insert("end", msg + "\n")
        self.doc_log.see("end")

if __name__ == "__main__":
    app = ViralApp()
    app.mainloop()
