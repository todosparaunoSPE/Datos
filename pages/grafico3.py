# -*- coding: utf-8 -*-
"""
Created on Mon Dec 23 18:55:16 2024

@author: jperezr
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import os

# Título de la aplicación
st.title("Visualización de Resultados de las AFORE")

# Ruta del archivo predeterminado
default_file = "resultados.xlsx"

# Cargar automáticamente si el archivo existe
if os.path.exists(default_file):
    uploaded_file = default_file
    st.info(f"Se cargó automáticamente el archivo: {default_file}")
else:
    # Subir el archivo manualmente si no existe el archivo predeterminado
    uploaded_file = st.file_uploader("Carga el archivo Excel con los resultados", type=["xlsx"])

if uploaded_file is not None:
    try:
        # Leer el archivo Excel
        df = pd.read_excel(uploaded_file, sheet_name="Hoja1")

        # Limpiar nombres de columnas
        df.columns = df.columns.str.strip()  # Eliminar espacios en blanco
        df.columns = df.columns.str.replace("\s+", "_", regex=True)  # Reemplazar espacios con guiones bajos
        df.columns = df.columns.str.upper()  # Convertir a mayúsculas para evitar discrepancias

        # Verificar si las columnas requeridas están presentes
        required_columns = ["AFORE", "FECHA", "VALOR_REAL", "PROYECCION"]
        if all(col in df.columns for col in required_columns):
            # Convertir la columna de fechas a tipo datetime si es necesario
            df["FECHA"] = pd.to_datetime(df["FECHA"])

            # Mostrar el DataFrame completo al inicio
            st.subheader("Datos cargados")
            st.dataframe(df)

            # Crear un selectbox de múltiples selecciones para las AFORE
            afore_list = df["AFORE"].unique()
            selected_afore = st.multiselect("Selecciona las AFORE para visualizar:", afore_list, default=afore_list)

            # Filtrar el DataFrame con las AFORE seleccionadas
            filtered_df = df[df["AFORE"].isin(selected_afore)]

            # Crear un DataFrame separado para gráficas de "VALOR_REAL" y "PROYECCION"
            plot_data = pd.DataFrame()

            for afore in selected_afore:
                temp = filtered_df[filtered_df["AFORE"] == afore]
                real_data = temp.iloc[:5][["FECHA", "VALOR_REAL"]].copy()  # Primeras 5 filas (VALOR_REAL)
                real_data["TIPO"] = "VALOR_REAL"
                real_data["VALOR"] = real_data["VALOR_REAL"]
                real_data["AFORE"] = afore

                projected_data = temp.iloc[5:10][["FECHA", "PROYECCION"]].copy()  # Siguientes 5 filas (PROYECCION)
                projected_data["TIPO"] = "PROYECCION"
                projected_data["VALOR"] = projected_data["PROYECCION"]
                projected_data["AFORE"] = afore

                # Combinar en el DataFrame para graficar
                combined_data = pd.concat([real_data[["FECHA", "VALOR", "TIPO", "AFORE"]], 
                                           projected_data[["FECHA", "VALOR", "TIPO", "AFORE"]]])
                plot_data = pd.concat([plot_data, combined_data])

            # Crear gráficos individuales para "VALOR_REAL" y "PROYECCION"
            if not plot_data.empty:
                # Datos reales
                real_data_plot = plot_data[plot_data["TIPO"] == "VALOR_REAL"]
                fig_real = px.line(
                    real_data_plot,
                    x="FECHA",
                    y="VALOR",
                    color="AFORE",
                    markers=True,
                    labels={"VALOR": "Valor Real", "FECHA": "Fecha"},
                    title="Valores Reales por AFORE"
                )
                fig_real.update_layout(xaxis=dict(tickmode='array', tickvals=real_data_plot["FECHA"].unique()))
                st.plotly_chart(fig_real)

                # Datos proyectados
                projected_data_plot = plot_data[plot_data["TIPO"] == "PROYECCION"]
                fig_projected = px.line(
                    projected_data_plot,
                    x="FECHA",
                    y="VALOR",
                    color="AFORE",
                    markers=True,
                    labels={"VALOR": "Proyección", "FECHA": "Fecha"},
                    title="Proyecciones por AFORE"
                )
                fig_projected.update_layout(xaxis=dict(tickmode='array', tickvals=projected_data_plot["FECHA"].unique()))
                st.plotly_chart(fig_projected)

                # Datos reales y proyectados juntos
                fig_combined = px.line(
                    plot_data,
                    x="FECHA",
                    y="VALOR",
                    color="AFORE",
                    markers=True,
                    line_dash="TIPO",  # Diferenciar por tipo de línea
                    labels={"VALOR": "Valor", "FECHA": "Fecha"},
                    title="Datos Reales y Proyecciones por AFORE"
                )
                fig_combined.update_layout(xaxis=dict(tickmode='array', tickvals=plot_data["FECHA"].unique()))
                st.plotly_chart(fig_combined)

            else:
                st.warning("No hay datos para mostrar en la gráfica.")
        else:
            st.error(f"El archivo no contiene las columnas requeridas: {', '.join(required_columns)}")
    except Exception as e:
        st.error(f"Hubo un error al procesar el archivo: {e}")
else:
    st.info("Por favor, sube un archivo Excel para comenzar.")