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

    def find_xbox_controller(self):
        """Busca el control de Xbox One entre los dispositivos Bluetooth"""
        print("Buscando control de Xbox One...")
        try:
            # Escanear dispositivos Bluetooth
            subprocess.run(['bluetoothctl', 'scan', 'on'], timeout=10)
            time.sleep(5)  # Dar tiempo para escanear
            
            # Obtener dispositivos emparejados
            result = subprocess.run(['bluetoothctl', 'paired-devices'],
                                 capture_output=True, text=True)
            
            for line in result.stdout.split('\n'):
                if self.controller_name in line:
                    self.controller_mac = line.split()[1]
                    print(f"Control encontrado: {self.controller_mac}")
                    return True
            
            print("Control no encontrado")
            return False
        except Exception as e:
            print(f"Error buscando el control: {e}")
            return False

    def connect_controller(self):
        """Conecta el control si está disponible"""
        if not self.controller_mac:
            return False
        
        try:
            print("Intentando conectar el control...")
            subprocess.run(['bluetoothctl', 'connect', self.controller_mac], 
                         check=True, timeout=10)
            time.sleep(2)
            return True
        except subprocess.CalledProcessError:
            print("Error conectando el control")
            return False

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
        
        if not self.find_xbox_controller():
            print("No se encontró el control. Asegúrate de que está en modo de emparejamiento")
            return False
        
        if not self.connect_controller():
            print("No se pudo conectar el control")
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