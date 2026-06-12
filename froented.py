import streamlit as st
import requests
import time

API_URL = "http://127.0.0.1:5050"

st.set_page_config(page_title="Multi-Purpose Chatbot 🤖", layout="wide")

# ✅ Black Theme with Modern Design
st.markdown("""
<style>
    .main { background: #000000; }
    .stApp { background: #000000; }
    .chat-container {
        background: #1a1a1a;
        padding: 20px;
        border-radius: 20px;
        box-shadow: 0 8px 32px rgba(255,255,255,0.1);
        margin-bottom: 20px;
        border: 1px solid #333;
    }
    .user-msg {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 12px 18px;
        border-radius: 18px 18px 5px 18px;
        margin: 10px 0;
        margin-left: 20%;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    }
    .bot-msg {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 12px 18px;
        border-radius: 18px 18px 18px 5px;
        margin: 10px 0;
        margin-right: 20%;
        box-shadow: 0 4px 12px rgba(245, 87, 108, 0.3);
    }
    .booking-box {
        background: #1a1a1a;
        border: 2px solid #667eea;
        padding: 30px;
        border-radius: 20px;
        box-shadow: 0 8px 30px rgba(102, 126, 234, 0.3);
    }
    .company-card {
        background: #1a1a1a;
        border: 2px solid #4facfe;
        padding: 20px;
        border-radius: 15px;
        margin: 10px 0;
        box-shadow: 0 4px 15px rgba(79, 172, 254, 0.3);
    }
    .booking-prompt {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        color: white;
        padding: 20px;
        border-radius: 15px;
        margin: 20px 0;
        text-align: center;
        font-weight: 600;
        box-shadow: 0 4px 15px rgba(79, 172, 254, 0.4);
    }
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 12px 30px;
        font-weight: 600;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.5);
    }
    h1, h2, h3, h4, h5, h6 { color: white !important; }
    .stTextInput>div>div>input {
        background: #1a1a1a;
        color: white;
        border-radius: 25px;
        border: 2px solid #667eea;
        padding: 12px 20px;
    }
    .stTextArea>div>div>textarea {
        background: #1a1a1a;
        color: white;
        border-radius: 15px;
        border: 2px solid #667eea;
    }
    label { color: white !important; }
    p { color: #cccccc; }
    .success-msg {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        color: white;
        padding: 20px;
        border-radius: 15px;
        margin: 20px 0;
        text-align: center;
        font-size: 18px;
        font-weight: 600;
    }
    div[data-testid="stSidebar"] { background: #0a0a0a; }
</style>
""", unsafe_allow_html=True)

# ========== SESSION STATE ==========
if "messages" not in st.session_state:
    st.session_state.messages = []
    
if "hotel_knowledge" not in st.session_state:
    st.session_state.hotel_knowledge = """
🏨 Welcome to Grand Palace Hotel - Your Luxury Home in Karachi! 

📍 About Our Hotel:
Grand Palace Hotel ek premium 5-star luxury hotel hai jo Karachi ke main Shahrah-e-Faisal par located hai. Humara hotel 2010 mein open hua aur ab Pakistan ka top-rated hotel ban gaya hai. Har saal 50,000+ guests humare hotel ko choose karte hain apni comfortable stay ke liye.

🛏 Our Rooms (Total 150 Rooms Available):
1. Standard Room - Rs. 15,000 per night (5 Rooms)
2. Deluxe Room - Rs. 25,000 per night (4 Rooms)
3. Executive Suite - Rs. 45,000 per night (3 Rooms)
4. Presidential Suite - Rs. 85,000 per night (2 Rooms)

🌟 Facilities:
- 24/7 Room Service, Free WiFi, Swimming Pool
- Modern Gym & Spa, 3 Restaurants, Wedding Hall
- Free Parking, Airport Pickup/Drop

📞 Contact: +92-21-1234567
Email: info@grandpalacehotel.com
"""

if "show_booking_form" not in st.session_state:
    st.session_state.show_booking_form = False
if "show_booking_prompt" not in st.session_state:
    st.session_state.show_booking_prompt = False
if "current_page" not in st.session_state:
    st.session_state.current_page = "chat"
if "selected_company" not in st.session_state:
    st.session_state.selected_company = None

# ========== SIDEBAR ==========
with st.sidebar:
    st.header("🎯 Navigation")
    
    if st.button("💬 Chat", use_container_width=True):
        st.session_state.current_page = "chat"
        st.rerun()
    
    if st.button("🌐 Manage Companies", use_container_width=True):
        st.session_state.current_page = "companies"
        st.rerun()
    
    if st.button("📋 View Bookings", use_container_width=True):
        st.session_state.current_page = "bookings"
        st.rerun()
    
    st.markdown("---")
    
    st.header("📚 Hotel Knowledge")
    st.write("Hotel ki information:")
    
    knowledge_input = st.text_area(
        "Hotel Knowledge:",
        value=st.session_state.hotel_knowledge,
        height=300,
        key="hotel_knowledge_input"
    )
    
    if st.button("💾 Save Hotel Knowledge", use_container_width=True):
        if knowledge_input.strip():
            st.session_state.hotel_knowledge = knowledge_input
            st.success("✅ Hotel knowledge saved!")
        else:
            st.error("⚠ Knowledge text empty hai!")

# ========== COMPANIES PAGE ==========
if st.session_state.current_page == "companies":
    st.title("🌐 Company Management System")
    
    st.markdown("### ➕ Add New Company")
    st.write("Company ka naam aur website URL daalein - automatic scraping hogi!")
    
    with st.form("add_company_form"):
        company_name = st.text_input("🏢 Company Name *", 
                                     placeholder="Example: Tech Solutions")
        website_url = st.text_input("🔗 Website URL *", 
                                    placeholder="https://example.com")
        
        submit_company = st.form_submit_button("🚀 Scrape & Add Company", 
                                               use_container_width=True)
        
        if submit_company:
            if not company_name or not website_url:
                st.error("⚠ Company name aur URL dono required hain!")
            elif not website_url.startswith(('http://', 'https://')):
                st.error("⚠ URL must start with http:// or https://")
            else:
                with st.spinner(f"🔍 Scraping {website_url}... Thoda wait karein..."):
                    try:
                        response = requests.post(
                            f"{API_URL}/api/add_company",
                            json={"company_name": company_name, "website_url": website_url},
                            timeout=60  # Increased timeout
                        )
                        
                        if response.status_code == 200:
                            data = response.json()
                            
                            # Check if there's a warning
                            if data.get("warning", False):
                                st.warning(data['message'])
                                st.info(f"📊 Content scraped: {data['content_length']} characters")
                                st.info("💡 Tip: Kuch websites JavaScript heavy hoti hain ya scraping block karti hain. Aap phir bhi use kar sakte hain lekin limited knowledge hogi.")
                            else:
                                st.success(f"✅ {data['message']}")
                                st.info(f"📊 Total content scraped: {data['content_length']} characters")
                                st.balloons()
                            
                            time.sleep(2)
                            st.rerun()
                        else:
                            error_data = response.json()
                            error_detail = error_data.get('detail', 'Unknown error')
                            st.error(f"❌ Error: {error_detail}")
                            
                            # Show helpful message
                            if "block" in error_detail.lower() or "javascript" in error_detail.lower():
                                st.info("💡 Ye website scraping allow nahi karti. Koi aur simple website try karein.")
                            
                    except requests.Timeout:
                        st.error("⏰ Scraping mein bahut time lag raha hai. Website slow hai ya block kar rahi hai.")
                    except requests.ConnectionError:
                        st.error("🌐 Internet connection issue. Check karein aur dobara try karein.")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
                        st.info("💡 Koi aur website URL try karein ya check karein ke URL sahi hai.")
    
    st.markdown("---")
    st.markdown("### 📂 Saved Companies")
    
    try:
        response = requests.get(f"{API_URL}/api/get_companies", timeout=10)
        if response.status_code == 200:
            data = response.json()
            companies = data.get("companies", [])
            
            if len(companies) == 0:
                st.info("📭 Koi company saved nahi hai abhi.")
            else:
                for company in companies:
                    st.markdown('<div class="company-card">', unsafe_allow_html=True)
                    st.markdown(f"### 🏢 {company['name']}")
                    st.write(f"🔗 URL:** {company['url']}")
                    st.write(f"📅 Added:** {company['created_at']}")
                    
                    if st.button(f"✅ Use {company['name']}", 
                                key=f"use_{company['name']}"):
                        st.session_state.selected_company = company['name']
                        st.session_state.current_page = "chat"
                        st.success(f"🎯 Now chatting as {company['name']}!")
                        time.sleep(1)
                        st.rerun()
                    
                    st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.error("❌ Could not load companies")
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

# ========== BOOKINGS PAGE ==========
elif st.session_state.current_page == "bookings":
    st.title("📋 Hotel Bookings")
    
    try:
        response = requests.get(f"{API_URL}/api/get_bookings", timeout=10)
        if response.status_code == 200:
            data = response.json()
            bookings = data.get("bookings", [])
            
            if len(bookings) == 0:
                st.info("❌ Koi booking nahi hai abhi tak.")
            else:
                st.success(f"✅ Total Bookings: {len(bookings)}")
                
                for booking in bookings:
                    st.markdown('<div class="company-card">', unsafe_allow_html=True)
                    st.markdown(f"### 🆔 Booking #{booking['id']}")
                    st.write(f"👤 Name:** {booking['name']}")
                    st.write(f"📧 Email:** {booking['email']}")
                    st.write(f"📞 Phone:** {booking['phone']}")
                    st.write(f"🏠 Address:** {booking['address']}")
                    st.write(f"💬 Message:** {booking['message']}")
                    st.write(f"📅 Date:** {booking['created_at']}")
                    st.markdown('</div>', unsafe_allow_html=True)
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

# ========== CHAT PAGE ==========
elif st.session_state.current_page == "chat":
    
    # Show selected company
    if st.session_state.selected_company:
        st.info(f"🎯 Currently chatting as: *{st.session_state.selected_company}*")
        if st.button("🏨 Switch to Hotel Mode"):
            st.session_state.selected_company = None
            st.rerun()
    else:
        st.info("🏨 Currently in Hotel Mode")
    
    # ========== BOOKING FORM ==========
    if st.session_state.show_booking_form:
        st.title("🏨 Hotel Room Booking Form")
        st.markdown('<div class="booking-box">', unsafe_allow_html=True)
        
        with st.form("booking_form"):
            booking_name = st.text_input("📛 Full Name *")
            booking_email = st.text_input("📧 Email *")
            booking_phone = st.text_input("📞 Phone *")
            booking_address = st.text_area("🏠 Address *")
            booking_message = st.text_area("💬 Special Requests")
            
            col1, col2 = st.columns(2)
            with col1:
                submit = st.form_submit_button("✅ Confirm Booking", 
                                              use_container_width=True)
            with col2:
                cancel = st.form_submit_button("❌ Cancel", 
                                              use_container_width=True)

            if submit:
                if not all([booking_name, booking_email, booking_phone, booking_address]):
                    st.error("⚠ All fields required!")
                else:
                    try:
                        res = requests.post(
                            f"{API_URL}/api/save_booking",
                            json={
                                "name": booking_name,
                                "email": booking_email,
                                "phone": booking_phone,
                                "address": booking_address,
                                "message": booking_message
                            },
                            timeout=10
                        )
                        if res.status_code == 200:
                            st.markdown(
                                f'<div class="success-msg">🎉 {booking_name}, aapka booking confirm! ✅</div>',
                                unsafe_allow_html=True
                            )
                            st.balloons()
                            st.session_state.show_booking_form = False
                            st.session_state.messages.append({
                                "role": "bot",
                                "text": f"🎉 {booking_name}, booking successful! Hum aapse jald contact karenge!"
                            })
                            time.sleep(2)
                            st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
            
            if cancel:
                st.session_state.show_booking_form = False
                st.session_state.show_booking_prompt = False
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)

    # ========== CHAT VIEW ==========
    else:
        st.title("🤖 Smart Chatbot")
        st.write("Hotel, Company ya kuch bhi poochein!")
        
        # Chat history
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                st.markdown(f'<div class="user-msg">🧑 {msg["text"]}</div>', 
                           unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="bot-msg">🤖 {msg["text"]}</div>', 
                           unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Booking prompt
        if st.session_state.show_booking_prompt:
            st.markdown(
                '<div class="booking-prompt">🏨 Kya aap booking karna chahenge?</div>',
                unsafe_allow_html=True
            )
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Haan, Book Karein!", use_container_width=True):
                    st.session_state.show_booking_form = True
                    st.session_state.show_booking_prompt = False
                    st.rerun()
            with col2:
                if st.button("❌ Nahi, Abhi Nahi", use_container_width=True):
                    st.session_state.show_booking_prompt = False
                    st.session_state.messages.append({
                        "role": "bot",
                        "text": "Koi baat nahi! Kuch aur poochna ho to batayein! 😊"
                    })
                    st.rerun()
        
        # User input
        with st.form(key="chat_form", clear_on_submit=True):
            user_input = st.text_input("💬 Message:", 
                                      placeholder="Kuch bhi poochein...")
            send = st.form_submit_button("Send 📤", use_container_width=True)
            
            if send and user_input.strip():
                st.session_state.messages.append({"role": "user", "text": user_input})
                
                try:
                    with st.spinner("🤔 Soch raha hoon..."):
                        resp = requests.post(
                            f"{API_URL}/api/chat",
                            json={
                                "message": user_input,
                                "hotel_knowledge": st.session_state.hotel_knowledge,
                                "company_name": st.session_state.selected_company
                            },
                            timeout=30
                        )
                        
                        if resp.status_code == 200:
                            bot_reply = resp.json().get("answer", "Sorry!")
                        else:
                            bot_reply = "❌ Error connecting to bot."
                except Exception as e:
                    bot_reply = f"❌ Error: {str(e)}"
                
                st.session_state.messages.append({"role": "bot", "text": bot_reply})
                
                # Check for booking trigger
                if "booking karna chahenge" in bot_reply.lower() or \
                   "book karna" in bot_reply.lower():
                    st.session_state.show_booking_prompt = True
                
                st.rerun()
        
        # Clear chat
        if st.button("🗑 Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.show_booking_form = False
            st.session_state.show_booking_prompt = False
            st.rerun()