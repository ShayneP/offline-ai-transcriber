# Vox-Box Quickstart

We need vox-box to have it's own venv because there's conflicts with some of the other libraries. Hopefully this won't always be needed, but it is for now.

1. Create a virtual environment in this directory:
   ```sh
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```

3. Start the server:
   ```sh
   vox-box start --huggingface-repo-id Systran/faster-whisper-small --data-dir ./cache/data-dir --host 0.0.0.0 --port 5002
   ```

From here, your agent will be able to connect to the server for local transcriptions.