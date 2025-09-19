import streamlit as st
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import seaborn as sns
import folium
from folium.plugins import MarkerCluster
from shapely.geometry import Point
from streamlit_folium import st_folium


# Título del dashboard
st.title("Paradoja de Simpson")
st.write("Este dashboard demuestra cómo los datos agregados pueden ocultar correlaciones reales.")

# Cargar hospitales
df = pd.read_csv("data/hospitales.csv", encoding="latin1")

# Limpiar columnas y datos
df.columns = df.columns.str.strip()
df = df[df["Estado"] == "FUNCIONANDO"]
df = df.dropna(subset=["NORTE", "ESTE"])
df = df.rename(columns={"NORTE": "lat", "ESTE": "lon"})

# Verificar columna UBIGEO en hospitales
if "UBIGEO" not in df.columns:
    st.error("La columna 'UBIGEO' no existe en hospitales.csv. Verifica el nombre exacto.")
else:
    df = df.rename(columns={"UBIGEO": "IDDIST"})

# Cargar distritos desde shapefile
distritos = gpd.read_file("data/distritos/distritos.shp").to_crs("EPSG:4326")
distritos.columns = distritos.columns.str.strip()

# Verificar columna IDDIST en distritos
if "IDDIST" not in distritos.columns:
    st.error("La columna 'IDDIST' no existe en distritos.shp. Verifica el nombre exacto.")

# Agrupar hospitales por IDDIST
hospitales_por_distrito = df.groupby("IDDIST").size().reset_index(name="hospitales")

# Unir con shapefile
distritos = distritos.merge(hospitales_por_distrito, on="IDDIST", how="left")
distritos["hospitales"] = distritos["hospitales"].fillna(0)

# Mostrar tabla después del merge
st.subheader("Distritos con número de hospitales")
st.dataframe(distritos[["DISTRITO", "IDDIST", "hospitales"]].head())

# Mapa 1: Total hospitales por distrito
st.subheader("🗺️ Mapa 1: Total hospitales por distrito")
fig1, ax1 = plt.subplots(figsize=(10, 10))
distritos.plot(column="hospitales", cmap="Blues", legend=True, ax=ax1, edgecolor="black")
ax1.set_title("Total hospitales por distrito")
ax1.axis("off")
st.pyplot(fig1)

# Mapa 2: Distritos con cero hospitales
st.subheader("🗺️ Mapa 2: Distritos con cero hospitales")
distritos["sin_hospitales"] = distritos["hospitales"] == 0
fig2, ax2 = plt.subplots(figsize=(10, 10))
distritos.plot(color="lightgrey", ax=ax2, edgecolor="black")
distritos[distritos["sin_hospitales"]].plot(color="red", ax=ax2, edgecolor="black")
ax2.set_title("Distritos sin hospitales")
ax2.axis("off")
st.pyplot(fig2)

# Mapa 3: Top 10 distritos con más hospitales
st.subheader("🗺️ Mapa 3: Top 10 distritos con más hospitales")
top10 = distritos.sort_values("hospitales", ascending=False).head(10)
fig3, ax3 = plt.subplots(figsize=(10, 10))
distritos.plot(color="lightgrey", ax=ax3, edgecolor="black")
top10.plot(column="hospitales", cmap="OrRd", legend=True, ax=ax3, edgecolor="black")
ax3.set_title("Top 10 distritos con más hospitales")
ax3.axis("off")
st.pyplot(fig3)

# Título del dashboard
st.title("Análisis por Departamento")
st.write("Esta sección muestra el total de hospitales operativos por departamento.")

# Cargar hospitales
df = pd.read_csv("data/hospitales.csv", encoding="latin1")
df.columns = df.columns.str.strip()
df = df[df["Estado"] == "ACTIVADO"]
df = df.dropna(subset=["NORTE", "ESTE"])
df = df.rename(columns={"NORTE": "lat", "ESTE": "lon"})

# Verificar columna 'Departamento'
if "Departamento" not in df.columns:
    st.error("La columna 'Departamento' no existe en hospitales.csv. Verifica el nombre exacto.")

# Agrupar por Departamento
hospitales_por_departamento = df.groupby("Departamento").size().reset_index(name="hospitales")
hospitales_por_departamento = hospitales_por_departamento.sort_values("hospitales", ascending=False)

# Mostrar tabla ordenada
st.subheader("📊 Tabla: Total de hospitales por departamento")
st.dataframe(hospitales_por_departamento)

# Identificar extremos
if not hospitales_por_departamento.empty:
    max_dep = hospitales_por_departamento.iloc[0]
    min_dep = hospitales_por_departamento.iloc[-1]

    st.markdown(f"🟢 **Departamento con más hospitales:** {max_dep['Departamento']} ({max_dep['hospitales']})")
    st.markdown(f"🔴 **Departamento con menos hospitales:** {min_dep['Departamento']} ({min_dep['hospitales']})")
else:
    st.warning("No se encontraron hospitales operativos por departamento.")

# Gráfico de barras
if not hospitales_por_departamento.empty:
    st.subheader("📈 Gráfico de barras: hospitales por departamento")
    fig_bar, ax_bar = plt.subplots(figsize=(12, 6))
    sns.barplot(data=hospitales_por_departamento, x="hospitales", y="Departamento", palette="viridis", ax=ax_bar)
    ax_bar.set_title("Total de hospitales operativos por departamento")
    ax_bar.set_xlabel("Número de hospitales")
    ax_bar.set_ylabel("Departamento")
    st.pyplot(fig_bar)


# Título
st.title("Análisis de Proximidad: Lima y Loreto")
st.write("Este análisis identifica centros poblados con más y menos hospitales cercanos en un radio de 10 km.")


# Cargar hospitales
df = pd.read_csv("data/hospitales.csv", encoding="latin1")
df.columns = df.columns.str.strip()
df = df[df["Estado"] == "ACTIVADO"]
df = df.dropna(subset=["NORTE", "ESTE"])
df = df.rename(columns={"NORTE": "lat", "ESTE": "lon"})
df["geometry"] = df.apply(lambda row: Point(row["lon"], row["lat"]), axis=1)
hospitales = gpd.GeoDataFrame(df, geometry="geometry", crs="EPSG:4326")

# Cargar centros poblados
centros = gpd.read_file("data/centros_poblados/CCPP_IGN100K.shp").to_crs("EPSG:4326")
centros.columns = centros.columns.str.strip()

# Verificar columnas necesarias
if "DEP" not in centros.columns or "NOM_POBLAD" not in centros.columns:
    st.error("El shapefile debe tener las columnas 'DEP' y 'NOM_POBLAD'.")

# Filtrar Lima y Loreto
centros = centros[centros["DEP"].isin(["LIMA", "LORETO"])]

# Calcular centroides si son polígonos
if centros.geometry.geom_type.isin(["Polygon", "MultiPolygon"]).any():
    centros["centroide"] = centros.geometry.centroid
else:
    centros["centroide"] = centros.geometry

# Reproyectar a EPSG:32718 para medir en metros
centros_proj = centros.set_geometry("centroide").to_crs("EPSG:32718")
hospitales_proj = hospitales.to_crs("EPSG:32718")

# Crear buffers de 10 km
centros_proj["buffer"] = centros_proj.geometry.buffer(10000)

# Contar hospitales dentro de cada buffer
hospitales_por_buffer = []
for i, centro in centros_proj.iterrows():
    dentro = hospitales_proj[hospitales_proj.within(centro["buffer"])]
    hospitales_por_buffer.append(len(dentro))

centros["hospitales_cercanos"] = hospitales_por_buffer

# Identificar extremos por región
resultados = []
for region in ["LIMA", "LORETO"]:
    subset = centros[centros["DEP"] == region]
    if not subset.empty:
        aislado = subset.loc[subset["hospitales_cercanos"].idxmin()]
        concentrado = subset.loc[subset["hospitales_cercanos"].idxmax()]
        resultados.append((region, aislado, concentrado))

# Mostrar resultados y mapas
for region, aislado, concentrado in resultados:
    st.subheader(f"📍 Región: {region}")
    st.markdown(f"🔴 Centro poblado más aislado: **{aislado['NOM_POBLAD']}** ({aislado['hospitales_cercanos']} hospitales cercanos)")
    st.markdown(f"🟢 Centro poblado más concentrado: **{concentrado['NOM_POBLAD']}** ({concentrado['hospitales_cercanos']} hospitales cercanos)")

    # Crear mapa Folium
    m = folium.Map(location=[aislado["centroide"].y, aislado["centroide"].x], zoom_start=10)

    # Añadir buffer
    folium.Circle(
        location=[aislado["centroide"].y, aislado["centroide"].x],
        radius=10000,
        color="blue",
        fill=True,
        fill_opacity=0.2,
        popup="Buffer 10 km"
    ).add_to(m)

    # Añadir centro poblado
    folium.Marker(
        location=[aislado["centroide"].y, aislado["centroide"].x],
        popup=f"{aislado['NOM_POBLAD']} (aislado)",
        icon=folium.Icon(color="red")
    ).add_to(m)

    # Añadir hospitales dentro del buffer
    buffer_geom = centros_proj.loc[aislado.name, "buffer"]
    hospitales_dentro = hospitales_proj[hospitales_proj.within(buffer_geom)].to_crs("EPSG:4326")

    for _, hosp in hospitales_dentro.iterrows():
        folium.CircleMarker(
            location=[hosp.geometry.y, hosp.geometry.x],
            radius=4,
            color="green",
            fill=True,
            fill_opacity=0.7,
            popup=hosp["Nombre"]
        ).add_to(m)
        # Título

# Título
st.title("🗺️ Task 1: Mapa Interactivo Nacional")
st.write("Este mapa muestra la distribución de hospitales operativos por distrito y su ubicación geográfica.")

# Cargar hospitales
df = pd.read_csv("data/hospitales.csv", encoding="latin1")
df.columns = df.columns.str.strip()
df = df[df["Estado"] == "ACTIVADO"]
df = df.dropna(subset=["NORTE", "ESTE"])
df = df.rename(columns={"NORTE": "lat", "ESTE": "lon"})
df["geometry"] = df.apply(lambda row: Point(row["lon"], row["lat"]), axis=1)
hospitales = gpd.GeoDataFrame(df, geometry="geometry", crs="EPSG:4326")


# Cargar distritos
distritos = gpd.read_file("data/distritos/distritos.shp").to_crs("EPSG:4326")
distritos.columns = distritos.columns.str.strip()

# Asegurar que IDDIST esté en formato string
hospitales["UBIGEO"] = hospitales["UBIGEO"].astype(str)
distritos["IDDIST"] = distritos["IDDIST"].astype(str)

# Agrupar hospitales por distrito
hospitales_por_distrito = hospitales.groupby("UBIGEO").size().reset_index(name="hospitales")

# Unir con shapefile
distritos = distritos.merge(hospitales_por_distrito, left_on="IDDIST", right_on="UBIGEO", how="left")
distritos["hospitales"] = distritos["hospitales"].fillna(0)

# Crear mapa base centrado en Perú
m = folium.Map(location=[-9.19, -75.015], zoom_start=5)

# Choropleth por distrito
folium.Choropleth(
    geo_data=distritos,
    name="Choropleth",
    data=distritos,
    columns=["IDDIST", "hospitales"],
    key_on="feature.properties.IDDIST",
    fill_color="YlOrRd",
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name="Hospitales operativos por distrito"
).add_to(m)

# Cluster de hospitales
cluster = MarkerCluster(name="Hospitales")
for _, hosp in hospitales.iterrows():
    folium.Marker(
        location=[hosp.geometry.y, hosp.geometry.x],
        popup=hosp["Nombre del establecimiento"],
        icon=folium.Icon(color="green", icon="plus-sign")
    ).add_to(cluster)
cluster.add_to(m)

# Controles
folium.LayerControl().add_to(m)

# Mostrar en Streamlit
st.subheader("🗺️ Mapa interactivo nacional")
st_folium(m, width=800, height=600)

st.title("📍 Task 2: Visualización de Proximidad — Lima & Loreto")
st.write("Este mapa muestra los centros poblados con mayor y menor acceso a hospitales en un radio de 10 km.")

# Cargar hospitales
df = pd.read_csv("data/hospitales.csv", encoding="latin1") 
df.columns = df.columns.str.strip() 
df = df[df["Estado"] == "ACTIVADO"] 
df = df.dropna(subset=["NORTE", "ESTE"]) 
df = df.rename(columns={"NORTE": "lat", "ESTE": "lon"}) 
df["geometry"] = df.apply(lambda row: Point(row["lon"], row["lat"]), axis=1) 
hospitales = gpd.GeoDataFrame(df, geometry="geometry", crs="EPSG:4326")

# Cargar centros poblados
centros = gpd.read_file("data/centros_poblados/CCPP_IGN100K.shp").to_crs("EPSG:4326")
centros.columns = centros.columns.str.strip()

# Filtrar Lima y Loreto
centros = centros[centros["DEP"].isin(["LIMA", "LORETO"])]

# Calcular centroides si son polígonos
if centros.geometry.geom_type.isin(["Polygon", "MultiPolygon"]).any():
    centros["centroide"] = centros.geometry.centroid
else:
    centros["centroide"] = centros.geometry

# Reproyectar a EPSG:32718 para medir en metros
centros_proj = centros.set_geometry("centroide").to_crs("EPSG:32718")
hospitales_proj = hospitales.to_crs("EPSG:32718")

# Crear buffers de 10 km
centros_proj["buffer"] = centros_proj.geometry.buffer(10000)

# Contar hospitales dentro de cada buffer
hospitales_por_buffer = []
for i, centro in centros_proj.iterrows():
    dentro = hospitales_proj[hospitales_proj.within(centro["buffer"])]
    hospitales_por_buffer.append(len(dentro))

centros["hospitales_cercanos"] = hospitales_por_buffer

# Identificar extremos por región
resultados = []
for region in ["LIMA", "LORETO"]:
    subset = centros[centros["DEP"] == region]
    if not subset.empty:
        aislado = subset.loc[subset["hospitales_cercanos"].idxmin()]
        concentrado = subset.loc[subset["hospitales_cercanos"].idxmax()]
        resultados.append((region, aislado, concentrado))

# Mostrar resultados y mapas
for region, aislado, concentrado in resultados:
    st.subheader(f"📍 Región: {region}")
    st.markdown(f"🔴 Centro poblado más aislado: **{aislado['NOM_POBLAD']}** ({aislado['hospitales_cercanos']} hospitales cercanos)")
    st.markdown(f"🟢 Centro poblado más concentrado: **{concentrado['NOM_POBLAD']}** ({concentrado['hospitales_cercanos']} hospitales cercanos)")

    # Crear mapa Folium
    m = folium.Map(location=[aislado["centroide"].y, aislado["centroide"].x], zoom_start=10)

    # Círculo rojo (aislado)
    folium.Circle(
        location=[aislado["centroide"].y, aislado["centroide"].x],
        radius=10000,
        color="red",
        fill=True,
        fill_opacity=0.3,
        tooltip=f"{aislado['NOM_POBLAD']} (aislado)\n{aislado['hospitales_cercanos']} hospitales"
    ).add_to(m)

    # Círculo verde (concentrado)
    folium.Circle(
        location=[concentrado["centroide"].y, concentrado["centroide"].x],
        radius=10000,
        color="green",
        fill=True,
        fill_opacity=0.3,
        tooltip=f"{concentrado['NOM_POBLAD']} (concentrado)\n{concentrado['hospitales_cercanos']} hospitales"
    ).add_to(m)

    st_folium(m, width=800, height=600)

# Análisis escrito
st.subheader("📝 Análisis de accesibilidad")
st.markdown("""
**Lima:**  
La alta concentración urbana facilita el acceso a servicios de salud. Los centros poblados con mayor densidad hospitalaria se ubican en zonas metropolitanas, reflejando una infraestructura más desarrollada y conectividad eficiente.

**Loreto:**  
La dispersión geográfica en la Amazonía presenta desafíos significativos. Muchos centros poblados están aislados, con escasa cobertura hospitalaria en un radio de 10 km, lo que evidencia barreras de accesibilidad por distancia, transporte y geografía.
""")