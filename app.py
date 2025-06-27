import streamlit as st
import lyricsgenius
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import pandas as pd
import os
from PIL import Image
import requests
from io import BytesIO

# --- Page Configuration ---
st.set_page_config(
    page_title="Taylor Swift Lyrics Explorer",
    page_icon="🎤",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS for Styling ---
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

try:
    local_css("style.css")
except FileNotFoundError:
    st.warning("Custom CSS file not found - using default styles")

# --- Genius API Setup ---
@st.cache_data
def get_genius_client():
    GENIUS_TOKEN = st.secrets.get("GENIUS_TOKEN", os.getenv("GENIUS_TOKEN"))
    if not GENIUS_TOKEN:
        st.error("Please set GENIUS_TOKEN in secrets.toml or environment variables")
        st.stop()
    genius = lyricsgenius.Genius(GENIUS_TOKEN)
    genius.verbose = False
    genius.remove_section_headers = True
    genius.skip_non_songs = True
    genius.excluded_terms = ["(Remix)", "(Live)"]
    return genius

genius = get_genius_client()

# --- App Header ---
header_image = st.image(
    "https://upload.wikimedia.org/wikipedia/commons/thumb/2/26/Taylor_Swift_-_Speak_Now_Tour_1_%28cropped%29.jpg/1200px-Taylor_Swift_-_Speak_Now_Tour_1_%28cropped%29.jpg", 
    caption="Taylor Swift Lyrics Explorer",
    use_container_width=True  # Updated parameter
)

st.title("🎶 Taylor Swift Lyrics Explorer")
st.markdown("""
    <div style='text-align: center; margin-bottom: 2rem;'>
        Discover lyrics and visualize word patterns from Taylor Swift's songs.<br>
        Enter a song title below to get started!
    </div>
""", unsafe_allow_html=True)

# --- Main App Functions ---
def get_song_artwork(url):
    try:
        response = requests.get(url, timeout=10)
        img = Image.open(BytesIO(response.content))
        return img
    except Exception as e:
        st.warning(f"Couldn't load artwork: {str(e)}")
        return None

def generate_word_cloud(lyrics, max_words, background_color, colormap):
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
    st.pyplot(fig, use_container_width=True)  # Updated parameter

def display_lyrics_stats(lyrics):
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

def display_common_words(lyrics):
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
        use_container_width=True  # Updated parameter
    )

# --- Main App Logic ---
def main():
    col1, col2 = st.columns([3, 1])
    with col1:
        song_title = st.text_input("Enter a Taylor Swift song title:", "Love Story")
    with col2:
        st.markdown("<div style='height: 27px'></div>", unsafe_allow_html=True)
        search_btn = st.button("🔍 Search Lyrics", use_container_width=True)
    
    if search_btn or song_title:
        with st.spinner(f"Searching for '{song_title}'..."):
            try:
                artist = genius.search_artist("Taylor Swift", max_songs=0)
                song = genius.search_song(song_title, artist.name)
                
                if song:
                    # Display song header
                    st.markdown(f"""
                        <div style='text-align: center; margin: 1rem 0 2rem 0;'>
                            <h2>{song.title}</h2>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Create tabs for different views
                    tab1, tab2 = st.tabs(["📜 Lyrics", "📊 Analysis"])
                    
                    with tab1:
                        # Display lyrics in a card
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
                        if 'show_stats' not in st.session_state or st.session_state.show_stats:
                            st.subheader("📈 Lyrics Statistics")
                            display_lyrics_stats(song.lyrics)
                            st.markdown("---")
                        
                        if 'show_wordcloud' not in st.session_state or st.session_state.show_wordcloud:
                            st.subheader("☁️ Word Cloud")
                            generate_word_cloud(song.lyrics, max_words, background_color, colormap)
                            st.markdown("---")
                        
                        if 'show_common_words' not in st.session_state or st.session_state.show_common_words:
                            st.subheader("📊 Most Common Words")
                            display_common_words(song.lyrics)
                
                else:
                    st.error("Song not found. Please check the title and try again.")
                    st.info("💡 Try exact song titles like 'All Too Well (10 Minute Version)'")
            
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                st.warning("If you see API rate limit errors, please wait a minute and try again.")

if __name__ == "__main__":
    # Initialize session state variables if they don't exist
    if 'show_stats' not in st.session_state:
        st.session_state.show_stats = True
    if 'show_wordcloud' not in st.session_state:
        st.session_state.show_wordcloud = True
    if 'show_common_words' not in st.session_state:
        st.session_state.show_common_words = True
    
    # Get sidebar options
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
    
    main()