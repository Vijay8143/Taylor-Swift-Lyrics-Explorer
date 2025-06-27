import streamlit as st
import lyricsgenius
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import pandas as pd
import os
from PIL import Image
import requests
from io import BytesIO
import time
from requests.exceptions import HTTPError
import json
from pathlib import Path

# --- Page Configuration ---
st.set_page_config(
    page_title="Taylor Swift Lyrics Explorer",
    page_icon="🎤",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS for Styling ---
def local_css(file_name):
    try:
        with open(file_name) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("Custom CSS file not found - using default styles")

local_css("style.css")

# --- Genius API Setup with Robust Error Handling ---
@st.cache_data
def get_genius_client():
    try:
        GENIUS_TOKEN = os.getenv("GENIUS_TOKEN")
        if not GENIUS_TOKEN:
            st.error("GENIUS_TOKEN environment variable not found. Please set it in your deployment settings.")
            st.stop()
        
        genius = lyricsgenius.Genius(
            GENIUS_TOKEN,
            verbose=False,
            remove_section_headers=True,
            skip_non_songs=True,
            excluded_terms=["(Remix)", "(Live)"],
            timeout=20
        )
        
        # Add headers to mimic browser request
        genius._session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json'
        })
        
        return genius
    except Exception as e:
        st.error(f"Failed to initialize Genius API client: {str(e)}")
        st.stop()

genius = get_genius_client()

# --- Song Search with Retry Logic ---
def search_song_with_retry(title, artist, max_retries=3):
    for attempt in range(max_retries):
        try:
            song = genius.search_song(title, artist)
            if song:
                return song
            elif attempt == max_retries - 1:
                return None
        except HTTPError as e:
            if e.response.status_code == 429:  # Rate limited
                wait_time = (attempt + 1) * 5
                time.sleep(wait_time)
                continue
            raise
    return None

# --- Word Cloud Generation ---
def generate_word_cloud(lyrics, max_words, background_color, colormap):
    try:
        wordcloud = WordCloud(
            width=800,
            height=400,
            background_color=background_color,
            max_words=max_words,
            colormap=colormap,
            collocations=False,
            prefer_horizontal=0.8,
            scale=2
        ).generate(lyrics)
        
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.axis('off')
        ax.set_title('Lyrics Word Cloud', fontsize=16, pad=20)
        st.pyplot(fig, use_container_width=True)
    except Exception as e:
        st.warning(f"Couldn't generate word cloud: {str(e)}")

# --- Lyrics Analysis Functions ---
def display_lyrics_stats(lyrics):
    try:
        words = lyrics.split()
        word_count = len(words)
        unique_words = len(set(word.lower() for word in words))
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Words", word_count)
        with col2:
            st.metric("Unique Words", unique_words)
        with col3:
            st.metric("Unique Ratio", f"{(unique_words/word_count)*100:.1f}%")
    except Exception as e:
        st.warning(f"Couldn't calculate lyrics stats: {str(e)}")

def display_common_words(lyrics):
    try:
        from collections import Counter
        import re
        
        words = re.findall(r'\w+', lyrics.lower())
        common_words = ["i", "you", "the", "a", "and", "to", "it", "me", "my", "we", "is", "in", "of", "that", "this"]
        filtered_words = [word for word in words if word not in common_words and len(word) > 3]
        word_counts = Counter(filtered_words).most_common(15)
        
        df = pd.DataFrame(word_counts, columns=["Word", "Count"])
        st.dataframe(
            df.style
            .background_gradient(cmap=colormap, subset=['Count'])
            .set_properties(**{'text-align': 'left'}),
            use_container_width=True
        )
    except Exception as e:
        st.warning(f"Couldn't analyze common words: {str(e)}")

# --- Main App UI ---
def main():
    # Initialize session state
    if 'show_stats' not in st.session_state:
        st.session_state.show_stats = True
    if 'show_wordcloud' not in st.session_state:
        st.session_state.show_wordcloud = True
    if 'show_common_words' not in st.session_state:
        st.session_state.show_common_words = True
    
    # Header
    st.title("🎶 Taylor Swift Lyrics Explorer")
    st.markdown("""
        <div style='text-align: center; margin-bottom: 2rem;'>
            Discover lyrics and visualize word patterns from Taylor Swift's songs.<br>
            Enter a song title below to get started!
        </div>
    """, unsafe_allow_html=True)
    
    # Search input
    col1, col2 = st.columns([3, 1])
    with col1:
        song_title = st.text_input("Enter a Taylor Swift song title:", "Love Story")
    with col2:
        st.markdown("<div style='height: 27px'></div>", unsafe_allow_html=True)
        search_btn = st.button("🔍 Search Lyrics", use_container_width=True)
    
    # Process search
    if search_btn or song_title:
        with st.spinner(f"Searching for '{song_title}'..."):
            try:
                song = search_song_with_retry(song_title, "Taylor Swift")
                
                if song:
                    # Display song header
                    st.markdown(f"""
                        <div style='text-align: center; margin: 1rem 0 2rem 0;'>
                            <h2>{song.title}</h2>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Create tabs
                    tab1, tab2 = st.tabs(["📜 Lyrics", "📊 Analysis"])
                    
                    with tab1:
                        with st.container():
                            st.markdown("""
                                <div style='
                                    background: #f8f9fa;
                                    border-radius: 10px;
                                    padding: 20px;
                                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                                '>
                            """, unsafe_allow_html=True)
                            st.text_area("", song.lyrics, height=400, label_visibility="collapsed")
                            st.markdown("</div>", unsafe_allow_html=True)
                    
                    with tab2:
                        if st.session_state.show_stats:
                            st.subheader("📈 Lyrics Statistics")
                            display_lyrics_stats(song.lyrics)
                            st.markdown("---")
                        
                        if st.session_state.show_wordcloud:
                            st.subheader("☁️ Word Cloud")
                            generate_word_cloud(song.lyrics, max_words, background_color, colormap)
                            st.markdown("---")
                        
                        if st.session_state.show_common_words:
                            st.subheader("📊 Most Common Words")
                            display_common_words(song.lyrics)
                else:
                    st.error("Song not found. Please check the title and try again.")
                    st.info("💡 Try exact song titles like 'All Too Well (10 Minute Version)'")
            
            except Exception as e:
                if "403" in str(e):
                    st.error("""
                        Access denied by Genius API (403 Forbidden). Possible reasons:
                        - Invalid API token
                        - Rate limit exceeded
                        - Temporary API issues
                        
                        Try again later or check your environment variables.
                    """)
                else:
                    st.error(f"An error occurred: {str(e)}")

# --- Sidebar Configuration ---
with st.sidebar:
    st.header("🎛️ Customization Options")
    with st.expander("Display Settings", expanded=True):
        st.session_state.show_stats = st.checkbox("Show statistics", st.session_state.show_stats)
        st.session_state.show_wordcloud = st.checkbox("Show word cloud", st.session_state.show_wordcloud)
        st.session_state.show_common_words = st.checkbox("Show common words", st.session_state.show_common_words)
    
    with st.expander("Word Cloud Settings", expanded=True):
        max_words = st.slider("Max words", 50, 300, 150, help="Maximum number of words to display in the word cloud")
        background_color = st.color_picker("Background color", "#ffffff")
        colormap = st.selectbox(
            "Color scheme",
            ["viridis", "plasma", "inferno", "magma", "cividis", "twilight", "hsv", "autumn", "winter"],
            index=2
        )
    
    st.markdown("---")
    st.markdown("""
        <div style='text-align: center;'>
            <small>Made with ❤️ by Swifties</small><br>
            <small>Data from Genius API</small>
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()