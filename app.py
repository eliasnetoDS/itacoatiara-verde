import streamlit as st
import geopandas as gpd
import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.express as px

# ── Configuração da página ──────────────────────────────────────────
st.set_page_config(
    page_title="Itacoatiara Verde",
    page_icon="🌿",
    layout="wide"
)

# ── Estilo ──────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #f8faf5; }
    .metric-box {
        background: white;
        border-radius: 10px;
        padding: 16px;
        border: 1px solid #e0ecd6;
        text-align: center;
    }
    .metric-value { font-size: 28px; font-weight: 600; color: #3B6D11; }
    .metric-label { font-size: 12px; color: #666; margin-top: 4px; }
    .status-adequado { background:#EAF3DE; color:#3B6D11; padding:4px 12px; border-radius:20px; font-size:13px; font-weight:500; }
    .status-moderado { background:#FAEEDA; color:#854F0B; padding:4px 12px; border-radius:20px; font-size:13px; font-weight:500; }
    .status-atencao  { background:#FAEEDA; color:#854F0B; padding:4px 12px; border-radius:20px; font-size:13px; font-weight:500; }
    .status-critico  { background:#FCEBEB; color:#A32D2D; padding:4px 12px; border-radius:20px; font-size:13px; font-weight:500; }
</style>
""", unsafe_allow_html=True)

# ── Carregar dados ───────────────────────────────────────────────────
@st.cache_data
def carregar_dados():
    gdf = gpd.read_file('itacoatiara_verde.geojson')
    df  = pd.read_csv('itacoatiara_verde.csv')
    return gdf, df

gdf, df = carregar_dados()

# ── Cabeçalho ───────────────────────────────────────────────────────
st.title("🌿 Itacoatiara - Área Verde Por Habitante")
st.markdown("**Painel Socioambiental Urbano** · Itacoatiara, Amazonas")
st.markdown("---")

# ── Métricas gerais ─────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="metric-box">
        <div class="metric-value">{len(df)}</div>
        <div class="metric-label">Setores censitários</div>
    </div>""", unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="metric-box">
        <div class="metric-value">{int(df['populacao'].sum()):,}</div>
        <div class="metric-label">População total</div>
    </div>""", unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="metric-box">
        <div class="metric-value">{df['area_veg_ha'].sum():.1f} ha</div>
        <div class="metric-label">Área verde total</div>
    </div>""", unsafe_allow_html=True)

with col4:
    media = df['indice_verde'].mean()
    st.markdown(f"""
    <div class="metric-box">
        <div class="metric-value">{media:.1f} m²</div>
        <div class="metric-label">Índice médio por habitante</div>
    </div>""", unsafe_allow_html=True)

st.markdown("---")

# ── Layout principal: mapa + painel ─────────────────────────────────
col_mapa, col_painel = st.columns([2, 1])

with col_mapa:
    st.subheader("🗺️ Mapa por setor censitário")
    st.caption("Clique em um setor para ver os indicadores detalhados")

    # Slider de opacidade
    opacidade = st.slider("🔍 Opacidade dos setores",
                          min_value=0.0, max_value=1.0,
                          value=0.75, step=0.05)

    # Cores por classificação
    cores = {
        'Adequado': '#639922',
        'Moderado': '#97C459',
        'Atenção':  '#EF9F27',
        'Crítico':  '#E24B4A'
    }

    # Mapa base Esri Satellite
    centro = [gdf.geometry.centroid.y.mean(), gdf.geometry.centroid.x.mean()]
    m = folium.Map(location=centro, zoom_start=13)

    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='Esri Satellite',
        overlay=False,
        control=True
    ).add_to(m)

    def estilo(feature):
        classe = feature['properties'].get('classificacao', '')
        return {
            'fillColor': cores.get(classe, '#888'),
            'color': 'white',
            'weight': 1.5,
            'fillOpacity': opacidade
        }

    def highlight(feature):
        return {'weight': 3, 'color': '#333', 'fillOpacity': 0.9}

    folium.GeoJson(
        gdf.__geo_interface__,
        style_function=estilo,
        highlight_function=highlight,
        tooltip=folium.GeoJsonTooltip(
            fields=['CD_SETOR', 'populacao', 'indice_verde', 'classificacao'],
            aliases=['Setor:', 'População:', 'Índice (m²/hab):', 'Classificação:'],
            localize=True
        )
    ).add_to(m)

    # Legenda
    legenda = """
    <div style="position: fixed; bottom: 30px; left: 30px; z-index: 1000;
         background: white; padding: 12px 16px; border-radius: 8px;
         border: 1px solid #ddd; font-family: sans-serif; font-size: 12px;">
      <b>Área verde / habitante</b><br>
      <span style="color:#639922">■</span> Adequado (≥12 m²)<br>
      <span style="color:#97C459">■</span> Moderado (6–12 m²)<br>
      <span style="color:#EF9F27">■</span> Atenção (3–6 m²)<br>
      <span style="color:#E24B4A">■</span> Crítico (&lt;3 m²)
    </div>
    """
    m.get_root().html.add_child(folium.Element(legenda))

    saida = st_folium(m, width=700, height=480)

with col_painel:
    st.subheader("📊 Indicadores do setor")

    setor_selecionado = None
    if saida and saida.get('last_active_drawing'):
        props = saida['last_active_drawing'].get('properties', {})
        setor_selecionado = props.get('CD_SETOR')

    if setor_selecionado:
        s = df[df['CD_SETOR'] == setor_selecionado].iloc[0]
        classe = s['classificacao']
        css    = classe.lower().replace('ã', 'a')

        st.markdown(f"**{setor_selecionado}**")
        st.markdown(f'<span class="status-{css}">{classe}</span>', unsafe_allow_html=True)
        st.markdown("")

        c1, c2 = st.columns(2)
        c1.metric("População", f"{int(s['populacao']):,}")
        c2.metric("Área verde", f"{s['area_veg_ha']:.1f} ha")
        st.metric("Índice verde / habitante", f"{s['indice_verde']:.1f} m²/hab")
        st.metric("Ranking no município", f"{int(s['ranking'])}º de {len(df)}")

        st.markdown("**Composição do setor**")
        comp = pd.DataFrame({
            'Classe': ['Vegetação', 'Construção', 'Outros'],
            'Percentual': [s['pct_vegetacao'], s['pct_construcao'], s['pct_outros']]
        })
        fig = px.bar(comp, x='Percentual', y='Classe', orientation='h',
                     color='Classe',
                     color_discrete_map={
                         'Vegetação': '#639922',
                         'Construção': '#888780',
                         'Outros': '#EF9F27'
                     },
                     range_x=[0, 100])
        fig.update_layout(showlegend=False, margin=dict(l=0, r=0, t=0, b=0),
                          height=180, plot_bgcolor='rgba(0,0,0,0)',
                          paper_bgcolor='rgba(0,0,0,0)')
        fig.update_xaxes(ticksuffix='%')
        st.plotly_chart(fig, use_container_width=True)

    else:
        st.info("👈 Clique em um setor no mapa para ver os indicadores")

# ── Ranking completo ─────────────────────────────────────────────────
st.markdown("---")
st.subheader("🏆 Ranking dos setores")

col_top, col_bot = st.columns(2)

with col_top:
    st.markdown("**✅ Top 5 — Mais verde por habitante**")
    top5 = df.nlargest(5, 'indice_verde')[['CD_SETOR', 'populacao', 'indice_verde', 'classificacao']]
    top5.columns = ['Setor', 'População', 'Índice (m²/hab)', 'Classificação']
    st.dataframe(top5, hide_index=True, use_container_width=True)

with col_bot:
    st.markdown("**⚠️ 5 setores mais críticos**")
    bot5 = df.nsmallest(5, 'indice_verde')[['CD_SETOR', 'populacao', 'indice_verde', 'classificacao']]
    bot5.columns = ['Setor', 'População', 'Índice (m²/hab)', 'Classificação']
    st.dataframe(bot5, hide_index=True, use_container_width=True)

# ── Rodapé ───────────────────────────────────────────────────────────
st.markdown("---")
st.caption("Dados: IBGE (setores censitários) · Classificação supervisionada de imagem de satélite · Developed with Python & Streamlit")