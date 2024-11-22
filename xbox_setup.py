#!/usr/bin/env python3
import subprocess
import time
import os
import sys

class XboxControllerSetup:
    def __init__(self):
        self.controller_mac = None
        self.controller_name = "Xbox Wireless Controller"
    
    def check_root(self):
        """Verifica si el script se está ejecutando como root"""
        if os.geteuid() != 0:
            print("Este script necesita privilegios de root.")
            print("Por favor, ejecuta: sudo python3 xbox_setup.py")
            sys.exit(1)

    def install_dependencies(self):
        """Instala las dependencias necesarias"""
        print("Instalando dependencias necesarias...")
        try:
            packages = ['bluetooth', 'bluez', 'xboxdrv']
            subprocess.run(['apt-get', 'update'], check=True)
            for package in packages:
                subprocess.run(['apt-get', 'install', '-y', package], check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error instalando dependencias: {e}")
            return False

    def setup_bluetooth_rules(self):
        """Configura las reglas udev para el control"""
        rules_content = '''
# Reglas para Xbox One Controller
SUBSYSTEM=="usb", ATTRS{idVendor}=="045e", ATTRS{idProduct}=="02ea", MODE="0666"
SUBSYSTEM=="input", ATTRS{name}=="Xbox Wireless Controller", MODE="0666"
'''
        try:
            with open('/etc/udev/rules.d/99-xbox-controller.rules', 'w') as f:
                f.write(rules_content)
            
            # Recargar reglas udev
            subprocess.run(['udevadm', 'control', '--reload-rules'], check=True)
            subprocess.run(['udevadm', 'trigger'], check=True)
            return True
        except Exception as e:
            print(f"Error configurando reglas udev: {e}")
            return False

    def setup_bluetooth_connection(self):
        """Configura la conexión Bluetooth con el control de Xbox"""
        print("Configurando conexión Bluetooth...")
        
        def execute_bluetooth_command(command, timeout=10):
            try:
                result = subprocess.run(['bluetoothctl', *command.split()],
                                      capture_output=True,
                                      text=True,
                                      timeout=timeout)
                return result.stdout
            except Exception as e:
                print(f"Error ejecutando {command}: {e}")
                return ""

        try:
            # Limpieza inicial más exhaustiva
            print("Limpiando configuraciones previas...")
            execute_bluetooth_command("remove EC:83:50:FD:99:15")  # Tu MAC específica
            subprocess.run(['sudo', 'systemctl', 'restart', 'bluetooth'], check=True)
            time.sleep(3)
            
            # Configuración más robusta de bluetooth
            execute_bluetooth_command("power off")
            time.sleep(1)
            execute_bluetooth_command("power on")
            time.sleep(1)
            execute_bluetooth_command("agent on")
            execute_bluetooth_command("default-agent")
            
            # Asegurarse que xboxdrv no está corriendo
            subprocess.run(['sudo', 'systemctl', 'stop', 'xboxdrv'], check=False)
            
            print("Buscando control de Xbox One...")
            print("Por favor, mantén presionado el botón de sincronización del control...")
            
            execute_bluetooth_command("scan on")
            time.sleep(5)  # Dar más tiempo para el escaneo inicial

            # Buscar el control con tu MAC específica
            self.controller_mac = "EC:83:50:FD:99:15"  # Tu MAC
            
            # Secuencia de conexión mejorada
            print(f"Intentando conectar con el control ({self.controller_mac})...")
            
            # Primero remover cualquier conexión existente
            execute_bluetooth_command(f"remove {self.controller_mac}")
            time.sleep(2)
            
            # Intentar emparejar
            print("Emparejando control...")
            pair_result = execute_bluetooth_command(f"pair {self.controller_mac}")
            time.sleep(3)
            
            # Establecer confianza antes de conectar
            print("Estableciendo confianza...")
            trust_result = execute_bluetooth_command(f"trust {self.controller_mac}")
            time.sleep(2)
            
            # Intentar conectar múltiples veces si es necesario
            max_connect_attempts = 3
            for attempt in range(max_connect_attempts):
                print(f"Intento de conexión {attempt + 1}/{max_connect_attempts}")
                connect_result = execute_bluetooth_command(f"connect {self.controller_mac}")
                time.sleep(2)
                
                # Verificar estado de conexión
                info = execute_bluetooth_command(f"info {self.controller_mac}")
                if "Connected: yes" in info:
                    print("Conexión establecida exitosamente")
                    
                    # Iniciar xboxdrv con configuración específica
                    print("Configurando driver del control...")
                    try:
                        subprocess.Popen([
                            'sudo', 'xboxdrv',
                            '--detach-kernel-driver',
                            '--dpad-as-button',
                            '--deadzone', '4000',
                            '--device-by-id', self.controller_mac,
                            '--type', 'xbox360-wireless',
                            '--axismap', '-Y1=Y1,-Y2=Y2',
                            '--mimic-xpad',
                            '--silent'
                        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        
                        time.sleep(2)
                        return True
                    except Exception as e:
                        print(f"Error iniciando xboxdrv: {e}")
                        return False
                
                print("Reintentando conexión...")
                time.sleep(2)
            
            print("No se pudo establecer una conexión estable")
            return False

        except Exception as e:
            print(f"Error en la configuración Bluetooth: {e}")
            return False
        finally:
            execute_bluetooth_command("scan off")

    def setup_xboxdrv(self):
        """Configura xboxdrv como servicio"""
        service_content = '''[Unit]
Description=Xbox Controller Driver
After=bluetooth.service
Wants=bluetooth.service

[Service]
ExecStart=/usr/bin/xboxdrv --daemon --detach-kernel-driver --dpad-as-button --deadzone 4000
Restart=on-failure

[Install]
WantedBy=multi-user.target
'''
        try:
            # Crear archivo de servicio
            with open('/etc/systemd/system/xboxdrv.service', 'w') as f:
                f.write(service_content)
            
            # Recargar systemd y habilitar el servicio
            subprocess.run(['systemctl', 'daemon-reload'], check=True)
            subprocess.run(['systemctl', 'enable', 'xboxdrv.service'], check=True)
            subprocess.run(['systemctl', 'start', 'xboxdrv.service'], check=True)
            return True
        except Exception as e:
            print(f"Error configurando xboxdrv: {e}")
            return False

    def verify_controller(self):
        """Verifica si el control está funcionando"""
        try:
            result = subprocess.run(['ls', '/dev/input/js0'], 
                                 capture_output=True, text=True)
            if result.returncode == 0:
                print("Control verificado y funcionando (/dev/input/js0)")
                return True
            return False
        except Exception:
            return False

    def verify_controller_status(self):
        """Verifica el estado actual del control"""
        try:
            # Verificar si el dispositivo está presente
            js_check = subprocess.run(['ls', '/dev/input/js0'], 
                                    capture_output=True, 
                                    text=True)
            
            if js_check.returncode != 0:
                print("Control no detectado en /dev/input/js0")
                return False
            
            # Verificar estado de conexión bluetooth
            info = subprocess.run(['bluetoothctl', 'info', self.controller_mac],
                                capture_output=True,
                                text=True)
            
            if "Connected: yes" not in info.stdout:
                print("Control no conectado via Bluetooth")
                return False
            
            # Verificar si xboxdrv está corriendo
            xboxdrv_check = subprocess.run(['pgrep', 'xboxdrv'],
                                         capture_output=True)
            
            if xboxdrv_check.returncode != 0:
                print("xboxdrv no está corriendo")
                return False
            
            print("Control verificado y funcionando correctamente")
            return True
            
        except Exception as e:
            print(f"Error verificando estado del control: {e}")
            return False

    def setup(self):
        """Proceso principal de configuración"""
        print("Iniciando configuración del control Xbox One...")
        
        self.check_root()
        
        if not self.install_dependencies():
            print("Error instalando dependencias")
            return False
        
        if not self.setup_bluetooth_rules():
            print("Error configurando reglas del sistema")
            return False
        
        if not self.setup_bluetooth_connection():  # Nueva función
            print("Error en la configuración Bluetooth")
            return False
        
        if not self.setup_xboxdrv():
            print("Error configurando xboxdrv")
            return False
        
        if self.verify_controller():
            print("\n¡Configuración exitosa!")
            print("El control está listo para usarse")
            print("Puedes acceder al control mediante /dev/input/js0")
            return True
        else:
            print("Error en la verificación final del control")
            return False

if __name__ == "__main__":
    setup = XboxControllerSetup()
    setup.setup() 