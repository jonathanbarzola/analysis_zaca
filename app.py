import streamlit as st
import pandas as pd
import re
import plotly.express as px
from collections import Counter
import emoji
from wordcloud import WordCloud, STOPWORDS
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt
import os

# --- Page Configuration ---
st.set_page_config(
    page_title="Análisis Chat WhatsApp - ZACA FEST 🥳",
    page_icon="💬",
    layout="wide"
)

# --- Helper Functions ---

def parse_chat_data(file_path):
    """
    Parsea el contenido del chat de WhatsApp desde archivo
    """
    if not os.path.exists(file_path):
        st.error(f"❌ No se encontró el archivo: {file_path}")
        return pd.DataFrame(), pd.DataFrame()
    
    data = []
    
    # Patrones para parsear mensajes
    user_pattern = r'\[(\d{2}/\d{2}/\d{2}, \d{2}:\d{2}:\d{2})\] ([^:]+): (.*)'
    system_pattern = r'\[(\d{2}/\d{2}/\d{2}, \d{2}:\d{2}:\d{2})\] (.*)'

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                line = line.strip()
                if not line:
                    continue
                    
                # Intentar coincidir con mensaje de usuario
                match_user = re.match(user_pattern, line)
                if match_user:
                    timestamp_str, sender, message = match_user.groups()
                    
                    # Limpiar el remitente
                    sender = sender.replace('~ ', '').strip()
                    
                    try:
                        timestamp = pd.to_datetime(timestamp_str, format='%d/%m/%y, %H:%M:%S')
                        data.append({
                            "Timestamp": timestamp,
                            "Sender": sender,
                            "Message": message.strip(),
                            "Type": "User"
                        })
                    except:
                        continue
                else:
                    # Intentar coincidir con mensaje de sistema
                    match_system = re.match(system_pattern, line)
                    if match_system:
                        timestamp_str, message_content = match_system.groups()
                        
                        # Identificar mensajes de sistema
                        system_keywords = [
                            "creó este grupo", "se unió usando el enlace", "Te uniste mediante el enlace",
                            "mensajes y las llamadas están cifrados", "añadió a", "cambió los ajustes",
                            "activó los mensajes temporales", "activó la aprobación"
                        ]
                        
                        if any(keyword in message_content for keyword in system_keywords):
                            try:
                                timestamp = pd.to_datetime(timestamp_str, format='%d/%m/%y, %H:%M:%S')
                                data.append({
                                    "Timestamp": timestamp,
                                    "Sender": "System",
                                    "Message": message_content.strip(),
                                    "Type": "System"
                                })
                            except:
                                continue
        
    except Exception as e:
        st.error(f"❌ Error al leer el archivo: {str(e)}")
        return pd.DataFrame(), pd.DataFrame()
    
    if not data:
        st.error("❌ No se pudieron extraer datos del archivo")
        return pd.DataFrame(), pd.DataFrame()
    
    df = pd.DataFrame(data)
    user_df = df[df['Type'] == 'User'].copy()
    
    if user_df.empty:
        return df, pd.DataFrame()

    # Agregar columnas de tiempo
    user_df['Date'] = user_df['Timestamp'].dt.date
    user_df['Hour'] = user_df['Timestamp'].dt.hour
    user_df['DayName'] = user_df['Timestamp'].dt.day_name()
    user_df['MonthName'] = user_df['Timestamp'].dt.month_name()
    user_df['Year'] = user_df['Timestamp'].dt.year
    
    return df, user_df

def extract_emojis(text):
    """
    Extrae emojis de un texto
    """
    return [char for char in text if emoji.is_emoji(char)]

def get_links(text):
    """
    Extrae URLs de un texto
    """
    url_pattern = r'(https?://\S+)'
    return re.findall(url_pattern, text)

def is_multimedia(message):
    """
    Identifica si un mensaje es multimedia
    """
    multimedia_keywords = [
        "sticker omitido", "video omitido", "imagen omitida", 
        "audio omitido", "gif omitido", "<Multimedia omitido>"
    ]
    return any(keyword in message.lower() for keyword in multimedia_keywords)

def is_poll(message):
    """
    Identifica si un mensaje es una encuesta
    """
    return message.strip().startswith("ENCUESTA:")

def create_wordcloud_image(text):
    """
    Crea una nube de palabras
    """
    # Stopwords en español
    stopwords_es = set(STOPWORDS)
    custom_stopwords = [
        "que", "qué", "con", "de", "la", "el", "en", "y", "o", "un", "una", "unos", "unas",
        "los", "las", "del", "al", "se", "su", "sus", "ya", "pero", "por", "para", "como",
        "más", "mas", "este", "esta", "eso", "esos", "esas", "si", "sí", "no", "ni",
        "me", "te", "le", "nos", "os", "les", "mi", "mis", "tu", "tus", "él", "ella",
        "ellos", "ellas", "nosotros", "nosotras", "vosotros", "vosotras", "usted", "ustedes",
        "sticker", "omitido", "video", "imagen", "audio", "gif", "multimedia", "mensaje",
        "eliminó", "jaja", "jajaja", "jajajaja", "xd", "https", "http", "www", "com", "pe", "es",
        "q", "k", "d", "x", "a", "e", "i", "u", "va", "solo", "pues", "ahí", "asi", "así", "ah", "ok",
        "gracias", "porfa", "hola", "holii", "enserio", "verdad", "entonces", "bueno", "listo",
        "tambien", "también", "pasar", "sticker", "guau", "roten"
    ]
    stopwords_es.update(custom_stopwords)
    
    if not text.strip():
        return None
        
    wordcloud = WordCloud(
        width=800, 
        height=400,
        background_color='black',
        stopwords=stopwords_es,
        min_font_size=10,
        colormap='plasma',
        max_words=100,
        collocations=False
    ).generate(text)
    
    return wordcloud

# --- Streamlit App ---
def main():
    st.title("🎉 Análisis Chat ZACA FEST")
    st.markdown("### Análisis completo del grupo de WhatsApp")
    
    # Cargar datos automáticamente
    with st.spinner("🔄 Cargando y procesando el chat..."):
        full_df, df = parse_chat_data("zaca.txt")
    
    if df.empty:
        st.error("❌ No se pudieron cargar los datos del chat.")
        st.info("Asegúrate de que el archivo 'zaca.txt' esté en la carpeta del proyecto.")
        return
    
    st.success(f"✅ Chat cargado exitosamente! 🎊")
    
    # --- Header con información básica ---
    st.markdown("---")
    total_messages = len(df)
    unique_users = df['Sender'].nunique()
    date_range = f"{df['Timestamp'].min().strftime('%d/%m/%Y')} - {df['Timestamp'].max().strftime('%d/%m/%Y')}"
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📊 Total Mensajes", total_messages)
    with col2:
        st.metric("👥 Participantes", unique_users)
    with col3:
        st.metric("📅 Período", date_range)
    
    st.markdown("---")
    
    # Calcular estadísticas adicionales
    df['Emojis'] = df['Message'].apply(extract_emojis)
    df['Links'] = df['Message'].apply(get_links)
    
    multimedia_count = df[df['Message'].apply(is_multimedia)].shape[0]
    emoji_count = sum(df['Emojis'].str.len())
    link_count = sum(df['Links'].str.len())
    deleted_count = df[df['Message'] == "Se eliminó este mensaje."].shape[0]
    
    # --- Estadísticas Generales ---
    st.header("📊 Estadísticas Generales")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🎬 Multimedia", multimedia_count)
    with col2:
        st.metric("😀 Emojis", emoji_count)
    with col3:
        st.metric("🔗 Enlaces", link_count)
    with col4:
        st.metric("🗑️ Eliminados", deleted_count)
    
    # --- Actividad por Usuario ---
    st.header("👥 ¿Quién habla más?")
    
    user_activity = df['Sender'].value_counts().reset_index()
    user_activity.columns = ['Usuario', 'Mensajes']
    user_activity['Porcentaje'] = (user_activity['Mensajes'] / total_messages * 100).round(2)
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📈 Ranking de Actividad")
        # Añadir emojis para el ranking
        ranking_emojis = ["🥇", "🥈", "🥉", "🏅", "🏅", "🏅", "🏅", "🏅", "🏅", "🏅"]
        user_activity_display = user_activity.copy()
        user_activity_display['Ranking'] = [ranking_emojis[i] if i < len(ranking_emojis) else "🏅" for i in range(len(user_activity_display))]
        user_activity_display = user_activity_display[['Ranking', 'Usuario', 'Mensajes', 'Porcentaje']]
        st.dataframe(user_activity_display, hide_index=True, use_container_width=True)
    
    with col2:
        st.subheader("🥧 Distribución de Mensajes")
        if len(user_activity) > 1:
            fig_pie = px.pie(
                user_activity.head(10), 
                values='Mensajes', 
                names='Usuario',
                title='¿Quién domina el chat?',
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            fig_pie.update_layout(template="plotly_dark")
            st.plotly_chart(fig_pie, use_container_width=True)
    
    # --- Análisis Temporal ---
    st.header("⏰ ¿Cuándo somos más activos?")
    
    # Actividad por hora
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🕐 Por Hora del Día")
        hourly_activity = df.groupby('Hour').size().reset_index()
        hourly_activity.columns = ['Hora', 'Mensajes']
        
        fig_hourly = px.line(
            hourly_activity, 
            x='Hora', 
            y='Mensajes',
            title='¿A qué hora hablamos más?',
            markers=True,
            color_discrete_sequence=['#ff6b6b']
        )
        fig_hourly.update_layout(template="plotly_dark")
        fig_hourly.update_traces(line=dict(width=3), marker=dict(size=8))
        st.plotly_chart(fig_hourly, use_container_width=True)
    
    with col2:
        st.subheader("📅 Por Día de la Semana")
        
        days_spanish = {
            'Monday': 'Lun', 'Tuesday': 'Mar', 'Wednesday': 'Mié',
            'Thursday': 'Jue', 'Friday': 'Vie', 'Saturday': 'Sáb', 'Sunday': 'Dom'
        }
        
        daily_activity = df.groupby('DayName').size().reset_index()
        daily_activity.columns = ['Día', 'Mensajes']
        daily_activity['Día'] = daily_activity['Día'].map(days_spanish)
        
        # Ordenar días correctamente
        day_order = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
        daily_activity['Día'] = pd.Categorical(daily_activity['Día'], categories=day_order, ordered=True)
        daily_activity = daily_activity.sort_values('Día')
        
        fig_daily = px.bar(
            daily_activity, 
            x='Día', 
            y='Mensajes',
            title='¿Qué día hablamos más?',
            color='Mensajes',
            color_continuous_scale='viridis'
        )
        fig_daily.update_layout(template="plotly_dark")
        st.plotly_chart(fig_daily, use_container_width=True)
    
    # Línea de tiempo
    st.subheader("📈 Evolución del Chat")
    timeline = df.groupby(df['Timestamp'].dt.date).size().reset_index()
    timeline.columns = ['Fecha', 'Mensajes']
    
    fig_timeline = px.area(
        timeline, 
        x='Fecha', 
        y='Mensajes',
        title='¿Cómo ha evolucionado nuestro chat?',
        color_discrete_sequence=['#4ecdc4']
    )
    fig_timeline.update_layout(template="plotly_dark")
    st.plotly_chart(fig_timeline, use_container_width=True)
    
    # --- Análisis de Emojis ---
    if emoji_count > 0:
        st.header("😀 ¡Nuestros Emojis Favoritos!")
        
        all_emojis = [emoji for emoji_list in df['Emojis'] for emoji in emoji_list]
        emoji_counter = Counter(all_emojis)
        top_emojis = pd.DataFrame(emoji_counter.most_common(15), columns=['Emoji', 'Cantidad'])
        
        if not top_emojis.empty:
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.subheader("🏆 Top 15 Emojis")
                # Añadir porcentajes
                top_emojis['Porcentaje'] = (top_emojis['Cantidad'] / emoji_count * 100).round(1)
                st.dataframe(top_emojis, hide_index=True, use_container_width=True)
            
            with col2:
                st.subheader("📊 Visualización")
                fig_emoji = px.bar(
                    top_emojis.head(10),
                    x='Cantidad',
                    y='Emoji',
                    orientation='h',
                    title='Los más usados',
                    color='Cantidad',
                    color_continuous_scale='rainbow'
                )
                fig_emoji.update_layout(template="plotly_dark", height=500)
                st.plotly_chart(fig_emoji, use_container_width=True)
    
    # --- Análisis de Multimedia ---
    if multimedia_count > 0:
        st.header("🎬 Análisis Multimedia")
        
        multimedia_df = df[df['Message'].apply(is_multimedia)]
        multimedia_by_user = multimedia_df['Sender'].value_counts().reset_index()
        multimedia_by_user.columns = ['Usuario', 'Multimedia']
        
        fig_multimedia = px.bar(
            multimedia_by_user.head(10),
            x='Usuario',
            y='Multimedia',
            title='¿Quién comparte más stickers/multimedia?',
            color='Multimedia',
            color_continuous_scale='sunset'
        )
        fig_multimedia.update_layout(template="plotly_dark")
        st.plotly_chart(fig_multimedia, use_container_width=True)
    
    # --- Nube de Palabras ---
    st.header("☁️ Nube de Palabras")
    st.subheader("Las palabras que más usamos")
    
    # Filtrar mensajes de texto
    text_messages = df[
        ~df['Message'].apply(is_multimedia) & 
        ~df['Message'].apply(is_poll) & 
        (df['Message'] != "Se eliminó este mensaje.")
    ]['Message']
    
    if not text_messages.empty:
        all_text = " ".join(text_messages.str.lower())
        
        wordcloud = create_wordcloud_image(all_text)
        
        if wordcloud:
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.imshow(wordcloud, interpolation='bilinear')
            ax.axis('off')
            plt.tight_layout(pad=0)
            st.pyplot(fig)
        else:
            st.info("No hay suficiente texto para generar la nube de palabras.")
    else:
        st.info("No se encontraron mensajes de texto.")
    
    # --- Estadísticas Detalladas por Usuario ---
    st.header("📈 Estadísticas Detalladas")
    st.subheader("¿Cómo es el estilo de cada uno?")
    
    detailed_stats = []
    for user in df['Sender'].unique():
        user_df = df[df['Sender'] == user]
        
        # Calcular estadísticas
        total_msgs = len(user_df)
        text_msgs = user_df[~user_df['Message'].apply(is_multimedia)]
        avg_words = text_msgs['Message'].apply(lambda x: len(x.split())).mean() if len(text_msgs) > 0 else 0
        multimedia_msgs = user_df[user_df['Message'].apply(is_multimedia)].shape[0]
        user_emojis = sum(user_df['Emojis'].str.len())
        user_links = sum(user_df['Links'].str.len())
        
        # Hora más activa
        user_hours = user_df['Hour'].mode()
        most_active_hour = user_hours.iloc[0] if len(user_hours) > 0 else 0
        
        detailed_stats.append({
            'Usuario': user,
            'Total Mensajes': total_msgs,
            'Promedio Palabras': round(avg_words if not pd.isna(avg_words) else 0, 1),
            'Multimedia': multimedia_msgs,
            'Emojis': user_emojis,
            'Enlaces': user_links,
            'Hora Favorita': f"{most_active_hour:02d}:00"
        })
    
    detailed_df = pd.DataFrame(detailed_stats).sort_values('Total Mensajes', ascending=False)
    st.dataframe(detailed_df, hide_index=True, use_container_width=True)
    
    # --- Mensajes más largos y más cortos ---
    st.header("📝 Mensajes Curiosos")
    
    col1, col2 = st.columns(2)
    
    # Filtrar solo mensajes de texto para análisis de longitud
    text_only_df = df[~df['Message'].apply(is_multimedia) & (df['Message'] != "Se eliminó este mensaje.")].copy()
    text_only_df['Word_Count'] = text_only_df['Message'].apply(lambda x: len(x.split()))
    
    with col1:
        st.subheader("📚 Mensaje más largo")
        if not text_only_df.empty:
            longest_msg = text_only_df.loc[text_only_df['Word_Count'].idxmax()]
            st.write(f"**{longest_msg['Sender']}** ({longest_msg['Word_Count']} palabras):")
            st.write(f"*{longest_msg['Message'][:200]}{'...' if len(longest_msg['Message']) > 200 else ''}*")
    
    with col2:
        st.subheader("💬 Usuario más expresivo")
        if not text_only_df.empty:
            avg_words_by_user = text_only_df.groupby('Sender')['Word_Count'].mean().sort_values(ascending=False)
            most_verbose = avg_words_by_user.index[0]
            avg_words = avg_words_by_user.iloc[0]
            st.write(f"**{most_verbose}**")
            st.write(f"Promedio: {avg_words:.1f} palabras por mensaje")
    
    # --- Footer ---
    st.markdown("---")
    st.markdown("### 🎊 ¡Resumen del ZACA FEST!")
    st.markdown(f"""
    - 💬 **{total_messages}** mensajes intercambiados
    - 👥 **{unique_users}** personas participando
    - 😀 **{emoji_count}** emojis compartidos
    - 🎬 **{multimedia_count}** stickers y multimedia
    - 📅 Desde **{df['Timestamp'].min().strftime('%d/%m/%Y')}** hasta **{df['Timestamp'].max().strftime('%d/%m/%Y')}**
    """)
    
    st.balloons()

if __name__ == "__main__":
    main()