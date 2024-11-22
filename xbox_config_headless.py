import pygame
import json
import os
import time
import math

class XboxControllerConfigHeadless:
    def __init__(self):
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

    def load_profiles(self):
        try:
            with open('controller_profiles.json', 'r') as f:
                self.profiles = json.load(f)
                print("Perfiles cargados exitosamente")
                print("Perfiles disponibles:", list(self.profiles.keys()))
        except FileNotFoundError:
            self.profiles = {"Default": self.default_config.copy()}
            print("No se encontraron perfiles previos. Creando perfil por defecto")

    def save_profiles(self):
        with open('controller_profiles.json', 'w') as f:
            json.dump(self.profiles, f, indent=4)
        print("Perfiles guardados exitosamente")

    def monitor_controller(self):
        if pygame.joystick.get_count() == 0:
            print("No se detectó ningún control. Conecta un control Xbox y vuelve a intentar.")
            return False

        joystick = pygame.joystick.Joystick(0)
        joystick.init()
        print(f"\nControl detectado: {joystick.get_name()}")
        print("Monitoreando entradas del control. Presiona Ctrl+C para salir.")
        
        try:
            while True:
                pygame.event.pump()
                
                # Monitorear sticks
                lx = joystick.get_axis(0)
                ly = joystick.get_axis(1)
                rx = joystick.get_axis(3)
                ry = joystick.get_axis(4)
                
                # Monitorear triggers
                lt = (joystick.get_axis(2) + 1) / 2
                rt = (joystick.get_axis(5) + 1) / 2
                
                # Limpiar eventos
                for event in pygame.event.get():
                    if event.type == pygame.JOYBUTTONDOWN:
                        print(f"\nBotón presionado: {event.button}")
                
                # Solo mostrar valores si superan la zona muerta
                dead_zone = 0.15
                if abs(lx) > dead_zone or abs(ly) > dead_zone:
                    print(f"\rStick Izquierdo: X:{lx:6.2f} Y:{ly:6.2f}", end='')
                if abs(rx) > dead_zone or abs(ry) > dead_zone:
                    print(f" | Stick Derecho: X:{rx:6.2f} Y:{ry:6.2f}", end='')
                if lt > dead_zone:
                    print(f" | LT:{lt:4.2f}", end='')
                if rt > dead_zone:
                    print(f" | RT:{rt:4.2f}", end='')
                
                time.sleep(0.1)  # Reducir la frecuencia de actualización
                
        except KeyboardInterrupt:
            print("\n\nMonitoreo finalizado")
            return True

    def calibrate_sticks(self):
        if pygame.joystick.get_count() == 0:
            print("No se detectó ningún control")
            return

        joystick = pygame.joystick.Joystick(0)
        joystick.init()
        
        print("\nCalibración de sticks:")
        print("1. Deja los sticks en posición neutral")
        input("Presiona Enter cuando estés listo...")
        
        # Calibrar centro
        for stick in ['LEFT', 'RIGHT']:
            if stick == 'LEFT':
                x = joystick.get_axis(0)
                y = joystick.get_axis(1)
            else:
                x = joystick.get_axis(3)
                y = joystick.get_axis(4)
            
            self.profiles[self.current_profile]['sticks'][stick]['center_x'] = x
            self.profiles[self.current_profile]['sticks'][stick]['center_y'] = y
            print(f"Stick {stick} calibrado - Centro X:{x:.2f} Y:{y:.2f}")

    def show_menu(self):
        while True:
            print("\n=== Configurador de Control Xbox ===")
            print("1. Monitorear entradas del control")
            print("2. Calibrar sticks")
            print("3. Crear nuevo perfil")
            print("4. Cambiar perfil actual")
            print("5. Guardar configuración")
            print("6. Salir")
            
            option = input("\nSelecciona una opción: ")
            
            if option == "1":
                self.monitor_controller()
            elif option == "2":
                self.calibrate_sticks()
            elif option == "3":
                name = input("Nombre del nuevo perfil: ")
                if name and name not in self.profiles:
                    self.profiles[name] = self.default_config.copy()
                    self.current_profile = name
                    print(f"Perfil '{name}' creado y seleccionado")
            elif option == "4":
                print("\nPerfiles disponibles:")
                for i, profile in enumerate(self.profiles.keys(), 1):
                    print(f"{i}. {profile}")
                try:
                    idx = int(input("\nSelecciona el número de perfil: ")) - 1
                    profile_name = list(self.profiles.keys())[idx]
                    self.current_profile = profile_name
                    print(f"Perfil '{profile_name}' seleccionado")
                except (ValueError, IndexError):
                    print("Selección inválida")
            elif option == "5":
                self.save_profiles()
            elif option == "6":
                print("¡Hasta luego!")
                break
            else:
                print("Opción inválida")

if __name__ == "__main__":
    app = XboxControllerConfigHeadless()
    app.show_menu() 