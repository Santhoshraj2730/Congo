import os  
from app import app  

if __name__ == "__main__":  
    port = int(os.environ.get("PORT", 4000))  # Default to 5000 locally  
    app.run(host="0.0.0.0", port=port, debug=True)  
