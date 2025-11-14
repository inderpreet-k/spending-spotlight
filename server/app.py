from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import pdfplumber
import os
from openai import OpenAI
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

app = Flask(__name__)

# CORS Configuration
CORS(app, origins="*", supports_credentials=True)

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

def extract_text_from_pdf(pdf_path):
    """Extract all text from PDF"""
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

def extract_transactions_with_ai(pdf_text):
    """Use AI to extract transactions from PDF text"""
    
    prompt = f"""You are analyzing a bank or credit card statement. Extract ONLY the actual transaction lines.

Rules:
1. Extract lines that represent actual purchases, payments, or charges
2. EXCLUDE: headers, footers, account summaries, balances, addresses, date ranges, subtotals, interest charges summaries, page numbers
3. Each transaction should have: a date, merchant/description, and amount
4. Include the FULL transaction line exactly as it appears
5. If you see patterns like "LONDON DRUGS", "NETFLIX", "CHEVRON", "AMAZON", etc. - these are transactions
6. Skip lines like "Beginning Balance", "Ending Balance", "Total Credits", "Statement Period", addresses, etc.

Here is the statement text:

{pdf_text[:4000]}

Return ONLY a JSON array of transaction strings. Example format:
["sep 9 sep 10 london drugs 17 delta bc 27.63", "sep 10 sep 11 rogers ******8621 888-764-3771 on 185.98"]

If the text is longer, focus on the transaction section. Return only valid JSON, no markdown or explanation."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a financial document analyzer. Extract only transaction lines from bank statements. Return valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            max_tokens=2000
        )
        
        result = response.choices[0].message.content.strip()
        
        # Remove markdown code blocks if present
        if result.startswith("```json"):
            result = result.replace("```json", "").replace("```", "").strip()
        elif result.startswith("```"):
            result = result.replace("```", "").strip()
        
        transactions = json.loads(result)
        return transactions if isinstance(transactions, list) else []
        
    except Exception as e:
        print(f"Error extracting transactions with AI: {e}")
        return []

def classify_with_gpt(transaction, expected_categories):
    """Classify transaction using GPT"""
    prompt = f"""You are classifying credit card/bank transactions as either 'Expected' or 'Unexpected'.

The user expects spending in these categories: {', '.join(expected_categories)}.

Map merchants intelligently:
- Grocery stores (Thrifty Foods, Safeway, Walmart grocery, etc.) → groceries
- Gas stations (Chevron, Esso, Shell, etc.) → gas
- Restaurants, cafes, food delivery → dining or food
- Streaming services (Netflix, Spotify, etc.) → media
- Phone/internet bills (Rogers, Telus, etc.) → bills
- Pharmacies (London Drugs, CVS, Walgreens) → medical
- Amazon, online retailers → online shopping
- Parking, airports, hotels → travel
- One-time government fees (passport, immigration) → if user selected those custom categories

Transaction: "{transaction}"

Reply with ONLY one word: Expected or Unexpected"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a financial assistant. Classify transactions accurately."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            max_tokens=10
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error classifying: {e}")
        return "Unexpected"

@app.route('/', methods=['GET'])
def home():
    """Root endpoint"""
    return jsonify({
        "message": "Spending Spotlight API",
        "status": "running",
        "endpoints": {
            "health": "/api/health",
            "analyze": "/api/analyze (POST)"
        }
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "Server is running!", "version": "2.0.0"})

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
        categories = json.loads(categories)
        
        if len(categories) == 0:
            return jsonify({"error": "No categories selected"}), 400
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            # Extract text from PDF
            pdf_text = extract_text_from_pdf(filepath)
            
            if not pdf_text or len(pdf_text) < 50:
                os.remove(filepath)
                return jsonify({"error": "Could not extract text from PDF"}), 400
            
            # Use AI to extract transactions
            transactions = extract_transactions_with_ai(pdf_text)
            
            if len(transactions) == 0:
                os.remove(filepath)
                return jsonify({"error": "No transactions found in PDF"}), 400
            
            # Classify transactions with GPT
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