import streamlit as st
from streamlit_folium import st_folium
import folium
from folium.plugins import MarkerCluster
from geopy.geocoders import Nominatim
import database as db
import pandas as pd

# Configuração da página Web
st.set_page_config(
    page_title="Sistema Integrado de Gestão de Riscos - Defesa Civil",
    page_icon="🛡️",
    layout="wide"
)

# Inicializa o BD
db.init_db()

# Dicionário de Cores por Nível de Severidade (Para Ocorrências Ativas/Em Atendimento)
SEVERITY_COLORS = {
    "Baixo": "yellow",
    "Médio": "orange",
    "Crítico": "red"
}

# Mapeamento de Ícones por Natureza da Ocorrência (FontAwesome / Bootstrap Icons do Folium)
CATEGORY_ICONS = {
    "Buraco/Avaria na via": "wrench",
    "Árvore/Ramo caído": "tree",
    "Alagamento/Inundação": "tint",
    "Incêndio em vegetação/edificação": "fire",
    "Fio energizado/Rede elétrica caída": "flash",
    "Deslizamento/Risco de desabamento": "warning-sign",
    "Outro": "info-sign"
}

STATUS_MAP = {
    "active": "🚨 Ativo",
    "in_progress": "🟧 Em Atendimento",
    "resolved": "✅ Resolvido"
}

CATEGORIES = [
    "Buraco/Avaria na via",
    "Árvore/Ramo caído",
    "Alagamento/Inundação",
    "Incêndio em vegetação/edificação",
    "Fio energizado/Rede elétrica caída",
    "Deslizamento/Risco de desabamento",
    "Outro"
]

# Geocodificador
geolocator = Nominatim(user_agent="defesa_civil_app")

# --- BARRA LATERAL (Sidebar) ---
st.sidebar.title("🛡️ Defesa Civil Colaborativa")

# Alternador de Perfil
role = st.sidebar.radio(
    "Modo de Operação:",
    ["👤 Cidadão (Reporte)", "🛡️ Agente Defesa Civil (Gestão/Analytics)"],
    index=0
)

st.sidebar.divider()

# Busca por Endereço
st.sidebar.subheader("📍 Ir para Localização / CEP")
search_address = st.sidebar.text_input("Endereço, Bairro ou Cidade:", placeholder="Ex: Av. Paulista, São Paulo")
searched_coords = None

if search_address:
    try:
        location = geolocator.geocode(search_address)
        if location:
            searched_coords = [location.latitude, location.longitude]
            st.sidebar.success(f"Encontrado: {location.address[:35]}...")
        else:
            st.sidebar.warning("Endereço não localizado.")
    except Exception:
        st.sidebar.error("Erro no serviço de busca por endereço.")

st.sidebar.divider()

# Filtros do Mapa
st.sidebar.subheader("🔍 Filtros de Visualização")
cat_filter = st.sidebar.selectbox("Categoria:", ["Todas"] + CATEGORIES)
sev_filter = st.sidebar.selectbox("Gravidade:", ["Todos", "Baixo", "Médio", "Crítico"])
stat_filter = st.sidebar.selectbox("Status:", ["Todos", "active", "in_progress", "resolved"], format_func=lambda x: STATUS_MAP.get(x, x))

# Obter Incidentes
incidents = db.get_incidents(cat_filter, sev_filter, stat_filter)

# --- CORPO PRINCIPAL ---
st.title("🗺️ Monitoramento Geográfico e Resposta a Riscos")

# Abas Principais (Mapa vs Analytics)
if "🛡️ Agente" in role:
    tab_mapa, tab_analytics = st.tabs(["🗺️ Mapa Operacional", "📊 Relatórios e Exportação CSV"])
else:
    tab_mapa = st.container()
    tab_analytics = None

# ---- ABA 1: MAPA OPERACIONAL ----
with tab_mapa:
    col_map, col_action = st.columns([2.5, 1])

    with col_map:
        st.caption("Centralize o mapa clicando para cadastrar um risco ou clique nos marcadores para detalhes.")

        # Posição Central do Mapa
        map_center = [-23.55052, -46.633308] # SP Default
        if searched_coords:
            map_center = searched_coords
        elif incidents:
            map_center = [incidents[0]["latitude"], incidents[0]["longitude"]]

        # Mapa com Múltiplas Camadas (Satélite / OSM)
        m = folium.Map(location=map_center, zoom_start=13, tiles=None)
        
        folium.TileLayer('OpenStreetMap', name='Mapa de Ruas').add_to(m)
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Esri',
            name='Visão Satélite'
        ).add_to(m)

        # Agrupamento (Cluster) de Marcadores
        marker_cluster = MarkerCluster(name="Ocorrências Agrupadas").add_to(m)

        for inc in incidents:
            # REGRA DE ÍCONES E CORES DINÂMICAS:
            if inc["status"] == "resolved":
                color = "green"        # Ocorrência resolvida sempre fica VERDE
                icon_name = "ok"       # Ícone de verificação / resolvido
            else:
                color = SEVERITY_COLORS.get(inc["severity"], "orange") # Cor conforme a urgência (Amarelo/Laranja/Vermelho)
                icon_name = CATEGORY_ICONS.get(inc["category"], "exclamation-sign") # Ícone conforme a natureza

            status_desc = STATUS_MAP.get(inc["status"], inc["status"])
            
            popup_html = f"""
            <div style="font-family: Arial, sans-serif; width: 200px;">
                <h4 style="margin-bottom:5px;">{inc['category']}</h4>
                <p style="margin:2px 0;"><b>Status:</b> {status_desc}</p>
                <p style="margin:2px 0;"><b>Urgência:</b> {inc['severity']}</p>
                <p style="margin:5px 0; font-size: 12px;">{inc['description']}</p>
                <small style="color:gray;"><b>Horário:</b> {inc['created_at']}</small>
            </div>
            """
            
            folium.Marker(
                location=[inc["latitude"], inc["longitude"]],
                popup=folium.Popup(popup_html, max_width=240),
                tooltip=f"[{inc['severity']}] {inc['category']} - {status_desc}",
                icon=folium.Icon(color=color, icon=icon_name)
            ).add_to(marker_cluster)

        folium.LayerControl().add_to(m)

        # Renderização Interativa
        map_data = st_folium(m, width="100%", height=550)

    # Painel de Ação Lateral
    with col_action:
        if "👤 Cidadão" in role:
            st.subheader("➕ Novo Reporte")
            
            clicked = map_data.get("last_clicked") if map_data else None
            
            if clicked:
                lat, lng = clicked["lat"], clicked["lng"]
                st.success(f"📍 Coordenada: {lat:.4f}, {lng:.4f}")
            else:
                lat, lng = map_center[0], map_center[1]
                st.info("💡 Clique em qualquer ponto do mapa para selecionar a localização.")

            with st.form("new_incident"):
                cat = st.selectbox("Tipo:", CATEGORIES)
                sev = st.select_slider("Urgência:", options=["Baixo", "Médio", "Crítico"], value="Médio")
                desc = st.text_area("Descrição do Risco/Ocorrência:")
                img = st.text_input("Link de Imagem (Opcional):")
                
                if st.form_submit_button("🚨 Enviar para Defesa Civil", use_container_width=True):
                    if not desc.strip():
                        st.error("Descreva a ocorrência antes de enviar.")
                    else:
                        db.add_incident(cat, sev, desc, img, lat, lng)
                        st.success("Ocorrência enviada com sucesso!")
                        st.rerun()

        else:
            # Visão da Defesa Civil - Moderação Rápida
            st.subheader("⚙️ Painel Operacional")
            
            criticos = [i for i in incidents if i['severity'] == 'Crítico' and i['status'] != 'resolved']
            st.metric("Ocorrências CRÍTICAS Pendentes", len(criticos))

            st.divider()

            for inc in incidents[:5]: # Mostra os 5 mais recentes
                with st.expander(f"#{inc['id']} - {inc['category']}"):
                    st.write(f"**Urgência:** {inc['severity']}")
                    st.write(f"**Descrição:** {inc['description']}")
                    st.write(f"**Status:** {STATUS_MAP.get(inc['status'])}")
                    
                    c1, c2 = st.columns(2)
                    if c1.button("Em Atendimento", key=f"btn_prog_{inc['id']}"):
                        db.update_status(inc['id'], 'in_progress')
                        st.rerun()
                    if c2.button("Resolver", key=f"btn_res_{inc['id']}"):
                        db.update_status(inc['id'], 'resolved')
                        st.rerun()

# ---- ABA 2: ANALYTICS & RELATÓRIOS ----
if "🛡️ Agente" in role and tab_analytics:
    with tab_analytics:
        st.subheader("📊 Relatórios e Dados Estratégicos")
        
        df = db.get_dataframe()
        
        if not df.empty:
            # Métricas Gerais
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total de Ocorrências", len(df))
            m2.metric("Ativas/Abertas", len(df[df['status'] == 'active']))
            m3.metric("Em Atendimento", len(df[df['status'] == 'in_progress']))
            m4.metric("Resolvidas", len(df[df['status'] == 'resolved']))

            st.divider()

            # Gráficos Resumidos
            g1, g2 = st.columns(2)
            with g1:
                st.markdown("**Ocorrências por Categoria**")
                cat_counts = df['category'].value_counts()
                st.bar_chart(cat_counts)
                
            with g2:
                st.markdown("**Distribuição por Gravidade**")
                sev_counts = df['severity'].value_counts()
                st.bar_chart(sev_counts)

            st.divider()

            # Tabela de Dados Completa + Botão para Download CSV/Excel
            st.subheader("📋 Tabela Completa de Chamados")
            st.dataframe(df, use_container_width=True)

            # Botão de Exportação CSV
            csv_data = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Baixar Relatório Completo (.CSV)",
                data=csv_data,
                file_name="relatorio_defesa_civil.csv",
                mime="text/csv",
                use_container_width=True
            )
        else:
            st.info("Nenhum dado registrado para gerar relatórios.")