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
    """Use AI to extract transactions from PDF text - optimized for large statements"""
    
    # Step 1: First, ask AI to identify where transactions are
    preview = pdf_text[:3000]  # Quick preview
    
    identification_prompt = f"""Analyze this bank statement preview and tell me:
1. Does this section contain actual transactions?
2. What keywords indicate transaction sections? (e.g., "Transactions", "Activity", "Purchases")

Preview:
{preview}

Reply in JSON format:
{{"has_transactions": true/false, "section_keywords": ["keyword1", "keyword2"]}}"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a document analyzer. Identify transaction sections."},
                {"role": "user", "content": identification_prompt}
            ],
            temperature=0,
            max_tokens=200
        )
        
        result = response.choices[0].message.content.strip()
        if result.startswith("```json"):
            result = result.replace("```json", "").replace("```", "").strip()
        
        identification = json.loads(result)
        section_keywords = identification.get("section_keywords", [])
        
    except:
        section_keywords = ["transactions", "activity", "details", "purchases"]
    
    # Step 2: Extract relevant sections containing transactions
    lines = pdf_text.split('\n')
    transaction_section = []
    in_transaction_section = False
    
    for line in lines:
        line_lower = line.lower()
        
        # Check if we're entering a transaction section
        if any(keyword in line_lower for keyword in section_keywords):
            in_transaction_section = True
        
        # Check if we're leaving (common end markers)
        if any(marker in line_lower for marker in ["interest information", "important information", "in case of errors"]):
            if in_transaction_section and len(transaction_section) > 50:
                # Continue a bit more to catch remaining transactions
                transaction_section.append(line)
                continue
        
        if in_transaction_section:
            transaction_section.append(line)
    
    # If we found a section, use it; otherwise use full text
    relevant_text = '\n'.join(transaction_section) if transaction_section else pdf_text
    
    # Step 3: Process in manageable chunks
    max_chars = 12000  # Increased chunk size for efficiency
    all_transactions = []
    
    text_chunks = [relevant_text[i:i+max_chars] for i in range(0, len(relevant_text), max_chars)]
    
    # Limit to reasonable number of chunks (prevents excessive API calls for massive docs)
    max_chunks = 10  # Handles ~120,000 characters (typically 40-60 pages of transactions)
    
    for idx, chunk in enumerate(text_chunks[:max_chunks]):
        
        prompt = f"""Extract ALL transaction lines from this bank statement section.

A transaction line MUST have:
- A date (can be abbreviated like "Sep 9" or full "September 9")
- A merchant/vendor name or description
- An amount (dollars)

INCLUDE lines like:
- "Sep 10 Sep 11 ROGERS ******8621 888-764-3771 ON 185.98"
- "Oct 14 POS PURCHASE W/PIN ($130.02) AMAR CONVENIENCE MANTECA CA"
- "Nov 03 REAL TIME CREDIT $1,200.00 RTP CREDIT DALJIT SINGH"
- "001 Sep 9 Sep 10 LONDON DRUGS 17 DELTA BC 27.63"

EXCLUDE:
- Account summaries, headers, footers
- Balance information, totals, subtotals
- Page numbers, statement dates
- Terms and conditions
- Customer addresses
- Lines that only say "Continued" or "Page X of Y"

Text section {idx + 1}:
{chunk}

Return a JSON array of transaction strings: ["transaction1", "transaction2", ...]
Return [] if no transactions found.
JSON only, no markdown."""

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Extract transaction lines. Return valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                max_tokens=3000
            )
            
            result = response.choices[0].message.content.strip()
            
            # Clean markdown
            if result.startswith("```json"):
                result = result.replace("```json", "").replace("```", "").strip()
            elif result.startswith("```"):
                result = result.replace("```", "").strip()
            
            transactions = json.loads(result)
            if isinstance(transactions, list):
                all_transactions.extend(transactions)
            
        except Exception as e:
            print(f"Error in chunk {idx + 1}: {e}")
            continue
    
    # Remove duplicates and empty strings
    unique_transactions = list(set([t.strip() for t in all_transactions if t.strip()]))
    
    return unique_transactions

def classify_with_gpt(transaction, expected_categories):
    """Classify transaction using GPT"""
    prompt = f"""You are classifying credit card/bank transactions as either 'Expected' or 'Unexpected'.

The user expects spending in these categories: {', '.join(expected_categories)}.

Map merchants intelligently:
- Grocery stores (Thrifty Foods, Safeway, Walmart grocery, Whole Foods, etc.) → groceries
- Gas stations (Chevron, Esso, Shell, Arco, etc.) → gas
- Restaurants, cafes, food delivery, sweets shops → dining or food or food pickup
- Streaming services (Netflix, Spotify, Apple Music, etc.) → media
- Phone/internet bills (Rogers, Telus, Verizon, AT&T, etc.) → bills
- Pharmacies (London Drugs, CVS, Walgreens, etc.) → medical
- Amazon, online retailers → online shopping
- Parking, airports, hotels → travel
- Car services, automotive → travel or maintenance
- One-time government fees (passport, immigration) → check if user has custom categories for these
- Clothing stores, fashion → online shopping or entertainment
- Banks, financial transfers → bills or money transfer

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
        "version": "2.0.0",
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
            # Check file size (optional - prevents very large files)
            file_size_mb = os.path.getsize(filepath) / (1024 * 1024)
            
            if file_size_mb > 15:
                os.remove(filepath)
                return jsonify({
                    "error": "Statement too large. Please upload files smaller than 15MB.",
                    "suggestion": "Try splitting large statements into smaller files."
                }), 400
            
            # Extract text from PDF
            pdf_text = extract_text_from_pdf(filepath)
            
            if not pdf_text or len(pdf_text) < 50:
                os.remove(filepath)
                return jsonify({"error": "Could not extract text from PDF"}), 400
            
            # Use AI to extract transactions
            transactions = extract_transactions_with_ai(pdf_text)
            
            if len(transactions) == 0:
                os.remove(filepath)
                return jsonify({"error": "No transactions found in PDF. Please ensure the PDF contains transaction details."}), 400
            
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