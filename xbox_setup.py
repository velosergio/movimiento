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
            """Ejecuta comandos de bluetoothctl y retorna la salida"""
            try:
                result = subprocess.run(['bluetoothctl', *command.split()],
                                      capture_output=True,
                                      text=True,
                                      timeout=timeout)
                return result.stdout
            except subprocess.TimeoutExpired:
                print(f"Tiempo de espera agotado ejecutando: {command}")
                return ""
            except Exception as e:
                print(f"Error ejecutando {command}: {e}")
                return ""

        try:
            # Reiniciar el servicio bluetooth
            subprocess.run(['systemctl', 'restart', 'bluetooth'], check=True)
            time.sleep(2)

            # Configuración inicial de bluetoothctl
            execute_bluetooth_command("power on")
            execute_bluetooth_command("agent on")
            execute_bluetooth_command("default-agent")
            
            # Detener cualquier escaneo previo
            execute_bluetooth_command("scan off")
            time.sleep(1)

            print("Buscando control de Xbox One...")
            print("Por favor, mantén presionado el botón de sincronización del control...")
            
            # Iniciar escaneo en un proceso separado
            scan_process = subprocess.Popen(['bluetoothctl', 'scan', 'on'],
                                          stdout=subprocess.PIPE,
                                          stderr=subprocess.PIPE)
            
            # Esperar y buscar el control
            max_attempts = 30
            attempt = 0
            while attempt < max_attempts:
                devices_output = execute_bluetooth_command("devices")
                for line in devices_output.split('\n'):
                    if "Xbox Wireless Controller" in line:
                        self.controller_mac = line.split()[1]
                        print(f"¡Control encontrado! MAC: {self.controller_mac}")
                        
                        # Detener el escaneo
                        execute_bluetooth_command("scan off")
                        scan_process.terminate()
                        
                        print("Emparejando control...")
                        pair_result = execute_bluetooth_command(f"pair {self.controller_mac}")
                        if "Failed" in pair_result:
                            print("Error en el emparejamiento. Reintentando...")
                            execute_bluetooth_command(f"remove {self.controller_mac}")
                            time.sleep(2)
                            execute_bluetooth_command(f"pair {self.controller_mac}")

                        print("Conectando control...")
                        connect_result = execute_bluetooth_command(f"connect {self.controller_mac}")
                        if "Failed" in connect_result:
                            print("Error en la conexión. Reintentando...")
                            time.sleep(2)
                            execute_bluetooth_command(f"connect {self.controller_mac}")

                        print("Estableciendo confianza con el control...")
                        trust_result = execute_bluetooth_command(f"trust {self.controller_mac}")
                        
                        # Verificar estado final
                        info = execute_bluetooth_command(f"info {self.controller_mac}")
                        if "Connected: yes" in info:
                            print("¡Control configurado exitosamente!")
                            return True
                        else:
                            print("Error en la conexión final")
                            return False

                attempt += 1
                time.sleep(1)
                sys.stdout.write(f"\rBuscando control... {attempt}/{max_attempts}")
                sys.stdout.flush()

            print("\nNo se encontró el control después de varios intentos")
            return False

        except Exception as e:
            print(f"Error en la configuración Bluetooth: {e}")
            return False
        finally:
            # Asegurarse de detener el escaneo
            execute_bluetooth_command("scan off")
            if 'scan_process' in locals():
                scan_process.terminate()

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