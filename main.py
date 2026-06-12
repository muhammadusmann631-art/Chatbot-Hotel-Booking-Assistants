from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import sqlite3
import os
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import re

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("⚠ WARNING: GEMINI_API_KEY not found in .env file!")
else:
    print(f"✅ API Key loaded successfully!")

app = FastAPI(title="Multi-Purpose Chatbot with Web Scraping")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = "chatbot_data.db"
SCRAPE_TIMEOUT = 10  # FIXED: Defined timeout

# ========== DATABASE INITIALIZATION ==========
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            phone TEXT,
            address TEXT,
            message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_message TEXT,
            bot_reply TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS company_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT UNIQUE,
            website_url TEXT,
            scraped_content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()

# ========== DATABASE FUNCTIONS ==========
def save_chat(user_msg, bot_reply):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO chat_history (user_message, bot_reply) VALUES (?, ?)", 
                   (user_msg, bot_reply))
    conn.commit()
    conn.close()

def save_booking_db(name, email, phone, address, message):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO bookings (name, email, phone, address, message) VALUES (?, ?, ?, ?, ?)", 
                   (name, email, phone, address, message))
    conn.commit()
    conn.close()

def get_all_bookings():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email, phone, address, message, created_at FROM bookings ORDER BY created_at DESC")
    bookings = cursor.fetchall()
    conn.close()
    return bookings

def save_company_data(company_name, website_url, scraped_content):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO company_data (company_name, website_url, scraped_content, updated_at)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
    """, (company_name, website_url, scraped_content))
    conn.commit()
    conn.close()

def get_company_data(company_name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT website_url, scraped_content FROM company_data WHERE company_name = ?", 
                   (company_name,))
    result = cursor.fetchone()
    conn.close()
    return result

def get_all_companies():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT company_name, website_url, created_at FROM company_data ORDER BY created_at DESC")
    companies = cursor.fetchall()
    conn.close()
    return companies

# ========== IMPROVED WEB SCRAPING FUNCTION ==========
def clean_text(text: str) -> str:
    """Clean and normalize text"""
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove special characters but keep basic punctuation
    text = re.sub(r'[^\w\s\.\,\!\?\-\:\;]', '', text)
    return text.strip()

def scrape_website_improved(name, url):
    if not url.startswith("http"):
        url = "https://" + url
    url = url.rstrip("/")
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, timeout=SCRAPE_TIMEOUT, headers=headers)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')

        desc = ""
        meta = soup.find("meta", {"name": re.compile("description", re.I)})
        if meta and (content := meta.get("content")):
            desc = clean_text(content)
        else:
            for p in soup.find_all("p"):
                txt = clean_text(p.get_text())
                if txt and 30 < len(txt) < 500:
                    desc = txt
                    break
            if not desc:
                desc = f"Welcome to {name}!"

        logo = None
        for sel in [
            "img[alt*='logo' i]", ".logo img", "header img",
            'link[rel="icon"]', 'link[rel="shortcut icon"]',
            'meta[property="og:image"]'
        ]:
            tag = soup.select_one(sel)
            if tag:
                src = tag.get("src") or tag.get("href") or tag.get("content")
                if src:
                    logo = urljoin(url, src)
                    break

        body = soup.find("body")
        context = clean_text(body.get_text())[:4000] if body else f"{name} website."

        # FIXED: Return string for scraped_content (main context)
        return context or desc or f"Welcome to {name}! Visit {url} for more info."
        
    except Exception as e:
        print(f"Website load nahi hui: {str(e)}")  # FIXED: No st.warning
        return f"{name} is at {url}. Limited info available."

# ========== GEMINI API CALL ==========
def call_gemini_api(prompt: str) -> str:
    if not GEMINI_API_KEY:
        return "Main abhi kaam nahi kar sakta. Admin se API key setup karne ko kaho. 🔧"
    
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}]
        }

        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            answer = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            if answer:
                return answer.strip()
            return "Maaf kijiye, main abhi answer nahi de sakta. 🙏"
        else:
            return "Sorry, main abhi thoda slow hoon. Dobara try karein please! 😊"
            
    except Exception as e:
        print(f"❌ API Error: {str(e)}")
        return "Kuch technical problem aa gayi hai. Thodi der baad try karein. 🔧"

# ========== INTELLIGENT ANSWER FUNCTION ==========
def get_answer(question: str, hotel_knowledge: str, company_name: str = None) -> str:
    """
    SMART multi-purpose chatbot with STRICT context separation
    """
    try:
        # Step 1: Detect what user is asking about
        question_lower = question.lower()
        
        # Hotel keywords detection
        hotel_keywords = ['hotel', 'room', 'booking', 'book', 'reserve', 'stay', 
                         'facility', 'price', 'rate', 'suite', 'deluxe', 'standard',
                         'presidential', 'executive']
        is_hotel_query = any(keyword in question_lower for keyword in hotel_keywords)
        
        # Company keywords detection (only if company selected)
        company_keywords = ['company', 'startup', 'program', 'incubation', 'apply',
                           'admission', 'mentorship', 'plan9', 'pitb', 'suzuki', 
                           'wagonr', 'alto', 'cultus', 'motorcycle', company_name.lower() if company_name else '']
        is_company_query = company_name and any(keyword in question_lower for keyword in company_keywords)
        
        # Step 2: Build appropriate prompt based on detection
        
        # CASE 1: HOTEL QUERY
        if is_hotel_query:
            prompt = f"""You are a hotel assistant for Grand Palace Hotel.

HOTEL INFORMATION:
{hotel_knowledge}

USER QUESTION: {question}

INSTRUCTIONS:
- Answer ONLY about the hotel using the information above
- Give accurate room prices and details
- Be professional and helpful
- If discussing booking, end with: "Kya aap booking karna chahenge?"
- Use the same language as the question (Roman Urdu or English)

Answer:"""
            return call_gemini_api(prompt)
        
        # CASE 2: COMPANY QUERY (only if company selected AND company mentioned)
        elif is_company_query:
            result = get_company_data(company_name)
            if result and result[1]:
                company_data = result[1]
                prompt = f"""You are an assistant for {company_name}.

COMPANY INFORMATION:
{company_data}

USER QUESTION: {question}

INSTRUCTIONS:
- Answer ONLY about {company_name} using the information above
- Be accurate and professional
- If information not available, say so honestly
- Use the same language as the question

Answer:"""
                return call_gemini_api(prompt)
            else:
                return f"Sorry, {company_name} ke baare mein information nahi hai database mein."
        
        # CASE 3: GENERAL KNOWLEDGE QUERY (default)
        else:
            prompt = f"""You are a helpful AI assistant with knowledge about science, technology, programming, and general topics.

USER QUESTION: {question}

INSTRUCTIONS:
- Answer using your general AI knowledge
- Be educational, accurate and helpful
- Cover topics like: ML, NLP, computers, science, history, coding, etc.
- Use the same language as the question (Roman Urdu or English)
- Keep it conversational and friendly

Answer:"""
            return call_gemini_api(prompt)

    except Exception as e:
        print(f"Error in get_answer: {e}")
        return "Sorry, kuch technical issue aa gaya. Please try again."

# ========== PYDANTIC MODELS ==========
class ChatRequest(BaseModel):
    message: str
    hotel_knowledge: str
    company_name: str | None = None

class BookingRequest(BaseModel):
    name: str
    email: str
    phone: str
    address: str
    message: str | None = None

class CompanyRequest(BaseModel):
    company_name: str
    website_url: str

# ========== API ROUTES ==========
@app.get("/")
def root():
    return {"message": "✅ USMAN 2 BAJ KE 6", "version": "2.0"}

@app.post("/api/chat")
async def chat(req: ChatRequest):
    print(f"❓ Question: {req.message}")
    print(f"🏢 Company: {req.company_name if req.company_name else 'None (Hotel mode)'}")
    
    if not req.message.strip():
        return {"answer": "Question khali hai!"}
    
    answer = await asyncio.to_thread(
        get_answer, 
        req.message, 
        req.hotel_knowledge,
        req.company_name
    )
    
    # Save to history
    await asyncio.to_thread(save_chat, req.message, answer)
    
    return {"answer": answer}

@app.post("/api/save_booking")
async def save_booking_route(req: BookingRequest):
    await asyncio.to_thread(save_booking_db, req.name, req.email, req.phone, 
                           req.address, req.message or "")
    return {"status": "Booking saved successfully"}

@app.get("/api/get_bookings")
async def get_bookings_route():
    bookings = await asyncio.to_thread(get_all_bookings)
    booking_list = []
    for b in bookings:
        booking_list.append({
            "id": b[0],
            "name": b[1],
            "email": b[2],
            "phone": b[3],
            "address": b[4],
            "message": b[5],
            "created_at": b[6]
        })
    return {"bookings": booking_list}

@app.post("/api/add_company")
async def add_company(req: CompanyRequest):
    """
    Add company with IMPROVED scraping
    """
    try:
        print(f"🌐 Adding company: {req.company_name}")
        print(f"🔗 URL: {req.website_url}")
        
        # Validate URL
        if not req.website_url.startswith(('http://', 'https://')):
            raise HTTPException(
                status_code=400, 
                detail="URL must start with http:// or https://"
            )
        
        # FIXED: Pass name to scraper, get string content
        scraped_dict = await asyncio.to_thread(
            scrape_website_improved, 
            req.company_name,
            req.website_url
        )
        scraped_content = scraped_dict  # Now it's a string
        
        # Check if good content
        if len(scraped_content) < 200:
            await asyncio.to_thread(
                save_company_data, 
                req.company_name, 
                req.website_url, 
                scraped_content
            )
            return {
                "status": "partial_success",
                "message": f"⚠ {req.company_name} saved but limited data scraped",
                "content_length": len(scraped_content),
                "warning": True,
                "details": "Website ne full access nahi di. Limited knowledge available."
            }
        
        await asyncio.to_thread(
            save_company_data, 
            req.company_name, 
            req.website_url, 
            scraped_content
        )
        
        return {
            "status": "success",
            "message": f"✅ {req.company_name} successfully added!",
            "content_length": len(scraped_content),
            "warning": False
        }
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        print(f"❌ {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)

@app.get("/api/get_companies")
async def get_companies_route():
    companies = await asyncio.to_thread(get_all_companies)
    company_list = []
    for c in companies:
        company_list.append({
            "name": c[0],
            "url": c[1],
            "created_at": c[2]
        })
    return {"companies": company_list}

@app.get("/api/get_company/{company_name}")
async def get_company_info(company_name: str):
    result = await asyncio.to_thread(get_company_data, company_name)
    if result:
        return {
            "company_name": company_name,
            "website_url": result[0],
            "content_length": len(result[1]),
            "has_content": len(result[1]) > 300
        }
    return {"error": "Company not found"}

# Initialize on startup
init_db()
print("="*60)
print("✅ FIXED MULTI-PURPOSE CHATBOT READY!")
print("🏨 Hotel System: Active")
print("🌐 Web Scraping: Fixed & Working")
print("🤖 General AI: Active")
print("="*60)