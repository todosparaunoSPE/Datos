# -*- coding: utf-8 -*-
"""
Created on Fri Dec 20 11:35:34 2024

@author: jperezr
"""


import streamlit as st
import pandas as pd
import numpy as np
from statsmodels.tsa.holtwinters import ExponentialSmoothing
import plotly.express as px
import plotly.graph_objects as go
from scipy.stats import norm

# Cargar automáticamente el archivo ponderado.xlsx
archivo = 'ponderado.xlsx'

@st.cache_data
def cargar_datos(archivo):
    return pd.read_excel(archivo, sheet_name='Hoja1')

# Leer los datos del archivo
datos = cargar_datos(archivo)

# Título de la aplicación
st.title("Análisis de datos")

# Sección de ayuda en la barra lateral
st.sidebar.header("Ayuda")
st.sidebar.write("""
    Este aplicativo permite realizar un análisis de datos provenientes de un archivo Excel".
    Se pueden visualizar los datos completos, filtrarlos por la columna "Consecutivo", y graficar las series de tiempo.
    Además, se pueden aplicar diferentes modelos de ajuste a los datos, como la media móvil, el suavizado exponencial y los modelos Holt-Winters (aditivo y multiplicativo).
    También se muestra una proyección de los datos con intervalos de confianza.
    
    Creado por: **Javier Horacio Pérez Ricárdez**
""")

# Mostrar el DataFrame completo
st.header("Datos completos")
st.dataframe(datos)

# Crear un multiselect para filtrar por columna "Consecutivo"
st.header("Filtrar por Consecutivo")
opciones = datos['Consecutivo'].dropna().unique()
seleccion = st.multiselect("Selecciona uno o más Consecutivos", opciones)

# Filtrar los datos por la selección múltiple
if seleccion:
    datos_filtrados = datos[datos['Consecutivo'].isin(seleccion)]
else:
    datos_filtrados = datos  # Si no hay selección, mostrar todos los datos

# Mostrar el DataFrame filtrado
st.header("Datos filtrados")
st.dataframe(datos_filtrados)

# Graficar automáticamente todas las columnas excepto "Consecutivo"
st.header("Gráfica")
if seleccion:
    datos_long = datos_filtrados.melt(
        id_vars=["Consecutivo"], 
        value_vars=datos.columns[1:], 
        var_name="Mes", 
        value_name="Valor"
    )
    fig = px.line(
        datos_long,
        x="Mes",
        y="Valor",
        color="Consecutivo",
        markers=True,
        title="Gráfica de puntos unidos por líneas"
    )
    st.plotly_chart(fig)
else:
    st.info("Selecciona al menos un Consecutivo para graficar.")

# Selección del modelo para ajuste
st.header("Ajuste de Modelos")
modelos = ["Media móvil", "Suavizado exponencial", "Holt-Winters Aditivo", "Holt-Winters Multiplicativo"]
modelo_seleccionado = st.selectbox("Selecciona un modelo para ajustar los datos", modelos)

# Ajustar los datos según el modelo seleccionado
if seleccion:
    # Datos para ajuste
    datos_modelo = datos_filtrados.iloc[:, 1:].mean(axis=0).reset_index()
    datos_modelo.columns = ['Mes', 'Valor']
    datos_modelo['Mes'] = pd.to_datetime(datos_modelo['Mes'], errors='coerce')

    if modelo_seleccionado == "Media móvil":
        datos_modelo['Ajuste'] = datos_modelo['Valor'].rolling(window=3, min_periods=1).mean()

    elif modelo_seleccionado == "Suavizado exponencial":
        modelo = ExponentialSmoothing(datos_modelo['Valor']).fit(smoothing_level=0.2, optimized=False)
        datos_modelo['Ajuste'] = modelo.fittedvalues

    elif modelo_seleccionado == "Holt-Winters Aditivo":
        modelo = ExponentialSmoothing(datos_modelo['Valor'], trend='add', seasonal='add', seasonal_periods=12).fit()
        datos_modelo['Ajuste'] = modelo.fittedvalues

    elif modelo_seleccionado == "Holt-Winters Multiplicativo":
        modelo = ExponentialSmoothing(datos_modelo['Valor'], trend='mul', seasonal='mul', seasonal_periods=12).fit()
        datos_modelo['Ajuste'] = modelo.fittedvalues

    # Cálculo de los residuos y el error estándar
    residuos = datos_modelo['Valor'] - datos_modelo['Ajuste']
    error_estandar = residuos.std()

    # Cálculo del intervalo de confianza (95%)
    z_score = norm.ppf(0.975)  # Para un intervalo de confianza del 95%
    margen_error = z_score * error_estandar
    intervalo_inferior = datos_modelo['Ajuste'] - margen_error
    intervalo_superior = datos_modelo['Ajuste'] + margen_error

    # Graficar con los resultados de ajuste y el intervalo de confianza
    fig_ajuste = go.Figure()
    fig_ajuste.add_trace(go.Scatter(x=datos_modelo['Mes'], y=datos_modelo['Valor'], mode='markers+lines', name='Datos reales'))
    fig_ajuste.add_trace(go.Scatter(x=datos_modelo['Mes'], y=datos_modelo['Ajuste'], mode='lines', name='Ajuste'))
    fig_ajuste.add_trace(go.Scatter(x=datos_modelo['Mes'], y=intervalo_inferior, mode='lines', name='Intervalo Inferior', line=dict(dash='dash', color='gray')))
    fig_ajuste.add_trace(go.Scatter(x=datos_modelo['Mes'], y=intervalo_superior, mode='lines', name='Intervalo Superior', line=dict(dash='dash', color='gray')))
    fig_ajuste.update_layout(title=f"Datos reales vs Ajuste con Intervalos de Confianza ({modelo_seleccionado})", xaxis_title="Mes", yaxis_title="Valor")
    st.plotly_chart(fig_ajuste)

    # Proyección a dic-24, ene-25, feb-25, mar-25, abr-25
    proyeccion_fechas = pd.to_datetime(['2024-12-01', '2025-01-01', '2025-02-01', '2025-03-01', '2025-04-01'])
    
    # Ajustar el modelo seleccionado para la proyección
    if modelo_seleccionado == "Media móvil":
        proyeccion = datos_modelo['Valor'].rolling(window=3, min_periods=1).mean().iloc[-1]
        proyeccion = [proyeccion] * len(proyeccion_fechas)

    elif modelo_seleccionado == "Suavizado exponencial":
        proyeccion = modelo.forecast(len(proyeccion_fechas))

    elif modelo_seleccionado == "Holt-Winters Aditivo":
        proyeccion = modelo.forecast(len(proyeccion_fechas))

    elif modelo_seleccionado == "Holt-Winters Multiplicativo":
        proyeccion = modelo.forecast(len(proyeccion_fechas))

    # Graficar proyección con intervalo de confianza
    proyeccion_inferior = proyeccion - margen_error
    proyeccion_superior = proyeccion + margen_error

    fig_proyeccion = go.Figure()
    fig_proyeccion.add_trace(go.Scatter(x=datos_modelo['Mes'], y=datos_modelo['Valor'], mode='markers+lines', name='Datos reales'))
    fig_proyeccion.add_trace(go.Scatter(x=proyeccion_fechas, y=proyeccion, mode='lines+markers', name=f'Proyección ({modelo_seleccionado})', line=dict(dash='dot', color='red')))
    fig_proyeccion.add_trace(go.Scatter(x=proyeccion_fechas, y=proyeccion_inferior, mode='lines', name='Proyección Inferior', line=dict(dash='dash', color='gray')))
    fig_proyeccion.add_trace(go.Scatter(x=proyeccion_fechas, y=proyeccion_superior, mode='lines', name='Proyección Superior', line=dict(dash='dash', color='gray')))
    fig_proyeccion.update_layout(title=f"Ajuste con Proyección y Intervalos de Confianza ({modelo_seleccionado})", xaxis_title="Mes", yaxis_title="Valor")
    st.plotly_chart(fig_proyeccion)

    # Crear el DataFrame con los datos de proyección e intervalos de confianza
    datos_completos = pd.DataFrame({
        'Mes': pd.concat([datos_modelo['Mes'], pd.Series(proyeccion_fechas)]).reset_index(drop=True),
        'Valor Real': pd.concat([datos_modelo['Valor'], pd.Series([None]*len(proyeccion_fechas))]).reset_index(drop=True),
        'Proyección': pd.concat([pd.Series([None]*len(datos_modelo)), pd.Series(proyeccion)]).reset_index(drop=True),
        'Intervalo Inferior': pd.concat([pd.Series([None]*len(datos_modelo)), pd.Series(proyeccion_inferior)]).reset_index(drop=True),
        'Intervalo Superior': pd.concat([pd.Series([None]*len(datos_modelo)), pd.Series(proyeccion_superior)]).reset_index(drop=True),
    })

    # Mostrar los datos con las proyecciones e intervalos de confianza
    st.header(f"Datos completos con Proyección e Intervalos de Confianza ({modelo_seleccionado})")
    st.dataframe(datos_completos)