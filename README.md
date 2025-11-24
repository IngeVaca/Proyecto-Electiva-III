# Sistema IoT de Monitoreo para Micro-Paneles Solares

Solución completa de hardware y software para la caracterización experimental de paneles solares de baja potencia en condiciones ambientales reales. Desarrollado como parte de una investigación sobre sistemas fotovoltaicos en el contexto climático de la sabana de Bogotá.

## Características Principales

### Hardware
- **ESP32** como unidad central de procesamiento
- **Sensor DHT22** para temperatura y humedad ambiental
- **Sistema de medición** de tensión y corriente DC
- **Alimentación regulada** con protección térmica
- **PCB personalizado** para integración robusta

### Software
- **Firmware ESP32** con conexión WiFi dual
- **Comunicación MQTT** para transmisión en tiempo real
- **Dashboard HTML/JavaScript** para visualización local
- **Integración con ThingSpeak** para monitoreo remoto
- **Generación automática** de archivos CSV diarios

### Análisis de Datos
- **Scripts Python** para análisis exploratorio (EDA)
- **Visualizaciones profesionales** de comportamiento eléctrico
- **Análisis de correlaciones** ambientales
- **Validación experimental** vs modelos teóricos

## Datos del Estudio

- **Período de medición**: Noviembre 2025
- **Ubicación**: Bogotá, Colombia (4.6°N, 74.1°W, 2640 msnm)
- **Panel bajo prueba**: 1W policristalino
- **Configuración de carga**: 150Ω + LED
- **Total de registros**: 600+ mediciones

## Estructura del Repositorio

iot-solar-monitoring-system/

├── firmware/ # Código ESP32 (Arduino)

├── hardware/ # Esquemáticos y PCB

├── dashboard/ # Interfaz web local

├── data_analysis/ # Scripts Python y Jupyter

├── docs/ # Documentación técnica

├── data/ # Datos recolectados (CSV)

└── images/ # Gráficas y fotos del sistema


## Hallazgos Clave

- Caracterización del comportamiento real vs teórico de paneles solares
- Identificación de condiciones ambientales óptimas para Bogotá
- Análisis de limitaciones de sensores comerciales (ACS712)
- Validación de arquitectura IoT para monitoreo prolongado

## Próximos Pasos

- Implementación de sensores de mayor precisión
- Extensión del estudio a diferentes tecnologías de panel
- Monitoreo estacional a largo plazo
- Desarrollo de modelos predictivos para la región andina

## Publicación

Este trabajo forma parte de la investigación:  
**"Diseño de un Sistema IoT para la Evaluación de Micro-Paneles Solares: Prueba de Concepto en Sistemas Energéticos Alternativos"**



