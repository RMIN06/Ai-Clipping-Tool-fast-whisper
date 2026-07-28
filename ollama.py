import subprocess
import time
import os

print("Downloading Ollama...")
os.system("curl -fsSL https://ollama.com/install.sh | sh")

print("Starting Ollama server...")
# Start server in background
subprocess.Popen(['ollama', 'serve'])
time.sleep(5)

print("Pulling Llama 3.2 model (this takes a minute)...")
os.system("ollama pull llama3.2")

print("\nServer is running! Move to Cell 3.")