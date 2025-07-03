import streamlit as st
import requests
import uuid
import speech_recognition as sr
import streamlit.components.v1 as components
from langchain_ollama import OllamaLLM
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage


if "user_id" not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())[:8]

USER_ID = st.session_state.user_id
API_BASE = "http://127.0.0.1:5001"

#API_BASE = st.secrets.get("API_BASE", "http://127.0.0.1:5001")


# --- API Helpers ---
def get_latest_voice_input_from_api():
    try:
        response = requests.get(f"{API_BASE}/latest", params={"user_id": USER_ID})
        if response.status_code == 200:
            text = response.json().get("text", "").strip()
            if text:
                clear_text_from_api()
            return text
    except Exception as e:
        st.error(f"API connection error: {e}")
    return ""

def send_text_to_api(text):
    try:
        response = requests.post(f"{API_BASE}/receive", json={"text": text, "user_id": USER_ID}).ok
        return response.status_code == 200
    except Exception as e:
        st.error(f"Failed to send to API: {e}")
        return False

def clear_text_from_api():
    try:
        requests.post(f"{API_BASE}/clear", json={"user_id": USER_ID})
    except Exception as e:
        st.warning(f"Failed to clear text on API: {e}")

# --- Streamlit Page Setup ---
st.set_page_config(page_title="ChatBot Assistant", layout="centered")
st.image("mpslabs.png")
st.title("ChatBot Assistant")

# --- LangChain Model Setup ---
model = OllamaLLM(model="gemma2:9b")
system_prompts = (
    "You are an intelligent, friendly, and helpful AI assistant. "
    "Always respond in a conversational tone, and do your best to clearly answer questions, help solve problems, or offer suggestions. "
    "If you don’t know something, say so honestly. Do not make up facts. "
    "When responding, keep replies concise and helpful. Ask follow-up questions if necessary to better understand the user. "
    "Always respond in a professional tone using plain text. "
    "Do NOT use emojis, emoticons, or symbols like 😊, 😂, 🙏, etc. in any response. "
    "Even if the user uses emojis, do not include them in your reply. "
    "Only use standard English text to express tone or emotion."
)

# --- Session State Init ---
if "messages" not in st.session_state: 
    st.session_state.messages = []
if "last_input" not in st.session_state: 
    st.session_state.last_input = ""
if "processing" not in st.session_state: 
    st.session_state.processing = False

# --- Display Chat Messages ---
for msg in st.session_state.messages:
    is_user = msg["role"] == "user"
    speaker = "You" if is_user else "Assistant"
    align = "flex-end" if is_user else "flex-start"
    bg = "#E4E6E3" if is_user else "#D8D2D2"
    st.markdown(f"""
    <div style="display: flex; justify-content: {align}; margin: 10px 0;">
        <div style="background-color: {bg}; padding: 10px 16px; border-radius: 12px; max-width: 70%; font-size: 1.1rem; line-height: 1.4; white-space: pre-wrap;">
            <strong>{speaker}:</strong><br>{msg["content"]}
        
    """, unsafe_allow_html=True)

if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
            if st.button("🔊 Speak Last Response"):
                last_response = st.session_state.messages[-1]["content"]
                escaped = last_response.replace('"', '\\"').replace("\n", " ")
                components.html(f"""
                <script>
                const msg = new SpeechSynthesisUtterance("{escaped}");
                msg.lang = "en-US";
                msg.rate = 1.0;
                window.speechSynthesis.speak(msg);
                </script>
                """, height=0)



# --- Check for Voice Input from API ---
voice_input = get_latest_voice_input_from_api()

# --- Initialize input clearing mechanism ---
if "clear_input" not in st.session_state:
    st.session_state.clear_input = False

# --- Text Input Field ---
input_value = "" if st.session_state.clear_input else st.session_state.get("manual_text_input", "")
manual_input = st.chat_input("Type your message and press Enter")
# --- Browser Mic: HTML + JS Component ---
# --- Input field + mic button in one row ---
components.html(f"""
<style>
    .mic-overlay-container {{
      position: absolute;
      bottom: 0px;
      right: 0px;
      z-index: 1000;
    }}
    .mic-btn {{
      background-color: white;
      border: 2px solid #CCC4C4;    
      padding: 10px 14px;
      font-size: 20px;
      border-radius: 8px;
      cursor: pointer;
      transition: all 0.3s ease;
    }}
    .mic-btn.listening {{
      background-color: #B8EAA4;
      animation: pulse 1s infinite;
    }}
    @keyframes pulse {{
      0% {{ transform: scale(1); }}
      50% {{ transform: scale(1.1); }}
      100% {{ transform: scale(1); }}
    }}
</style>

<div class="mic-overlay-container">
  <button class="mic-btn" id="mic-button" onclick="startRecognition()">🎙️</button>
</div>

<script>
  const micBtn = document.getElementById("mic-button");

  function startRecognition() {{
    const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
    recognition.lang = 'en-US';
    recognition.continuous = false;
    recognition.interimResults = false;

    micBtn.classList.add("listening");
    micBtn.innerText = "🎤";

    recognition.onresult = function(event) {{
      const transcript = event.results[0][0].transcript;

      fetch("http://127.0.0.1:5001/receive", {{
        method: "POST",
        headers: {{ "Content-Type": "application/json" }},
        body: JSON.stringify({{ text: transcript, user_id: "{USER_ID}" }})
      }});

      micBtn.classList.remove("listening");
      micBtn.innerText = "🎙️";
    }};

    recognition.onerror = function(event) {{
      alert("Mic error: " + event.error);
      micBtn.classList.remove("listening");
      micBtn.innerText = "🎙️";
    }};

    recognition.onend = function() {{
      micBtn.classList.remove("listening");
      micBtn.innerText = "🎙️";
    }};

    recognition.start();
  }}
</script>
""", height=100)




# --- Determine Final Input (Voice takes priority) ---
final_input = None
if voice_input:
    final_input = voice_input
    st.success(f"🎤 Voice input received: {voice_input}")
elif manual_input:
     final_input = manual_input

if "input_history" not in st.session_state:
    st.session_state.input_history=[]

if final_input and (len(st.session_state.input_history) == 0 or final_input != st.session_state.input_history[-1]):
    st.session_state.input_history.append(final_input)

MAX_HISTORY = 10
if len(st.session_state.input_history)>MAX_HISTORY:
    st.session_state.input_history=st.session_state.input_history[-MAX_HISTORY:]

with st.sidebar:
    #st.write(f"👤 User ID: `{USER_ID}`")
    #st.write("CHAT HISTORY")
    for idx, item in enumerate(reversed(st.session_state.input_history), 1):
        st.write(f"{idx}. {item}")



# --- Process Input Automatically ---                                                                                                                             
if final_input and final_input != st.session_state.last_input and not st.session_state.processing:
    st.session_state.processing = True
    st.session_state.last_input = final_input
    
    # Add user message
    st.session_state.messages.append({"role": "user", "content": final_input})

    # Prepare chat history for LangChain
    chat_history = [SystemMessage(content=system_prompts)] + [
        HumanMessage(content=m["content"]) if m["role"] == "user" else AIMessage(content=m["content"])
        for m in st.session_state.messages
    ]


    # Get AI response
    with st.spinner("🤖Assistant is thinking..."):
        try:
            response = model.invoke(chat_history)
            st.session_state.messages.append({"role": "assistant", "content": response})
        except Exception as e:
            st.error(f"Error getting AI response: {e}")
            st.session_state.messages.append({"role": "assistant", "content": "I'm sorry, I encountered an error processing your request."})
    

        
    # Reset processing state and trigger input clearing
    st.session_state.processing = False
    st.session_state.clear_input = True
    #st.session_state.manual_input = ""
    
    
    # Rerun to update the display
    st.rerun()

# --- Reset clear_input flag after rerun ---
if st.session_state.clear_input:
    st.session_state.clear_input = False

# --- Auto-refresh for voice input (check every 2 seconds) ---
if not st.session_state.processing:
    import time
    time.sleep(2)  # Small delay to prevent too frequent polling
    st.rerun()



# --- Clear Chat History ---
# if st.button("🗑️ Clear Chat History"):
#     st.session_state.messages = []
#     st.session_state.last_input = ""
#     st.session_state.processing = False
#     st.rerun()