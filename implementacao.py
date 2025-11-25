import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ==============================================
# CONFIGURAÇÃO GERAL
# ==============================================
st.set_page_config(
    page_title="Dashboard Estudos e CNES",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================================
# ESTILO GLOBAL
# ==============================================
st.markdown("""
    <style>
        .main {background-color: #F8FAFC;}

        .title-box {
            background: linear-gradient(90deg, #5B21B6, #3AAFA9);
            border-radius: 15px;
            padding: 25px;
            text-align: center;
            margin-bottom: 35px;
            color: white;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        .title-box h1 {
            font-size: 46px;
            font-weight: 800;
            margin: 0;
            color: white;
        }

        .centered-title {
            text-align: center;
            font-weight: 700;
            color: #1E3A8A;
            margin-top: 5px;
            margin-bottom: -10px; /* aproxima o gráfico */
            font-size: 20px;
        }
        
        .filter-box {
            background: #ffffff;
            border: 2px solid #5B21B620;
            border-radius: 12px;
            padding: 15px 25px;
            margin-bottom: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }
        .metric-box {
            background: linear-gradient(135deg, #5B21B6, #3AAFA9);
            border-radius: 12px;
            padding: 20px 15px;
            text-align: center;
            color: white;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        .metric-label {
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 8px;
        }
        .metric-value {
            font-size: 36px;
            font-weight: 800;
        }
        h3 {color: #1E3A8A; font-weight: 700; margin-top: 25px;}
        footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)



# ==============================================
# TÍTULO
# ==============================================
st.markdown("""
<div class='title-box'>
    <h1>Estudos Clínicos em Oncologia X Unidades de Saúde (CNES)</h1>
</div>
""", unsafe_allow_html=True)

# ==============================================
# CARREGAR E PADRONIZAR DADOS
# ==============================================
@st.cache_data
def load_data():
    estudos = pd.read_csv("estudos_tratados.csv")
    cnes = pd.read_csv("cidades_tratadas.csv")

    estudos = estudos.rename(columns={
        "nctId": "ID",
        "facility": "Nome_Fantasia",
        "status": "Status",
        "nome": "Cidade",
        "estado": "UF",
        "latitude": "LAT",
        "longitude": "LONG"
    })
    cnes = cnes.rename(columns={
        "NO_RAZAO_SOCIAL": "Razao_Social",
        "NO_FANTASIA": "Nome_Fantasia",
        "estado_municipio": "UF",
        "cidade_estabelecimento": "Cidade",
        "latitude": "LAT",
        "longitude": "LONG"
    })
    return estudos, cnes

estudos, cnes = load_data()

# ==============================================
# CORRIGIR ESCALA DE COORDENADAS
# ==============================================
def corrigir_coord(v):
    if pd.isna(v):
        return v
    for fator in [1, 10, 100, 1000, 10000]:
        novo = v / fator
        if -35 <= novo <= 5 or -75 <= novo <= -30:
            return novo
    return v

for df in (estudos, cnes):
    df["LAT"] = df["LAT"].apply(corrigir_coord)
    df["LONG"] = df["LONG"].apply(corrigir_coord)

# ==============================================
# FILTROS GLOBAIS (dependentes)
# ==============================================
col_f1, col_f2 = st.columns(2)

# --- UF ---
ufs = sorted(set(estudos["UF"].dropna().unique()) | set(cnes["UF"].dropna().unique()))
ufs_sel = col_f1.multiselect("UF", ufs)

# --- Cidades (dependentes das UFs selecionadas) ---
if ufs_sel:
    cidades_filtradas = sorted(
        set(estudos.loc[estudos["UF"].isin(ufs_sel), "Cidade"].dropna().unique()) |
        set(cnes.loc[cnes["UF"].isin(ufs_sel), "Cidade"].dropna().unique())
    )
else:
    cidades_filtradas = sorted(
        set(estudos["Cidade"].dropna().unique()) | set(cnes["Cidade"].dropna().unique())
    )

cidades_sel = col_f2.multiselect("Cidade", cidades_filtradas)

# --- Aplicar filtros ---
if ufs_sel:
    estudos = estudos[estudos["UF"].isin(ufs_sel)]
    cnes = cnes[cnes["UF"].isin(ufs_sel)]

if cidades_sel:
    estudos = estudos[estudos["Cidade"].isin(cidades_sel)]
    cnes = cnes[cnes["Cidade"].isin(cidades_sel)]

df_estudos = estudos.copy()
df_cnes = cnes.copy()

# ==============================================
# INDICADORES (TILES)
# ==============================================
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f"<div class='metric-box'><div class='metric-label'>Estudos Clínicos</div><div class='metric-value'>{len(df_estudos):,}</div></div>", unsafe_allow_html=True)
with c2:
    st.markdown(f"<div class='metric-box'><div class='metric-label'>Unidades CNES</div><div class='metric-value'>{len(df_cnes):,}</div></div>", unsafe_allow_html=True)
with c3:
    st.markdown(f"<div class='metric-box'><div class='metric-label'>Cidades com Estudos</div><div class='metric-value'>{df_estudos['Cidade'].nunique():,}</div></div>", unsafe_allow_html=True)
with c4:
    st.markdown(f"<div class='metric-box'><div class='metric-label'>Cidades com CNES</div><div class='metric-value'>{df_cnes['Cidade'].nunique():,}</div></div>", unsafe_allow_html=True)

# ==============================================
# MAPA + GRÁFICOS
# ==============================================
col_mapa, col_grafs = st.columns([1.9, 1.3])

# ---- Mapa ----
with col_mapa:
    st.markdown("<h3 class='centered-title'>Mapa de Localização</h3>", unsafe_allow_html=True)


    fig_map = go.Figure()

    # CNES – Unidades de Saúde (Verde Esmeralda)
    if not df_cnes.empty:
        fig_map.add_trace(go.Scattermapbox(
            lat=df_cnes["LAT"],
            lon=df_cnes["LONG"],
            mode="markers",
            marker=go.scattermapbox.Marker(
                size=8,
                color="#3AAFA9",  # verde esmeralda
                opacity=0.85
            ),
            name="CNES – Unidades de Saúde",
            customdata=df_cnes[["Nome_Fantasia", "Razao_Social", "Cidade", "UF"]],
            hovertemplate="<b>%{customdata[0]}</b><br>Razão Social: %{customdata[1]}<br>Cidade: %{customdata[2]}<br>UF: %{customdata[3]}<extra></extra>"
        ))

        # Estudos Clínicos (Roxo Escuro) — hover mostra quantidade, tamanho fixo
    if not df_estudos.empty:
        # Agrupar por coordenadas
        agrupado = (
            df_estudos.groupby(["LAT", "LONG", "Cidade", "UF"])
            .size()
            .reset_index(name="Qtd_Estudos")
        )

        fig_map.add_trace(go.Scattermapbox(
            lat=agrupado["LAT"],
            lon=agrupado["LONG"],
            mode="markers",
            marker=go.scattermapbox.Marker(
                size=9,  # tamanho fixo
                color="#5B21B6",
                opacity=0.9
            ),
            name="Estudos Clínicos",
            customdata=agrupado[["Cidade", "UF", "Qtd_Estudos"]],
            hovertemplate="<b>%{customdata[0]}</b><br>UF: %{customdata[1]}<br>Estudos: %{customdata[2]}<extra></extra>"
        ))


    fig_map.update_layout(
        mapbox_style="open-street-map",
        mapbox_zoom=4,
        mapbox_center={"lat": -15.78, "lon": -47.93},
        height=850,
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        hovermode="closest",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=0.01,
            xanchor="right",
            x=1,
            bgcolor="rgba(255,255,255,0.7)",
            bordercolor="rgba(0,0,0,0.1)",
            borderwidth=1
        )
    )
    st.plotly_chart(fig_map, use_container_width=True)

# ---- Gráficos Laterais ----
with col_grafs:
    st.markdown("<h3 class='centered-title'>Cidades com Mais Estudos</h3>", unsafe_allow_html=True)


    top_cidades = (
        df_estudos["Cidade"]
        .value_counts()
        .head(10)
        .reset_index()
        .rename(columns={"index": "Cidade", "count": "Quantidade"})
        .sort_values(by="Quantidade", ascending=True)
    )

    if not top_cidades.empty:
        fig_bar = px.bar(
            top_cidades,
            x="Quantidade",
            y="Cidade",
            text="Quantidade",
            color="Quantidade",
            color_continuous_scale=["#3AAFA9", "#5B21B6"],  # verde → roxo
            orientation="h"
        )
        fig_bar.update_layout(
            xaxis_title="Quantidade de Estudos",
            yaxis_title="",
            coloraxis_showscale=False,
            height=400,
            margin=dict(t=20, b=20)
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("Nenhum estudo encontrado com os filtros aplicados.")

        # ==============================================
    # GRÁFICO DE STATUS
    # ==============================================
    st.markdown("<h3 class='centered-title'>Distribuição dos Estudos por Status</h3>", unsafe_allow_html=True)


    if not df_estudos.empty and "Status" in df_estudos.columns:
        status_count = df_estudos["Status"].astype(str).str.strip().value_counts().reset_index()
        status_count.columns = ["Status", "Quantidade"]

        # Dicionário de tradução (com lower-case para garantir correspondência)
        traducao_status = {
            "recruiting": "Recrutando",
            "active_not_recruiting": "Ativo, não recrutando",
            "completed": "Concluído",
            "terminated": "Encerrado",
            "withdrawn": "Retirado",
            "enrolling by invitation": "Inscrição por convite",
            "suspended": "Suspenso",
            "not_yet_recruiting": "Ainda não recrutando",
            "unknown status": "Status desconhecido"
        }

        # Traduzindo de forma segura
        status_count["Status_PT"] = status_count["Status"].apply(
            lambda x: traducao_status.get(x.lower().strip(), x)
        )

        # Ordena por quantidade
        status_count = status_count.sort_values(by="Quantidade", ascending=False)

        # Gráfico radar
        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=status_count["Quantidade"],
            theta=status_count["Status_PT"],
            fill="toself",
            name="Status",
            line_color="#5B21B6",
            fillcolor="rgba(58, 175, 169, 0.3)"
        ))

        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, color="#3AAFA9")),
            showlegend=False,
            height=400,
            margin=dict(t=20, b=20)
        )

        st.plotly_chart(fig_radar, use_container_width=True)
    else:
        st.info("Nenhum dado disponível para o gráfico de status.")

