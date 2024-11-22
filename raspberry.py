import pygame
import random
from inputs import get_gamepad
import threading
import sys
import subprocess
import time
import os

def setup_xbox_controller():
    """Función para detectar y configurar el control de Xbox One"""
    print("Iniciando configuración del control Xbox One...")
    
    def check_bluetooth_controller():
        try:
            # Verificar dispositivos Bluetooth emparejados
            result = subprocess.run(['bluetoothctl', 'paired-devices'], 
                                  capture_output=True, 
                                  text=True)
            
            # Verificar dispositivos Bluetooth conectados
            connected = subprocess.run(['bluetoothctl', 'info'], 
                                    capture_output=True, 
                                    text=True)
            
            if "Xbox Wireless Controller" in result.stdout:
                if "Connected: yes" in connected.stdout:
                    print("Control Xbox One encontrado y conectado")
                    return True
                else:
                    print("Control Xbox One encontrado pero no conectado")
                    # Intentar conectar automáticamente
                    device_addr = None
                    for line in result.stdout.split('\n'):
                        if "Xbox Wireless Controller" in line:
                            device_addr = line.split()[1]
                            break
                    
                    if device_addr:
                        print("Intentando conectar automáticamente...")
                        connect = subprocess.run(['bluetoothctl', 'connect', device_addr],
                                              capture_output=True,
                                              text=True)
                        return "Connection successful" in connect.stdout
            return False
        except Exception as e:
            print(f"Error verificando Bluetooth: {e}")
            return False

    def setup_controller_mapping():
        try:
            # Verificar si xboxdrv está instalado
            subprocess.run(['which', 'xboxdrv'], check=True)
        except subprocess.CalledProcessError:
            print("xboxdrv no está instalado. Instalando...")
            try:
                subprocess.run(['sudo', 'apt-get', 'update'], check=True)
                subprocess.run(['sudo', 'apt-get', 'install', '-y', 'xboxdrv'], check=True)
            except subprocess.CalledProcessError as e:
                print(f"Error instalando xboxdrv: {e}")
                return False

        try:
            # Configurar el mapeo del control
            subprocess.Popen(['sudo', 'xboxdrv', 
                            '--detach-kernel-driver',
                            '--dpad-as-button',
                            '--axismap', '-Y1=Y1',  # Invertir eje Y del stick izquierdo
                            '--axismap', '-Y2=Y2',  # Invertir eje Y del stick derecho
                            '--silent'],
                           stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL)
            return True
        except Exception as e:
            print(f"Error configurando el mapeo del control: {e}")
            return False

    # Secuencia principal de configuración
    print("1. Verificando conexión Bluetooth...")
    if not check_bluetooth_controller():
        print("No se encontró el control por Bluetooth")
        print("Por favor, asegúrate de que:")
        print("1. El control está encendido")
        print("2. El Bluetooth está activado")
        print("3. El control está emparejado con la Raspberry Pi")
        return False

    print("2. Configurando mapeo del control...")
    if not setup_controller_mapping():
        print("Error en la configuración del mapeo del control")
        return False

    # Verificar si podemos recibir eventos del control
    print("3. Verificando eventos del control...")
    timeout = time.time() + 10
    while time.time() < timeout:
        try:
            events = get_gamepad()
            if events:
                print("¡Control configurado y funcionando correctamente!")
                return True
        except Exception:
            time.sleep(0.1)
            continue

    print("No se pudieron detectar eventos del control")
    return False

def test_controller():
    """Función para probar el control"""
    print("\nPrueba del control:")
    print("Mueve los sticks y presiona algunos botones...")
    print("Presiona Ctrl+C para terminar la prueba")
    
    try:
        while True:
            events = get_gamepad()
            for event in events:
                print(f"Tipo: {event.ev_type}, Código: {event.code}, Estado: {event.state}")
    except KeyboardInterrupt:
        print("\nPrueba finalizada")
    except Exception as e:
        print(f"Error durante la prueba: {e}")

# Función principal
def main():
    # Verificar si se está ejecutando en Raspberry Pi
    is_raspberry_pi = os.path.exists('/sys/firmware/devicetree/base/model')
    
    if is_raspberry_pi:
        print("Detectado sistema Raspberry Pi")
        if not setup_xbox_controller():
            print("No se pudo configurar el control. Saliendo...")
            sys.exit(1)
        
        # Opcional: descomentar para probar el control
        # test_controller()
    
    # Inicializar pygame y continuar con el resto del código
    pygame.init()
    
    # Configuración de la pantalla
    WIDTH, HEIGHT = 800, 600
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Movimiento")

    # Colores
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)

    # Palabra a mostrar
    word = "MOVIMIENTO"
    letters = list(word)

    # Tamaños aleatorios para cada letra
    letter_sizes = [random.randint(74, 200) for _ in letters]

    # Posición inicial de las letras
    letter_positions = [
        [50 + i * 70, HEIGHT // 2] for i in range(len(letters))
    ]

    # Ángulos de rotación para cada letra
    letter_rotations = [0 for _ in letters]

    # Variables de control
    selected_index = 0
    left_stick_x = 0
    left_stick_y = 0
    running = True
    move_active = False

    # Funciones para manejar el control de Xbox
    def handle_gamepad():
        global left_stick_x, left_stick_y, running, move_active, selected_index
        
        while running:
            try:
                events = get_gamepad()
                for event in events:
                    if event.ev_type == "Absolute":
                        # Stick izquierdo
                        if event.code == "ABS_X":  # Movimiento horizontal
                            if abs(event.state) > 3000:  # Zona muerta
                                left_stick_x = event.state / 32767 * 5
                                move_active = True
                            else:
                                left_stick_x = 0
                                move_active = False
                                
                        elif event.code == "ABS_Y":  # Movimiento vertical
                            if abs(event.state) > 3000:  # Zona muerta
                                left_stick_y = event.state / 32767 * 5
                                move_active = True
                            else:
                                left_stick_y = 0
                                move_active = False
                                
                        elif event.code == "ABS_Z":  # Gatillo izquierdo
                            if event.state > 0:
                                letter_sizes[selected_index] = max(74, letter_sizes[selected_index] - 2)
                                
                        elif event.code == "ABS_RZ":  # Gatillo derecho
                            if event.state > 0:
                                letter_sizes[selected_index] = min(200, letter_sizes[selected_index] + 2)
                                
                        # Stick derecho para rotación
                        elif event.code == "ABS_RX":  # Eje X del stick derecho
                            if abs(event.state) > 3000:
                                # Rotar más rápido cuando el stick se mueve más
                                rotation_speed = event.state / 32767 * 5
                                letter_rotations[selected_index] += rotation_speed
                                # Mantener el ángulo entre 0 y 360 grados
                                letter_rotations[selected_index] %= 360
                                
                    elif event.ev_type == "Key" and event.state == 1:
                        if event.code == "BTN_SOUTH":  # Botón A
                            selected_index = (selected_index + 1) % len(letters)
                        elif event.code == "BTN_NORTH":  # Botón Y
                            selected_index = (selected_index - 1) % len(letters)
                        elif event.code == "BTN_START":  # Botón Start
                            running = False
                            
            except Exception as e:
                print(f"Error en el gamepad: {e}")
                continue

    # Crear un hilo para manejar el gamepad
    gamepad_thread = threading.Thread(target=handle_gamepad)
    gamepad_thread.daemon = True
    gamepad_thread.start()

    # Modificar el manejo de salida
    def cleanup():
        pygame.quit()
        sys.exit()

    # Agregar después de las importaciones
    def test_gamepad():
        print("Probando gamepad... Mueve los controles")
        try:
            while True:
                events = get_gamepad()
                for event in events:
                    print(event.ev_type, event.code, event.state)
        except KeyboardInterrupt:
            pass

    # Descomentar para probar:
    # test_gamepad()

    # Bucle principal del programa
    while running:
        screen.fill(WHITE)

        # Dibujar las letras en pantalla
        for i, (letter, pos, size, rotation) in enumerate(zip(letters, letter_positions, letter_sizes, letter_rotations)):
            font = pygame.font.Font(None, size)
            color = BLACK if i != selected_index else (0, 255, 0)
            text = font.render(letter, True, color)
            
            # Crear una superficie rotada
            rotated_text = pygame.transform.rotate(text, rotation)
            # Obtener el rectángulo de la superficie rotada
            text_rect = rotated_text.get_rect(center=(pos[0], pos[1]))
            # Dibujar el texto rotado
            screen.blit(rotated_text, text_rect)

        # Mover la letra seleccionada según el joystick izquierdo solo si se está presionando
        if move_active:
            letter_positions[selected_index][0] += left_stick_x
            letter_positions[selected_index][1] -= left_stick_y
            
            # Limitar el movimiento dentro de la pantalla
            letter_positions[selected_index][0] = max(0, min(WIDTH - 50, letter_positions[selected_index][0]))
            letter_positions[selected_index][1] = max(0, min(HEIGHT - 50, letter_positions[selected_index][1]))

        # Manejar eventos de salida
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                cleanup()

        pygame.display.flip()

    # Finalizar pygame
    pygame.quit()

if __name__ == "__main__":
    main()