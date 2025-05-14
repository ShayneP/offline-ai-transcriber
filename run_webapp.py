from app.web_app import app

if __name__ == "__main__":
    print("Starting Voice Transcripts Web App...")
    print("Open http://localhost:5003 in your browser to view transcripts")
    app.run(debug=True, host='0.0.0.0', port=5003)