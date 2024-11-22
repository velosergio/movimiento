import tkinter as tk
from tkinter import ttk
import pygame
import json
import os

class XboxControllerConfig:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Configuración Control Xbox")
        
        # Inicializar pygame para el joystick
        pygame.init()
        pygame.joystick.init()
        
        # Configuración por defecto
        self.config = {
            'A': None,
            'B': None,
            'X': None,
            'Y': None,
            'LB': None,
            'RB': None,
            'START': None,
            'BACK': None
        }
        
        self.load_config()
        self.create_gui()
    
    def load_config(self):
        try:
            with open('controller_config.json', 'r') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            pass
    
    def save_config(self):
        with open('controller_config.json', 'w') as f:
            json.dump(self.config, f, indent=4)
    
    def create_gui(self):
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Crear elementos para cada botón
        row = 0
        for button in self.config.keys():
            ttk.Label(main_frame, text=f"Botón {button}:").grid(row=row, column=0, pady=5)
            
            # Entry para mostrar la configuración actual
            entry = ttk.Entry(main_frame)
            entry.grid(row=row, column=1, pady=5, padx=5)
            if self.config[button]:
                entry.insert(0, self.config[button])
            
            # Botón para configurar
            ttk.Button(
                main_frame, 
                text="Configurar",
                command=lambda b=button, e=entry: self.configure_button(b, e)
            ).grid(row=row, column=2, pady=5)
            
            row += 1
        
        # Botón guardar
        ttk.Button(
            main_frame,
            text="Guardar configuración",
            command=self.save_config
        ).grid(row=row, column=0, columnspan=3, pady=20)
    
    def configure_button(self, button_name, entry_widget):
        # Ventana de configuración
        config_window = tk.Toplevel(self.root)
        config_window.title(f"Configurar {button_name}")
        
        label = ttk.Label(config_window, text="Presiona el botón que deseas asignar...")
        label.pack(pady=20, padx=20)
        
        def check_button():
            if pygame.joystick.get_count() > 0:
                joystick = pygame.joystick.Joystick(0)
                joystick.init()
                
                pygame.event.pump()
                for event in pygame.event.get():
                    if event.type == pygame.JOYBUTTONDOWN:
                        self.config[button_name] = f"Botón {event.button}"
                        entry_widget.delete(0, tk.END)
                        entry_widget.insert(0, self.config[button_name])
                        config_window.destroy()
                        return
                
            config_window.after(100, check_button)
        
        check_button()
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = XboxControllerConfig()
    app.run() 