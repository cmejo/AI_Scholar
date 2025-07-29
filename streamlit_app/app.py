"""
Streamlit UI for AI Scholar RAG System
Alternative Python-based interface
"""
import streamlit as st
import requests
import json
import time
from typing import List, Dict, Any
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Configure Streamlit page
st.set_page_config(
    page_title="AI Scholar RAG",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        border-left: 4px solid #667eea;
    }
    
    .user-message {
        background-color: #f0f2f6;
        border-left-color: #667eea;
    }
    
    .assistant-message {
        background-color: #e8f4fd;
        border-left-color: #764ba2;
    }
    
    .source-card {
        background-color: #f8f9fa;
        padding: 0.8rem;
        border-radius: 8px;
        border: 1px solid #dee2e6;
        margin: 0.3rem 0;
    }
    
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Configuration
API_BASE_URL = "http://localhost:8000"
OLLAMA_URL = "http://localhost:11434"

class RAGInterface:
    def __init__(self):
        self.session_state = st.session_state
        if 'messages' not in self.session_state:
            self.session_state.messages = []
        if 'documents' not in self.session_state:
            self.session_state.documents = []
        if 'current_user' not in self.session_state:
            self.session_state.current_user = None

    def authenticate_user(self):
        """Simple authentication interface"""
        if not self.session_state.current_user:
            st.sidebar.header("🔐 Authentication")
            
            with st.sidebar.form("login_form"):
                email = st.text_input("Email", value="admin@example.com")
                password = st.text_input("Password", type="password", value="admin123")
                
                if st.form_submit_button("Login"):
                    try:
                        response = requests.post(
                            f"{API_BASE_URL}/api/auth/login",
                            data={"email": email, "password": password}
                        )
                        if response.status_code == 200:
                            self.session_state.current_user = response.json()
                            st.success("Logged in successfully!")
                            st.rerun()
                        else:
                            st.error("Invalid credentials")
                    except Exception as e:
                        st.error(f"Login failed: {str(e)}")
            
            st.stop()

    def render_header(self):
        """Render main header"""
        st.markdown("""
        <div class="main-header">
            <h1>🧠 AI Scholar RAG System</h1>
            <p>Advanced Retrieval Augmented Generation with Knowledge Graphs</p>
        </div>
        """, unsafe_allow_html=True)

    def render_sidebar(self):
        """Render sidebar with navigation and controls"""
        st.sidebar.header("🎛️ Controls")
        
        # Model selection
        model_options = ["mistral", "llama2", "codellama", "neural-chat"]
        selected_model = st.sidebar.selectbox("Select Model", model_options)
        
        # RAG settings
        st.sidebar.subheader("RAG Settings")
        max_sources = st.sidebar.slider("Max Sources", 1, 10, 5)
        temperature = st.sidebar.slider("Temperature", 0.0, 2.0, 0.7, 0.1)
        enable_cot = st.sidebar.checkbox("Chain of Thought", value=True)
        citation_mode = st.sidebar.checkbox("Citation Mode", value=True)
        
        # Document management
        st.sidebar.subheader("📚 Document Management")
        uploaded_file = st.sidebar.file_uploader(
            "Upload Document",
            type=['pdf', 'txt', 'md'],
            help="Upload PDF, TXT, or Markdown files"
        )
        
        if uploaded_file:
            if st.sidebar.button("Process Document"):
                self.upload_document(uploaded_file)
        
        # Document list
        if st.sidebar.button("Refresh Documents"):
            self.load_documents()
        
        if self.session_state.documents:
            st.sidebar.write(f"📄 {len(self.session_state.documents)} documents loaded")
            
            # Show document list
            for doc in self.session_state.documents[:5]:
                with st.sidebar.expander(f"📄 {doc.get('name', 'Unknown')[:20]}..."):
                    st.write(f"**Status:** {doc.get('status', 'Unknown')}")
                    st.write(f"**Chunks:** {doc.get('chunks', 0)}")
                    st.write(f"**Size:** {doc.get('size', 0)} bytes")
        
        return {
            'model': selected_model,
            'max_sources': max_sources,
            'temperature': temperature,
            'enable_cot': enable_cot,
            'citation_mode': citation_mode
        }

    def upload_document(self, uploaded_file):
        """Upload and process document"""
        try:
            files = {"file": uploaded_file.getvalue()}
            response = requests.post(f"{API_BASE_URL}/api/documents/upload", files=files)
            
            if response.status_code == 200:
                st.sidebar.success(f"Document '{uploaded_file.name}' uploaded successfully!")
                self.load_documents()
            else:
                st.sidebar.error("Upload failed")
        except Exception as e:
            st.sidebar.error(f"Upload error: {str(e)}")

    def load_documents(self):
        """Load documents from backend"""
        try:
            response = requests.get(f"{API_BASE_URL}/api/documents")
            if response.status_code == 200:
                self.session_state.documents = response.json().get('documents', [])
        except Exception as e:
            st.error(f"Failed to load documents: {str(e)}")

    def render_chat_interface(self, settings):
        """Render main chat interface"""
        st.header("💬 Chat with Your Documents")
        
        # Display chat history
        for message in self.session_state.messages:
            self.render_message(message)
        
        # Chat input
        user_input = st.chat_input("Ask me anything about your documents...")
        
        if user_input:
            # Add user message
            user_message = {
                "role": "user",
                "content": user_input,
                "timestamp": datetime.now()
            }
            self.session_state.messages.append(user_message)
            
            # Generate response
            with st.spinner("Thinking..."):
                response = self.generate_response(user_input, settings)
                self.session_state.messages.append(response)
            
            st.rerun()

    def render_message(self, message):
        """Render individual chat message"""
        if message["role"] == "user":
            with st.chat_message("user"):
                st.write(message["content"])
        else:
            with st.chat_message("assistant"):
                st.write(message["content"])
                
                # Show sources if available
                if "sources" in message and message["sources"]:
                    with st.expander(f"📚 Sources ({len(message['sources'])})"):
                        for i, source in enumerate(message["sources"], 1):
                            st.markdown(f"""
                            <div class="source-card">
                                <strong>Source {i}:</strong> {source.get('document', 'Unknown')}<br>
                                <strong>Page:</strong> {source.get('page', 'N/A')}<br>
                                <strong>Relevance:</strong> {source.get('relevance', 0):.2%}<br>
                                <em>{source.get('snippet', '')[:200]}...</em>
                            </div>
                            """, unsafe_allow_html=True)
                
                # Show chain of thought if available
                if "chain_of_thought" in message and message["chain_of_thought"]:
                    with st.expander("🧠 Chain of Thought"):
                        cot = message["chain_of_thought"]
                        st.write(f"**Steps:** {cot.get('totalSteps', 0)}")
                        st.write(f"**Confidence:** {cot.get('overallConfidence', 0):.2%}")
                        st.write(f"**Processing Time:** {cot.get('executionTime', 0)}ms")

    def generate_response(self, query, settings):
        """Generate response using backend API"""
        try:
            payload = {
                "message": query,
                "conversation_id": "streamlit_session",
                "use_chain_of_thought": settings['enable_cot'],
                "citation_mode": settings['citation_mode']
            }
            
            response = requests.post(
                f"{API_BASE_URL}/api/chat/message",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "role": "assistant",
                    "content": data.get("response", "No response generated"),
                    "sources": data.get("sources", []),
                    "chain_of_thought": data.get("chain_of_thought"),
                    "model": data.get("model", settings['model']),
                    "processing_time": data.get("processing_time", 0),
                    "timestamp": datetime.now()
                }
            else:
                return {
                    "role": "assistant",
                    "content": f"Error: {response.status_code} - {response.text}",
                    "timestamp": datetime.now()
                }
                
        except Exception as e:
            return {
                "role": "assistant",
                "content": f"Error generating response: {str(e)}",
                "timestamp": datetime.now()
            }

    def render_analytics_tab(self):
        """Render analytics dashboard"""
        st.header("📊 Analytics Dashboard")
        
        # Mock analytics data
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Queries", "1,234", "↗️ 12%")
        
        with col2:
            st.metric("Documents", len(self.session_state.documents), "↗️ 3")
        
        with col3:
            st.metric("Avg Response Time", "1.2s", "↘️ 0.3s")
        
        with col4:
            st.metric("Success Rate", "94.5%", "↗️ 2.1%")
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Query volume chart
            dates = pd.date_range(start='2024-01-01', end='2024-01-07', freq='D')
            volumes = [45, 52, 48, 61, 58, 67, 72]
            
            fig = px.line(
                x=dates, y=volumes,
                title="Daily Query Volume",
                labels={'x': 'Date', 'y': 'Queries'}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Response time distribution
            response_times = [0.8, 1.2, 0.9, 1.5, 1.1, 0.7, 1.3, 1.0, 0.9, 1.4]
            
            fig = px.histogram(
                x=response_times,
                title="Response Time Distribution",
                labels={'x': 'Response Time (s)', 'y': 'Frequency'}
            )
            st.plotly_chart(fig, use_container_width=True)

    def render_documents_tab(self):
        """Render document management tab"""
        st.header("📚 Document Management")
        
        if not self.session_state.documents:
            st.info("No documents uploaded yet. Use the sidebar to upload documents.")
            return
        
        # Document statistics
        total_docs = len(self.session_state.documents)
        total_chunks = sum(doc.get('chunks', 0) for doc in self.session_state.documents)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Documents", total_docs)
        with col2:
            st.metric("Total Chunks", total_chunks)
        with col3:
            st.metric("Avg Chunks/Doc", f"{total_chunks/total_docs:.1f}" if total_docs > 0 else "0")
        
        # Document table
        df = pd.DataFrame(self.session_state.documents)
        if not df.empty:
            st.dataframe(
                df[['name', 'status', 'chunks', 'size']],
                use_container_width=True
            )
        
        # Document actions
        st.subheader("Document Actions")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Refresh Documents"):
                self.load_documents()
                st.rerun()
        
        with col2:
            if st.button("🗑️ Clear All Documents"):
                if st.confirm("Are you sure you want to delete all documents?"):
                    # Implementation would call delete API
                    st.success("All documents deleted")

    def run(self):
        """Main application runner"""
        self.authenticate_user()
        self.render_header()
        
        # Load documents on startup
        if not self.session_state.documents:
            self.load_documents()
        
        # Sidebar
        settings = self.render_sidebar()
        
        # Main tabs
        tab1, tab2, tab3 = st.tabs(["💬 Chat", "📊 Analytics", "📚 Documents"])
        
        with tab1:
            self.render_chat_interface(settings)
        
        with tab2:
            self.render_analytics_tab()
        
        with tab3:
            self.render_documents_tab()

# Run the application
if __name__ == "__main__":
    app = RAGInterface()
    app.run()