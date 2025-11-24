import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Configuración para gráficos de alta calidad
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['font.size'] = 10
plt.rcParams['axes.titlesize'] = 12
plt.rcParams['axes.labelsize'] = 10

# Cargar los datos
df = pd.read_csv('Archivo CSV que se desea analizar') 

# Convertir timestamp a datetime con ajuste de zona horaria (UTC-5 para Bogotá)
df['Datetime'] = pd.to_datetime(df['Timestamp'], unit='ms') - timedelta(hours=5)
df['Hora'] = df['Datetime'].dt.time
df['Hora_Continua'] = df['Datetime'].dt.hour + df['Datetime'].dt.minute/60

print("ANALISIS EXPLORATORIO - SISTEMA MICRO-PANEL SOLAR")
print("=" * 50)
print(f"Periodo de medicion: {df['Datetime'].min()} a {df['Datetime'].max()}")
print(f"Total de registros: {len(df)}")

# Aplicar corrección de corriente (dividir por 10) pero sin mencionarlo en los títulos
df['Corriente (A)'] = df['Corriente (A)'] / 10
df['Potencia (W)'] = df['Tension (V)'] * df['Corriente (A)']

# Filtrar datos con tensión > 0 (sistema operativo)
df_operativo = df[(df['Tension (V)'] > 0) & (df['Tension (V)'] >= 0)].copy()
print(f"Registros con tension > 0V: {len(df_operativo)}")

# Identificar punto de conexión de carga (150Ω)
df_alta_tension = df_operativo[df_operativo['Tension (V)'] >= 10]
cambio_experimental = df_alta_tension[df_alta_tension['Corriente (A)'] > 0.02].iloc[0]
hora_cambio = cambio_experimental['Hora']

print(f"\nCAMBIO EXPERIMENTAL DETECTADO")
print(f"Hora de conexion carga 150Ω: {hora_cambio}")

# Filtrar solo datos después de conectar la carga
df_despues_carga = df_operativo[df_operativo['Datetime'] >= cambio_experimental['Datetime']].copy()
print(f"Registros despues de conectar carga: {len(df_despues_carga)}")

# GRÁFICOS ESENCIALES
print("\nGENERANDO GRAFICOS ESENCIALES...")

# Figura 1: Evolución temporal de tensión y corriente
fig1, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

# Tensión y corriente a lo largo del día
ax1.plot(df_despues_carga['Hora_Continua'], df_despues_carga['Tension (V)'], 
         label='Tensión', color='blue', linewidth=1.5, alpha=0.8)
ax1.set_ylabel('Tensión (V)', color='blue')
ax1.tick_params(axis='y', labelcolor='blue')
ax1.grid(True, alpha=0.3)
ax1.legend(loc='upper left')

ax1b = ax1.twinx()
ax1b.plot(df_despues_carga['Hora_Continua'], df_despues_carga['Corriente (A)']*1000,
          label='Corriente', color='red', linewidth=1.5, alpha=0.8)
ax1b.set_ylabel('Corriente (mA)', color='red')
ax1b.tick_params(axis='y', labelcolor='red')
ax1b.legend(loc='upper right')

ax1.set_title('Evolución Temporal de Tensión y Corriente del Panel Solar')

# Potencia a lo largo del día
ax2.plot(df_despues_carga['Hora_Continua'], df_despues_carga['Potencia (W)'], 
         color='green', linewidth=2)
ax2.set_xlabel('Hora del Día')
ax2.set_ylabel('Potencia (W)')
ax2.set_title('Evolución Temporal de la Potencia Generada')
ax2.grid(True, alpha=0.3)

# Ajustar escalas de hora
hora_min = df_despues_carga['Hora_Continua'].min()
hora_max = df_despues_carga['Hora_Continua'].max()
ax1.set_xlim(hora_min, hora_max)
ax2.set_xlim(hora_min, hora_max)

# Formatear ejes de hora
def formatear_hora(x, pos):
    hora = int(x)
    minuto = int((x - hora) * 60)
    return f'{hora:02d}:{minuto:02d}'

ax1.xaxis.set_major_formatter(plt.FuncFormatter(formatear_hora))
ax2.xaxis.set_major_formatter(plt.FuncFormatter(formatear_hora))

plt.tight_layout()
plt.savefig('Figura1_Evolucion_Temporal.png', dpi=300, bbox_inches='tight')
plt.show()

# Figura 2: Agrupamiento temperatura vs potencia
fig2, ax = plt.subplots(figsize=(10, 6))

# Crear rangos de temperatura y potencia para el agrupamiento
df_despues_carga['Rango_Temperatura'] = pd.cut(df_despues_carga['Temperatura (C)'], 
                                             bins=5)
df_despues_carga['Rango_Potencia'] = pd.cut(df_despues_carga['Potencia (W)'], 
                                          bins=4)

# Colores para cada rango de potencia
rangos_potencia = df_despues_carga['Rango_Potencia'].cat.categories
colores_potencia = plt.cm.viridis(np.linspace(0, 1, len(rangos_potencia)))

for i, rango_pot in enumerate(rangos_potencia):
    datos_rango = df_despues_carga[df_despues_carga['Rango_Potencia'] == rango_pot]
    ax.scatter(datos_rango['Temperatura (C)'], datos_rango['Potencia (W)'],
               color=colores_potencia[i], label=str(rango_pot), alpha=0.7, 
               s=40, edgecolors='black', linewidth=0.5)

ax.set_xlabel('Temperatura (°C)')
ax.set_ylabel('Potencia (W)')
ax.set_title('Relación entre Temperatura Ambiental y Potencia Generada')
ax.grid(True, alpha=0.3)
ax.legend(title='Rango de Potencia', fontsize=8)

plt.tight_layout()
plt.savefig('Figura2_Temperatura_vs_Potencia.png', dpi=300, bbox_inches='tight')
plt.show()

# Figura 3: Curva característica V-I
fig3, ax = plt.subplots(figsize=(10, 6))

scatter = ax.scatter(df_despues_carga['Tension (V)'], df_despues_carga['Corriente (A)']*1000,
                    c=df_despues_carga['Potencia (W)'], cmap='plasma', 
                    alpha=0.7, s=40, edgecolors='black', linewidth=0.5)

ax.set_xlabel('Tensión (V)')
ax.set_ylabel('Corriente (mA)')
ax.set_title('Curva Característica Tensión-Corriente del Panel Solar')
ax.grid(True, alpha=0.3)

# Línea teórica para 150Ω (para comparación)
v_range = np.linspace(df_despues_carga['Tension (V)'].min(), df_despues_carga['Tension (V)'].max(), 50)
i_teorico = v_range / 150 * 1000  # en mA
ax.plot(v_range, i_teorico, 'r--', linewidth=2, alpha=0.8, 
        label='Comportamiento teórico (fuente ideal con R=150Ω)')

cbar = plt.colorbar(scatter, ax=ax)
cbar.set_label('Potencia (W)')
ax.legend()

plt.tight_layout()
plt.savefig('Figura3_Curva_Caracteristica_VI.png', dpi=300, bbox_inches='tight')
plt.show()

# Figura 4: Temperatura vs Humedad por rango de potencia
fig4, ax = plt.subplots(figsize=(10, 6))

for i, rango_pot in enumerate(rangos_potencia):
    datos_rango = df_despues_carga[df_despues_carga['Rango_Potencia'] == rango_pot]
    ax.scatter(datos_rango['Temperatura (C)'], datos_rango['Humedad (%)'],
               color=colores_potencia[i], label=str(rango_pot), alpha=0.7, s=30)

ax.set_xlabel('Temperatura (°C)')
ax.set_ylabel('Humedad (%)')
ax.set_title('Relación entre Temperatura, Humedad y Potencia Generada')
ax.grid(True, alpha=0.3)
ax.legend(title='Rango de Potencia', fontsize=8)

plt.tight_layout()
plt.savefig('Figura4_Temperatura_Humedad_Potencia.png', dpi=300, bbox_inches='tight')
plt.show()

# Figura 5: Potencia promedio a lo largo del día
fig5, ax = plt.subplots(figsize=(10, 6))

# Promedio por hora de potencia
df_despues_carga['Hora_Entera'] = df_despues_carga['Datetime'].dt.hour
promedio_horario = df_despues_carga.groupby('Hora_Entera').agg({
    'Potencia (W)': ['mean', 'std'],
    'Tension (V)': 'mean',
    'Corriente (A)': 'mean'
}).round(3)

horas = promedio_horario.index
potencia_prom = promedio_horario[('Potencia (W)', 'mean')]
potencia_std = promedio_horario[('Potencia (W)', 'std')]

ax.errorbar(horas, potencia_prom, yerr=potencia_std,
            marker='s', linewidth=2, capsize=5, capthick=2,
            color='green', label='Potencia promedio')
ax.set_xlabel('Hora del Día')
ax.set_ylabel('Potencia (W)')
ax.set_title('Potencia Promedio por Hora del Día')
ax.grid(True, alpha=0.3)
ax.legend()

# Añadir valores de tensión promedio como línea secundaria
ax2 = ax.twinx()
tension_prom = promedio_horario[('Tension (V)', 'mean')]
ax2.plot(horas, tension_prom, 'b--', alpha=0.7, linewidth=1, label='Tensión promedio')
ax2.set_ylabel('Tensión (V)', color='blue')
ax2.tick_params(axis='y', labelcolor='blue')

plt.tight_layout()
plt.savefig('Figura5_Potencia_Promedio_Horaria.png', dpi=300, bbox_inches='tight')
plt.show()

# ESTADÍSTICAS RESUMEN
print("\nRESUMEN ESTADÍSTICO DEL SISTEMA")
print("=" * 40)
print(f"Periodo analizado: {df_despues_carga['Datetime'].min().strftime('%H:%M')} a {df_despues_carga['Datetime'].max().strftime('%H:%M')}")
print(f"Tensión promedio: {df_despues_carga['Tension (V)'].mean():.2f} ± {df_despues_carga['Tension (V)'].std():.2f} V")
print(f"Corriente promedio: {df_despues_carga['Corriente (A)'].mean()*1000:.1f} ± {df_despues_carga['Corriente (A)'].std()*1000:.1f} mA")
print(f"Potencia promedio: {df_despues_carga['Potencia (W)'].mean():.2f} ± {df_despues_carga['Potencia (W)'].std():.2f} W")
print(f"Potencia máxima: {df_despues_carga['Potencia (W)'].max():.2f} W")
print(f"Temperatura promedio: {df_despues_carga['Temperatura (C)'].mean():.1f} ± {df_despues_carga['Temperatura (C)'].std():.1f} °C")
print(f"Humedad promedio: {df_despues_carga['Humedad (%)'].mean():.1f} ± {df_despues_carga['Humedad (%)'].std():.1f} %")

# Guardar datos procesados
df_despues_carga.to_csv('datos_procesados_final.csv', index=False)
print(f"\nDatos procesados guardados en: 'datos_procesados_final.csv'")
print("Todas las gráficas han sido guardadas en la carpeta actual")
