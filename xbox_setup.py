#!/usr/bin/env python3
import subprocess
import time
import os
import sys

class XboxControllerSetup:
    def __init__(self):
        self.controller_mac = None
        self.controller_name = "Xbox Wireless Controller"
        self.xpadneo_path = "xpadneo"

    def check_root(self):
        """Verifica privilegios de root"""
        if os.geteuid() != 0:
            print("Este script necesita privilegios de root.")
            print("Por favor, ejecuta: sudo python3 xbox_setup.py")
            sys.exit(1)

    def install_dependencies(self):
        """Instala las dependencias necesarias y xpadneo"""
        print("Instalando dependencias...")
        try:
            # Actualizar repositorios
            subprocess.run(['apt-get', 'update'], check=True)
            
            # Instalar dependencias necesarias
            dependencies = [
                'dkms',
                'git',
                'raspberrypi-kernel-headers',
                'bluetooth',
                'bluez'
            ]
            
            for dep in dependencies:
                print(f"Instalando {dep}...")
                subprocess.run(['apt-get', 'install', '-y', dep], check=True)

            # Desinstalar xboxdrv si está instalado
            try:
                subprocess.run(['apt-get', 'remove', '-y', 'xboxdrv'], check=True)
            except:
                pass

            # Instalar xpadneo
            print("\nInstalando xpadneo...")
            if os.path.exists(self.xpadneo_path):
                subprocess.run(['rm', '-rf', self.xpadneo_path], check=True)
            
            subprocess.run(['git', 'clone', 'https://github.com/atar-axis/xpadneo.git'], check=True)
            os.chdir(self.xpadneo_path)
            subprocess.run(['./install.sh'], check=True)
            os.chdir('..')
            
            print("Dependencias instaladas correctamente")
            return True

        except Exception as e:
            print(f"Error instalando dependencias: {e}")
            return False

    def setup_bluetooth_connection(self):
        """Configura la conexión Bluetooth con el control"""
        print("\nConfigurando conexión Bluetooth...")
        
        def execute_bluetooth_command(command, timeout=10):
            try:
                result = subprocess.run(['bluetoothctl', *command.split()],
                                      capture_output=True,
                                      text=True,
                                      timeout=timeout)
                return result.stdout
            except Exception as e:
                print(f"Error ejecutando comando bluetooth: {e}")
                return ""

        try:
            # Reiniciar servicio bluetooth
            subprocess.run(['systemctl', 'restart', 'bluetooth'], check=True)
            time.sleep(2)

            # Configuración inicial bluetooth
            execute_bluetooth_command("power off")
            time.sleep(1)
            execute_bluetooth_command("power on")
            time.sleep(1)
            execute_bluetooth_command("agent on")
            execute_bluetooth_command("default-agent")

            print("\nBuscando control de Xbox One...")
            print("Por favor, mantén presionado el botón de sincronización del control...")
            
            # Iniciar escaneo
            execute_bluetooth_command("scan on")
            
            # Buscar el control
            attempts = 0
            max_attempts = 30
            while attempts < max_attempts:
                devices = execute_bluetooth_command("devices")
                for line in devices.split('\n'):
                    if "Xbox Wireless Controller" in line:
                        self.controller_mac = line.split()[1]
                        print(f"\n¡Control encontrado! MAC: {self.controller_mac}")
                        
                        # Detener escaneo
                        execute_bluetooth_command("scan off")
                        
                        # Remover conexiones previas
                        execute_bluetooth_command(f"remove {self.controller_mac}")
                        time.sleep(2)
                        
                        # Emparejar
                        print("Emparejando control...")
                        execute_bluetooth_command(f"pair {self.controller_mac}")
                        time.sleep(3)
                        
                        # Confiar
                        print("Estableciendo confianza...")
                        execute_bluetooth_command(f"trust {self.controller_mac}")
                        time.sleep(2)
                        
                        # Conectar
                        print("Conectando control...")
                        execute_bluetooth_command(f"connect {self.controller_mac}")
                        time.sleep(2)
                        
                        # Verificar conexión
                        info = execute_bluetooth_command(f"info {self.controller_mac}")
                        if "Connected: yes" in info:
                            print("Control conectado exitosamente")
                            return True
                        else:
                            print("Error en la conexión final")
                            return False
                
                attempts += 1
                sys.stdout.write(f"\rBuscando control... {attempts}/{max_attempts}")
                sys.stdout.flush()
                time.sleep(1)
            
            print("\nNo se encontró el control")
            return False

        except Exception as e:
            print(f"Error en la configuración Bluetooth: {e}")
            return False
        finally:
            execute_bluetooth_command("scan off")

    def verify_controller(self):
        """Verifica el funcionamiento del control"""
        try:
            # Verificar módulo xpadneo
            lsmod = subprocess.run(['lsmod'], capture_output=True, text=True)
            if 'xpadneo' not in lsmod.stdout:
                print("Módulo xpadneo no detectado")
                return False

            # Verificar dispositivo de juego
            js_check = subprocess.run(['ls', '/dev/input/js0'], 
                                    capture_output=True, 
                                    text=True)
            if js_check.returncode != 0:
                print("Control no detectado en /dev/input/js0")
                return False

            # Verificar conexión bluetooth
            if self.controller_mac:
                info = subprocess.run(['bluetoothctl', 'info', self.controller_mac],
                                    capture_output=True,
                                    text=True)
                if "Connected: yes" not in info.stdout:
                    print("Control no conectado via Bluetooth")
                    return False

            print("Control verificado y funcionando correctamente")
            return True

        except Exception as e:
            print(f"Error verificando el control: {e}")
            return False

    def setup(self):
        """Proceso principal de configuración"""
        print("=== Configuración del Control Xbox One con xpadneo ===")
        
        self.check_root()
        
        if not self.install_dependencies():
            print("Error instalando dependencias")
            return False
        
        if not self.setup_bluetooth_connection():
            print("Error en la configuración Bluetooth")
            return False
        
        if self.verify_controller():
            print("\n¡Configuración exitosa!")
            print("El control está listo para usarse")
            print("\nSe recomienda reiniciar el sistema.")
            print("¿Deseas reiniciar ahora? (s/n)")
            if input().lower() == 's':
                subprocess.run(['reboot'])
            return True
        else:
            print("Error en la verificación final del control")
            return False

if __name__ == "__main__":
    setup = XboxControllerSetup()
    setup.setup() 