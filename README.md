# Movimiento - Instalación de arte interactivo

Este proyecto es una aplicación interactiva desarrollada con `pygame` que permite manipular las letras de la palabra "MOVIMIENTO" mediante un control de Xbox. Puedes mover las letras, cambiar su tamaño y seleccionar diferentes letras para modificarlas.

## Características
- Movimiento de letras usando un joystick.
- Cambio de tamaño de las letras con los gatillos del control.
- Resaltar la letra seleccionada.

## Requisitos
- Python 3
- `pygame` biblioteca
- Control de Xbox
- Biblioteca `inputs`

## Instrucciones de Instalación

Sigue los siguientes pasos para instalar las dependencias y ejecutar la aplicación en tu sistema.

### Paso 1: Clonar el Repositorio
Clona este repositorio usando el comando:
```sh
$ git clone https://github.com/tu-usuario/movimiento-app.git
$ cd movimiento-app
```

### Paso 2: Actualizar el Sistema
Asegúrate de que tu sistema está actualizado:
```sh
$ sudo apt-get update
$ sudo apt-get upgrade
```

### Paso 3: Instalar Dependencias
Instala las dependencias necesarias para ejecutar el proyecto.

- Instala `pygame` para gráficos:
  ```sh
  $ sudo apt-get install python3-pygame
  ```

- Instala `joystick` y `xboxdrv` para soporte del control de Xbox:
  ```sh
  $ sudo apt-get install joystick
  $ sudo apt-get install xboxdrv
  ```

- Instala la biblioteca `inputs`:
  ```sh
  $ pip3 install inputs
  ```

### Paso 4: Ejecutar la Aplicación
Para ejecutar la aplicación, utiliza el siguiente comando:
```sh
$ python3 main.py
```

## Uso
- **Joystick Izquierdo**: Mueve la letra seleccionada.
- **Gatillo Izquierdo** (`ABS_Z`): Reduce el tamaño de la letra seleccionada.
- **Gatillo Derecho** (`ABS_RZ`): Aumenta el tamaño de la letra seleccionada.
- **Botón A** (`BTN_SOUTH`): Cambia la letra seleccionada hacia adelante.
- **Botón X** (`BTN_NORTH`): Cambia la letra seleccionada hacia atrás.
- **Botón START** (`BTN_START`): Salir de la aplicación.

## Notas
- Se ha añadido un umbral (`JOYSTICK_DEADZONE`) para evitar que pequeñas variaciones en los joysticks (conocido como "joystick drift") afecten el movimiento de las letras.
- La aplicación resaltará la letra seleccionada con un color verde.

## Licencia
Este proyecto está licenciado bajo la licencia MIT. Para más información, consulta el archivo `LICENSE`.

## Contribuciones
¡Las contribuciones son bienvenidas! Si deseas mejorar esta aplicación, por favor, abre un issue o envía un pull request en GitHub.

## Autor
Creado por [Sergio Esteban Veloza González](https://sergioveloza.com).
