import tkinter as tk
from tkinter import ttk, messagebox
import pygame
import json
import os
from PIL import Image, ImageTk
import math

class XboxControllerConfig:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Configuración Avanzada Control Xbox")
        
        # Inicializar pygame
        pygame.init()
        pygame.joystick.init()
        
        # Configuración por defecto
        self.default_config = {
            'buttons': {
                'A': None, 'B': None, 'X': None, 'Y': None,
                'LB': None, 'RB': None, 'START': None, 'BACK': None
            },
            'triggers': {
                'LT': {'min': 0, 'max': 1},
                'RT': {'min': 0, 'max': 1}
            },
            'sticks': {
                'LEFT': {'center_x': 0, 'center_y': 0, 'dead_zone': 0.2},
                'RIGHT': {'center_x': 0, 'center_y': 0, 'dead_zone': 0.2}
            }
        }
        
        self.profiles = {}
        self.current_profile = "Default"
        self.load_profiles()
        
        self.create_notebook_interface()
        self.setup_visualization()
        self.update_visualization()
    
    def load_profiles(self):
        try:
            with open('controller_profiles.json', 'r') as f:
                self.profiles = json.load(f)
        except FileNotFoundError:
            self.profiles = {"Default": self.default_config.copy()}
    
    def save_profiles(self):
        with open('controller_profiles.json', 'w') as f:
            json.dump(self.profiles, f, indent=4)
        messagebox.showinfo("Éxito", "Perfiles guardados correctamente")
    
    def create_notebook_interface(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill='both', padx=5, pady=5)
        
        # Pestañas principales
        self.config_frame = ttk.Frame(self.notebook)
        self.visual_frame = ttk.Frame(self.notebook)
        self.calibration_frame = ttk.Frame(self.notebook)
        
        self.notebook.add(self.config_frame, text="Configuración")
        self.notebook.add(self.visual_frame, text="Visualización")
        self.notebook.add(self.calibration_frame, text="Calibración")
        
        self.create_config_tab()
        self.create_visual_tab()
        self.create_calibration_tab()
    
    def create_config_tab(self):
        # Frame para selección de perfil
        profile_frame = ttk.LabelFrame(self.config_frame, text="Perfiles")
        profile_frame.pack(fill='x', padx=5, pady=5)
        
        # Combobox para perfiles
        self.profile_var = tk.StringVar(value=self.current_profile)
        self.profile_combo = ttk.Combobox(
            profile_frame, 
            textvariable=self.profile_var,
            values=list(self.profiles.keys())
        )
        self.profile_combo.pack(side='left', padx=5)
        
        # Botones de perfil
        ttk.Button(profile_frame, text="Nuevo", command=self.new_profile).pack(side='left', padx=2)
        ttk.Button(profile_frame, text="Guardar", command=self.save_profiles).pack(side='left', padx=2)
        ttk.Button(profile_frame, text="Eliminar", command=self.delete_profile).pack(side='left', padx=2)
        
        # Frame para botones
        button_frame = ttk.LabelFrame(self.config_frame, text="Botones")
        button_frame.pack(fill='x', padx=5, pady=5)
        
        # Crear configuración para cada botón
        for button in self.profiles[self.current_profile]['buttons'].keys():
            self.create_button_config(button_frame, button)
        
        # Frame para triggers
        trigger_frame = ttk.LabelFrame(self.config_frame, text="Gatillos")
        trigger_frame.pack(fill='x', padx=5, pady=5)
        
        for trigger in ['LT', 'RT']:
            self.create_trigger_config(trigger_frame, trigger)
    
    def create_visual_tab(self):
        self.canvas = tk.Canvas(self.visual_frame, width=400, height=300)
        self.canvas.pack(expand=True, fill='both')
        
        # Crear visualizaciones para sticks
        self.left_stick = self.canvas.create_oval(50, 50, 100, 100, fill='gray')
        self.right_stick = self.canvas.create_oval(250, 50, 300, 100, fill='gray')
        
        # Visualizaciones para triggers
        self.lt_bar = self.canvas.create_rectangle(50, 150, 100, 200, fill='gray')
        self.rt_bar = self.canvas.create_rectangle(250, 150, 300, 200, fill='gray')
    
    def create_calibration_tab(self):
        # Frame para calibración de sticks
        for stick in ['LEFT', 'RIGHT']:
            frame = ttk.LabelFrame(self.calibration_frame, text=f"Stick {stick}")
            frame.pack(fill='x', padx=5, pady=5)
            
            ttk.Button(
                frame,
                text="Calibrar centro",
                command=lambda s=stick: self.calibrate_stick_center(s)
            ).pack(side='left', padx=5)
            
            ttk.Label(frame, text="Zona muerta:").pack(side='left', padx=5)
            scale = ttk.Scale(
                frame,
                from_=0,
                to=1,
                orient='horizontal',
                value=self.profiles[self.current_profile]['sticks'][stick]['dead_zone']
            )
            scale.pack(side='left', expand=True, fill='x', padx=5)
    
    def update_visualization(self):
        if pygame.joystick.get_count() > 0:
            joystick = pygame.joystick.Joystick(0)
            joystick.init()
            
            # Actualizar posición de sticks
            lx = joystick.get_axis(0)
            ly = joystick.get_axis(1)
            rx = joystick.get_axis(3)
            ry = joystick.get_axis(4)
            
            # Actualizar visualización de sticks
            self.update_stick_position(self.left_stick, lx, ly)
            self.update_stick_position(self.right_stick, rx, ry)
            
            # Actualizar visualización de triggers
            lt = joystick.get_axis(2)
            rt = joystick.get_axis(5)
            self.update_trigger_position(self.lt_bar, lt)
            self.update_trigger_position(self.rt_bar, rt)
        
        self.root.after(16, self.update_visualization)  # ~60 FPS
    
    def update_stick_position(self, stick_obj, x, y):
        # Convertir coordenadas de -1,1 a coordenadas de pantalla
        center_x = 75 if stick_obj == self.left_stick else 275
        center_y = 75
        
        radius = 25
        screen_x = center_x + (x * radius)
        screen_y = center_y + (y * radius)
        
        self.canvas.coords(
            stick_obj,
            screen_x - 10,
            screen_y - 10,
            screen_x + 10,
            screen_y + 10
        )
    
    def update_trigger_position(self, trigger_obj, value):
        # Convertir valor de -1,1 a altura de barra
        value = (value + 1) / 2  # Convertir a 0-1
        height = 50 * value
        
        coords = self.canvas.coords(trigger_obj)
        self.canvas.coords(
            trigger_obj,
            coords[0],
            coords[3] - height,
            coords[2],
            coords[3]
        )
    
    def calibrate_stick_center(self, stick):
        if pygame.joystick.get_count() > 0:
            joystick = pygame.joystick.Joystick(0)
            joystick.init()
            
            if stick == 'LEFT':
                x = joystick.get_axis(0)
                y = joystick.get_axis(1)
            else:
                x = joystick.get_axis(3)
                y = joystick.get_axis(4)
            
            self.profiles[self.current_profile]['sticks'][stick]['center_x'] = x
            self.profiles[self.current_profile]['sticks'][stick]['center_y'] = y
            
            messagebox.showinfo(
                "Calibración",
                f"Centro del stick {stick} calibrado en X:{x:.2f} Y:{y:.2f}"
            )
    
    def new_profile(self):
        name = tk.simpledialog.askstring("Nuevo Perfil", "Nombre del nuevo perfil:")
        if name and name not in self.profiles:
            self.profiles[name] = self.default_config.copy()
            self.profile_combo['values'] = list(self.profiles.keys())
            self.profile_var.set(name)
    
    def delete_profile(self):
        if self.current_profile != "Default":
            del self.profiles[self.current_profile]
            self.current_profile = "Default"
            self.profile_var.set("Default")
            self.profile_combo['values'] = list(self.profiles.keys())
    
    def create_test_tab(self):
        test_frame = ttk.Frame(self.notebook)
        self.notebook.add(test_frame, text="Modo Prueba")
        
        # Canvas para mostrar qué botones están siendo presionados
        self.test_canvas = tk.Canvas(test_frame, width=400, height=300)
        self.test_canvas.pack(expand=True, fill='both')
        
        # Área de texto para mostrar eventos
        self.event_text = tk.Text(test_frame, height=10)
        self.event_text.pack(fill='x')
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = XboxControllerConfig()
    app.run() 