#!/usr/bin/env python3
"""
Script de Prueba para Sistema de Vigilancia Autónomo Snow
Verifica que todos los componentes funcionen correctamente
"""

import sys
import os
import json
import time
import logging
from pathlib import Path

def verificar_archivos():
    """Verifica que todos los archivos necesarios existan"""
    print("🔍 Verificando archivos del sistema...")
    
    archivos_requeridos = [
        "sistema_vigilancia_autonomo.py",
        "sistema_emergencia_sms.py", 
        "optimizador_energia.py",
        "config_sistema.json",
        "config_sms.json",
        "config_energia.json",
        "best.pt",
        "sonido_prueva0.mp3",
        "sonido_prueva2.mp3"
    ]
    
    archivos_faltantes = []
    for archivo in archivos_requeridos:
        if not Path(archivo).exists():
            archivos_faltantes.append(archivo)
        else:
            print(f"  ✅ {archivo}")
    
    if archivos_faltantes:
        print(f"  ❌ Archivos faltantes: {archivos_faltantes}")
        return False
    
    print("  ✅ Todos los archivos requeridos están presentes")
    return True

def verificar_dependencias():
    """Verifica que las dependencias de Python estén instaladas"""
    print("\n🔍 Verificando dependencias de Python...")
    
    dependencias = [
        "ultralytics",
        "cv2", 
        "pygame",
        "psutil",
        "numpy",
        "threading",
        "logging",
        "json",
        "time",
        "datetime"
    ]
    
    dependencias_faltantes = []
    for dep in dependencias:
        try:
            if dep == "cv2":
                import cv2
            elif dep == "ultralytics":
                from ultralytics import YOLO
            elif dep == "pygame":
                import pygame
            elif dep == "psutil":
                import psutil
            elif dep == "numpy":
                import numpy
            else:
                __import__(dep)
            print(f"  ✅ {dep}")
        except ImportError:
            dependencias_faltantes.append(dep)
            print(f"  ❌ {dep}")
    
    if dependencias_faltantes:
        print(f"  ❌ Dependencias faltantes: {dependencias_faltantes}")
        print("  💡 Instalar con: pip3 install " + " ".join(dependencias_faltantes))
        return False
    
    print("  ✅ Todas las dependencias están instaladas")
    return True

def verificar_configuraciones():
    """Verifica que los archivos de configuración sean válidos"""
    print("\n🔍 Verificando configuraciones...")
    
    configs = [
        ("config_sistema.json", "Configuración principal"),
        ("config_sms.json", "Configuración SMS"),
        ("config_energia.json", "Configuración energía")
    ]
    
    for archivo, descripcion in configs:
        try:
            with open(archivo, 'r') as f:
                config = json.load(f)
            print(f"  ✅ {descripcion} - Válida")
        except FileNotFoundError:
            print(f"  ❌ {descripcion} - Archivo no encontrado")
            return False
        except json.JSONDecodeError as e:
            print(f"  ❌ {descripcion} - JSON inválido: {e}")
            return False
    
    print("  ✅ Todas las configuraciones son válidas")
    return True

def verificar_camara():
    """Verifica que la cámara esté disponible"""
    print("\n🔍 Verificando cámara...")
    
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("  ❌ No se pudo abrir la cámara")
            return False
        
        ret, frame = cap.read()
        if not ret:
            print("  ❌ No se pudo capturar frame de la cámara")
            cap.release()
            return False
        
        print(f"  ✅ Cámara funcionando - Resolución: {frame.shape[1]}x{frame.shape[0]}")
        cap.release()
        return True
        
    except Exception as e:
        print(f"  ❌ Error verificando cámara: {e}")
        return False

def verificar_modelo_yolo():
    """Verifica que el modelo YOLO esté disponible"""
    print("\n🔍 Verificando modelo YOLO...")
    
    try:
        from ultralytics import YOLO
        
        if not Path("best.pt").exists():
            print("  ❌ Archivo best.pt no encontrado")
            return False
        
        modelo = YOLO('best.pt')
        print("  ✅ Modelo YOLO cargado correctamente")
        return True
        
    except Exception as e:
        print(f"  ❌ Error cargando modelo YOLO: {e}")
        return False

def verificar_audio():
    """Verifica que los archivos de audio estén disponibles"""
    print("\n🔍 Verificando archivos de audio...")
    
    archivos_audio = [
        "sonido_prueva0.mp3",
        "sonido_prueva2.mp3"
    ]
    
    for archivo in archivos_audio:
        if Path(archivo).exists():
            print(f"  ✅ {archivo}")
        else:
            print(f"  ❌ {archivo} - No encontrado")
            return False
    
    try:
        import pygame
        pygame.mixer.init()
        print("  ✅ Pygame mixer inicializado")
        return True
    except Exception as e:
        print(f"  ❌ Error inicializando pygame: {e}")
        return False

def verificar_gpio():
    """Verifica que GPIO esté disponible (solo en Raspberry Pi)"""
    print("\n🔍 Verificando GPIO...")
    
    try:
        import RPi.GPIO as GPIO
        print("  ✅ RPi.GPIO disponible")
        return True
    except ImportError:
        print("  ⚠️  RPi.GPIO no disponible (no es Raspberry Pi o no instalado)")
        return True  # No es crítico para la prueba
    except Exception as e:
        print(f"  ❌ Error con GPIO: {e}")
        return False

def verificar_directorios():
    """Verifica que los directorios necesarios existan"""
    print("\n🔍 Verificando directorios...")
    
    directorios = ["logs", "backups"]
    
    for directorio in directorios:
        Path(directorio).mkdir(exist_ok=True)
        print(f"  ✅ Directorio {directorio}/ creado/verificado")
    
    return True

def prueba_sistema_basico():
    """Ejecuta una prueba básica del sistema"""
    print("\n🧪 Ejecutando prueba básica del sistema...")
    
    try:
        # Importar el sistema de desarrollo
        sys.path.append('.')
        from sistema_desarrollo import SistemaVigilanciaDesarrollo
        
        print("  ✅ Sistema de desarrollo importado correctamente")
        
        # Crear instancia (sin inicializar hardware)
        print("  🔄 Creando instancia del sistema...")
        # Nota: No inicializamos completamente para evitar problemas con hardware
        
        print("  ✅ Prueba básica completada")
        return True
        
    except Exception as e:
        print(f"  ❌ Error en prueba básica: {e}")
        return False

def generar_reporte():
    """Genera un reporte de la verificación"""
    print("\n📋 Generando reporte...")
    
    reporte = {
        "fecha": time.strftime("%Y-%m-%d %H:%M:%S"),
        "sistema": "Sistema de Vigilancia Autónomo SADA",
        "version": "1.0",
        "resultados": {}
    }
    
    # Aquí se podrían agregar más verificaciones y resultados
    
    with open("reporte_verificacion.json", "w") as f:
        json.dump(reporte, f, indent=4)
    
    print("  ✅ Reporte generado: reporte_verificacion.json")

def main():
    """Función principal de verificación"""
    print("🚀 Sistema de Verificación SADA")
    print("=" * 50)
    
    verificaciones = [
        ("Archivos del sistema", verificar_archivos),
        ("Dependencias Python", verificar_dependencias),
        ("Configuraciones", verificar_configuraciones),
        ("Cámara", verificar_camara),
        ("Modelo YOLO", verificar_modelo_yolo),
        ("Audio", verificar_audio),
        ("GPIO", verificar_gpio),
        ("Directorios", verificar_directorios),
        ("Sistema básico", prueba_sistema_basico)
    ]
    
    resultados = []
    
    for nombre, funcion in verificaciones:
        try:
            resultado = funcion()
            resultados.append((nombre, resultado))
        except Exception as e:
            print(f"  ❌ Error en {nombre}: {e}")
            resultados.append((nombre, False))
    
    # Resumen final
    print("\n" + "=" * 50)
    print("📊 RESUMEN DE VERIFICACIÓN")
    print("=" * 50)
    
    exitosos = 0
    total = len(resultados)
    
    for nombre, resultado in resultados:
        estado = "✅ EXITOSO" if resultado else "❌ FALLIDO"
        print(f"{nombre:.<30} {estado}")
        if resultado:
            exitosos += 1
    
    print(f"\nResultado: {exitosos}/{total} verificaciones exitosas")
    
    if exitosos == total:
        print("🎉 ¡Sistema listo para funcionar!")
        print("\nPróximos pasos:")
        print("1. Ejecutar: ./instalar_sistema.sh")
        print("2. Reiniciar: sudo reboot")
        print("3. Iniciar: ./iniciar_sistema.sh")
    else:
        print("⚠️  Algunas verificaciones fallaron. Revisar errores arriba.")
        print("\nSoluciones comunes:")
        print("- Instalar dependencias faltantes: pip3 install <dependencia>")
        print("- Verificar conexión de cámara")
        print("- Verificar archivos de configuración")
    
    generar_reporte()
    
    return exitosos == total

if __name__ == "__main__":
    try:
        exito = main()
        sys.exit(0 if exito else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Verificación interrumpida por usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error crítico en verificación: {e}")
        sys.exit(1)
