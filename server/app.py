from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import pdfplumber
import re
import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app, resources={
    r"/api/*": {
        "origins": ["https://spending-spotlight-three.vercel.app", "http://localhost:3000"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_transactions(pdf_path):
    """Extract transaction lines from PDF"""
    text = ""
    
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    
    text = text.lower()
    month_abbr = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
    exclude_keywords = [
        "balance", "statement", "page", "account", "minimum", "summary",
        "interest", "credit", "limit", "please", "visit", "payment due"
    ]
    
    lines = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if any(bad in line for bad in exclude_keywords):
            continue
        # Look for date + amount pattern
        if any(month in line for month in month_abbr) and re.search(r"\$?\d{1,4}(\.\d{2})?", line):
            lines.append(line)
    
    return lines

def classify_with_gpt(line, expected_categories):
    """Classify transaction using GPT"""
    prompt = f"""You are classifying credit card transactions as either 'Expected' or 'Unexpected'.

The user expects spending in these categories: {', '.join(expected_categories)}.

Map merchants to categories smartly, for example:
- 'London Drugs' → medical
- 'Thrifty Foods' → groceries
- 'Netflix' → media
- 'Chevron', 'Esso' → gas
- 'Amazon', 'Amzn Mktp' → online shopping
- 'Concord Parking', 'Airport Parking' → travel
- Restaurants → dining or food

Classify this transaction: "{line}"

Reply ONLY with: Expected or Unexpected."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a financial assistant that classifies transactions."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            max_tokens=10
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error classifying transaction: {e}")
        return "Unexpected"  # Default to unexpected if error

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "Server is running!", "version": "1.0.0"})

@app.route('/api/analyze', methods=['POST'])
def analyze_pdf():
    """Analyze uploaded PDF and classify transactions"""
    try:
        # Check if file was uploaded
        if 'pdf' not in request.files:
            return jsonify({"error": "No PDF file uploaded"}), 400
        
        file = request.files['pdf']
        
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        if not allowed_file(file.filename):
            return jsonify({"error": "Only PDF files are allowed"}), 400
        
        # Get selected categories
        categories = request.form.get('categories', '[]')
        import json
        categories = json.loads(categories)
        
        if len(categories) == 0:
            return jsonify({"error": "No categories selected"}), 400
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            # Extract transactions
            transactions = extract_transactions(filepath)
            
            if len(transactions) == 0:
                os.remove(filepath)
                return jsonify({"error": "No transactions found in PDF"}), 400
            
            # Classify transactions
            expected = []
            unexpected = []
            
            for transaction in transactions:
                result = classify_with_gpt(transaction, categories)
                
                if result.lower().startswith("expected"):
                    expected.append({
                        "transaction": transaction,
                        "classification": "Expected"
                    })
                else:
                    unexpected.append({
                        "transaction": transaction,
                        "classification": "Unexpected"
                    })
            
            # Clean up uploaded file
            os.remove(filepath)
            
            return jsonify({
                "success": True,
                "totalTransactions": len(transactions),
                "expected": expected,
                "unexpected": unexpected
            })
            
        except Exception as e:
            # Clean up file if error occurs
            if os.path.exists(filepath):
                os.remove(filepath)
            raise e
            
    except Exception as e:
        print(f"Error analyzing PDF: {e}")
        return jsonify({
            "error": "Failed to analyze PDF",
            "details": str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)