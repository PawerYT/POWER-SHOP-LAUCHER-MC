import customtkinter as ctk
import os
import subprocess
import json
import requests
import hashlib
from PIL import Image

# --- CONFIGURACIÓN PRINCIPAL PARA FORGE 1.20.1 ---
SERVER_URL = "https://raw.githubusercontent.com/TuUsuario/MiLauncher-Servidor/main/minecraft"  # ¡CAMBIA ESTO A TU URL!
MANIFEST_URL = f"{SERVER_URL}/manifest.json"
LAUNCHER_NAME = "ZMODS"
LAUNCHER_GEOMETRY = "1200x700"

# --- AJUSTES DE VERSIÓN ---
MINECRAFT_VERSION = "1.20.1"
FORGE_VERSION = "47.3.0"  # Versión de Forge para Minecraft 1.20.1

# --- RUTAS DE CARPETAS ---
LAUNCHER_DIR = os.path.dirname(os.path.abspath(__file__))
MINECRAFT_DIR = os.path.join(LAUNCHER_DIR, ".minecraft")
MODS_DIR = os.path.join(MINECRAFT_DIR, "mods")
# Asegúrate que esta ruta coincida con la estructura de tu JDK 17 portable.
JAVA_PATH = os.path.join(LAUNCHER_DIR, "Java", "jdk-17.0.11_9", "bin", "java.exe") 

os.makedirs(MODS_DIR, exist_ok=True)

# --- CLASE PRINCIPAL DEL LAUNCHER ---
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(LAUNCHER_NAME)
        self.geometry(LAUNCHER_GEOMETRY)
        self.resizable(False, False)

        # Cargar imagen de fondo
        bg_image_path = os.path.join(LAUNCHER_DIR, "fondo.png")
        if os.path.exists(bg_image_path):
            self.bg_image = ctk.CTkImage(Image.open(bg_image_path), size=(1200, 700))
            self.bg_label = ctk.CTkLabel(self, image=self.bg_image, text="")
            self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        # --- WIDGETS ---
        self.username_entry = ctk.CTkEntry(self, placeholder_text="Nombre de Usuario", width=200)
        self.username_entry.place(relx=0.5, rely=0.7, anchor="center")
        
        self.status_label = ctk.CTkLabel(self, text="¡Bienvenido!", font=("Arial", 16))
        self.status_label.place(relx=0.5, rely=0.75, anchor="center")

        self.progress_bar = ctk.CTkProgressBar(self, width=300)
        self.progress_bar.set(0)
        self.progress_bar.place(relx=0.5, rely=0.8, anchor="center")
        
        self.play_button = ctk.CTkButton(self, text="Jugar", width=200, height=40, command=self.ejecutar_minecraft, state="disabled")
        self.play_button.place(relx=0.5, rely=0.85, anchor="center")
        
        self.after(100, self.sincronizar_mods) # Ejecuta la sincronización después de iniciar la ventana

    def sha256_checksum(self, filename, block_size=65536):
        sha256 = hashlib.sha256()
        with open(filename, 'rb') as f:
            for block in iter(lambda: f.read(block_size), b''):
                sha256.update(block)
        return sha256.hexdigest()

    def sincronizar_mods(self):
        self.status_label.configure(text="Verificando actualizaciones de mods...")
        self.update_idletasks() # Actualiza la UI
        
        try:
            response = requests.get(MANIFEST_URL)
            response.raise_for_status()
            manifest = response.json()
            
            mods_servidor = {mod['name']: mod for mod in manifest['files']}
            mods_locales = {f for f in os.listdir(MODS_DIR) if f.endswith('.jar')}

            # Borrar mods obsoletos
            for mod_local in mods_locales:
                if mod_local not in mods_servidor:
                    os.remove(os.path.join(MODS_DIR, mod_local))

            # Verificar y descargar mods
            total_mods = len(mods_servidor)
            for i, (nombre_mod, data_mod) in enumerate(mods_servidor.items()):
                ruta_local_mod = os.path.join(MODS_DIR, nombre_mod)
                self.status_label.configure(text=f"Verificando {nombre_mod}...")
                self.update_idletasks()
                
                if not os.path.exists(ruta_local_mod) or self.sha256_checksum(ruta_local_mod) != data_mod['hash']:
                    self.status_label.configure(text=f"Descargando {nombre_mod}...")
                    self.update_idletasks()
                    mod_response = requests.get(data_mod['url'])
                    mod_response.raise_for_status()
                    with open(ruta_local_mod, 'wb') as f:
                        f.write(mod_response.content)

                self.progress_bar.set((i + 1) / total_mods)

            self.status_label.configure(text="¡Todo listo para jugar!")
            self.play_button.configure(state="normal")

        except Exception as e:
            self.status_label.configure(text=f"Error de actualización. Revisa la conexión.", text_color="red")
            print(f"Error al sincronizar: {e}")
            self.play_button.configure(state="normal") # Permitir jugar offline si falla

    def ejecutar_minecraft(self):
        username = self.username_entry.get()
        if not username:
            self.status_label.configure(text="Introduce un nombre de usuario.", text_color="orange")
            return

        opciones = {
            "username": username,
            "uuid": hashlib.md5(username.encode()).hexdigest(),
            "token": "0",
            "jvmArguments": ["-Xmx4G", "-Xms2G"]
        }
        
        forge_full_version = f"{MINECRAFT_VERSION}-forge-{FORGE_VERSION}"
        comando = minecraft_launcher_lib.command.get_minecraft_command(forge_full_version, MINECRAFT_DIR, opciones)
        comando[0] = JAVA_PATH

        self.status_label.configure(text="Iniciando Minecraft...")
        try:
            subprocess.Popen(comando)
        except Exception as e:
            self.status_label.configure(text=f"Error al iniciar Minecraft: {e}", text_color="red")

if __name__ == "__main__":
    app = App()
    app.mainloop()