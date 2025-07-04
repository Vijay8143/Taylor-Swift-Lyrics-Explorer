# Taylor Swift Lyrics Explorer

![App Screenshot](https://upload.wikimedia.org/wikipedia/commons/thumb/2/26/Taylor_Swift_-_Speak_Now_Tour_1_%28cropped%29.jpg/1200px-Taylor_Swift_-_Speak_Now_Tour_1_%28cropped%29.jpg)

A Streamlit web application that fetches Taylor Swift song lyrics and generates interactive visualizations.

## Features

- 🎵 Fetch lyrics for any Taylor Swift song
- ☁️ Generate customizable word clouds
- 📊 View song statistics (word count, unique words)
- 🔍 Analyze most frequent words
- 🎨 Custom color schemes and settings

## Prerequisites

- Python 3.8+
- Genius API token
- Streamlit

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/taylor-swift-lyrics.git
cd taylor-swift-lyrics
```
2.Install dependencies:
```bash
pip install -r requirements.txt
```
3.Set up environment:
```bash
echo "GENIUS_TOKEN=your_api_token_here" > .env
```
4.Run the application:
```bash
streamlit run app.py
```

---

## Project Structure
```bash
taylor-swift-lyrics/
├── app.py            # Main application code
├── style.css         # Custom styling
├── requirements.txt  # Python dependencies
└── README.md         # Project documentation
```

