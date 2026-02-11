"""
TMS AI - Streamlit User Interface
"""
import streamlit as st
import requests
import json
import os
from typing import Optional

# Configure Streamlit page
st.set_page_config(
    page_title="TMS AI Document Assistant",
    page_icon="📦",
    layout="wide"
)

# API configuration - use environment variable or default to localhost
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8001")

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 2rem;
    }
    .confidence-high {
        color: #16A34A;
        font-weight: bold;
    }
    .confidence-medium {
        color: #CA8A04;
        font-weight: bold;
    }
    .confidence-low {
        color: #DC2626;
        font-weight: bold;
    }
    .source-box {
        background-color: #F3F4F6;
        color: #1F2937;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown('<h1 class="main-header">📦 TMS AI Document Assistant</h1>', unsafe_allow_html=True)
st.markdown("---")

# Session state initialization
if 'document_id' not in st.session_state:
    st.session_state.document_id = None
if 'filename' not in st.session_state:
    st.session_state.filename = None

# Sidebar
with st.sidebar:
    st.header("📋 About")
    st.write("""
    This AI assistant helps you:
    - 📄 **Upload** logistics documents
    - 💬 **Ask** questions about them
    - 📊 **Extract** structured data
    
    Supported formats: PDF, DOCX, TXT
    """)
    
    if st.session_state.document_id:
        st.success(f"✅ Active Document: {st.session_state.filename}")
        st.info(f"📝 ID: `{st.session_state.document_id[:8]}...`")
        if st.button("🗑️ Clear Document"):
            st.session_state.document_id = None
            st.session_state.filename = None
            st.rerun()
    
    st.markdown("---")
    st.caption("TMS AI v1.0 | Powered by Groq & Mistral")

# Create tabs
tab1, tab2, tab3 = st.tabs(["📤 Upload Document", "💬 Ask Questions", "📊 Extract Data"])

# Tab 1: Upload Document
with tab1:
    st.header("Upload Logistics Document")
    st.write("Upload a document to get started (PDF, DOCX, or TXT)")
    
    uploaded_file = st.file_uploader(
        "Choose a file",
        type=["pdf", "docx", "txt"],
        help="Maximum file size: 10MB"
    )
    
    if uploaded_file is not None:
        if st.button("🚀 Process Document", type="primary"):
            with st.spinner("Processing document..."):
                try:
                    # Upload to API
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
                    response = requests.post(f"{API_BASE_URL}/upload", files=files)
                    
                    if response.status_code == 200:
                        result = response.json()
                        st.session_state.document_id = result["document_id"]
                        st.session_state.filename = result["filename"]
                        
                        st.success(f"✅ Document processed successfully!")
                        st.info(f"📄 Filename: {result['filename']}")
                        st.info(f"🔢 Chunks created: {result['num_chunks']}")
                        st.info(f"📝 Document ID: `{result['document_id']}`")
                        
                        st.balloons()
                    else:
                        st.error(f"❌ Error: {response.json().get('detail', 'Unknown error')}")
                        
                except Exception as e:
                    st.error(f"❌ Error connecting to API: {str(e)}")
                    st.info("Make sure the FastAPI server is running on http://localhost:8001")

# Tab 2: Ask Questions
with tab2:
    st.header("Ask Questions About Your Document")
    
    if not st.session_state.document_id:
        st.warning("⚠️ Please upload a document first in the 'Upload Document' tab")
    else:
        st.success(f"📄 Active document: {st.session_state.filename}")
        
        # Example questions
        with st.expander("💡 Example Questions"):
            st.write("""
            - What is the carrier rate?
            - When is the pickup scheduled?
            - Who is the consignee?
            - What is the shipment weight?
            - What is the equipment type?
            - What is the delivery address?
            """)
        
        # Question input
        question = st.text_input(
            "Enter your question:",
            placeholder="e.g., What is the carrier rate?"
        )
        
        if st.button("🔍 Get Answer", type="primary", disabled=not question):
            with st.spinner("Analyzing document..."):
                try:
                    # Ask question via API
                    payload = {
                        "document_id": st.session_state.document_id,
                        "question": question
                    }
                    response = requests.post(f"{API_BASE_URL}/ask", json=payload)
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        # Display answer
                        st.markdown("### 💡 Answer")
                        st.write(result["answer"])
                        
                        # Display confidence
                        confidence = result["confidence_score"]
                        category = result["confidence_category"]
                        
                        confidence_class = f"confidence-{category}"
                        st.markdown(f"""
                        **Confidence Score:** 
                        <span class="{confidence_class}">{confidence:.1%} ({category.upper()})</span>
                        """, unsafe_allow_html=True)
                        
                        # Progress bar for confidence
                        st.progress(confidence)
                        
                        # Display sources
                        st.markdown("### 📚 Sources")
                        for i, source in enumerate(result["sources"], 1):
                            with st.expander(f"Source {i} (Similarity: {source['similarity_score']:.1%})"):
                                st.markdown(f'<div class="source-box">{source["content"]}</div>', 
                                          unsafe_allow_html=True)
                                st.caption(f"Chunk {source['metadata'].get('chunk_index', 'N/A')} of {source['metadata'].get('total_chunks', 'N/A')}")
                    else:
                        st.error(f"❌ Error: {response.json().get('detail', 'Unknown error')}")
                        
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

# Tab 3: Extract Structured Data
with tab3:
    st.header("Extract Structured Shipment Data")
    
    if not st.session_state.document_id:
        st.warning("⚠️ Please upload a document first in the 'Upload Document' tab")
    else:
        st.success(f"📄 Active document: {st.session_state.filename}")
        
        st.write("Extract key shipment information from your document into a structured JSON format.")
        
        if st.button("📊 Extract Data", type="primary"):
            with st.spinner("Extracting structured data..."):
                try:
                    # Extract data via API
                    response = requests.post(
                        f"{API_BASE_URL}/extract",
                        params={"document_id": st.session_state.document_id}
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        shipment_data = result["shipment_data"]
                        
                        st.success("✅ Data extracted successfully!")
                        
                        # Display in two columns
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("#### 📋 Shipment Details")
                            st.write(f"**Shipment ID:** {shipment_data.get('shipment_id') or 'N/A'}")
                            st.write(f"**Shipper:** {shipment_data.get('shipper') or 'N/A'}")
                            st.write(f"**Consignee:** {shipment_data.get('consignee') or 'N/A'}")
                            st.write(f"**Carrier:** {shipment_data.get('carrier_name') or 'N/A'}")
                            st.write(f"**Mode:** {shipment_data.get('mode') or 'N/A'}")
                            st.write(f"**Equipment:** {shipment_data.get('equipment_type') or 'N/A'}")
                        
                        with col2:
                            st.markdown("#### 📅 Schedule & Costs")
                            st.write(f"**Pickup:** {shipment_data.get('pickup_datetime') or 'N/A'}")
                            st.write(f"**Delivery:** {shipment_data.get('delivery_datetime') or 'N/A'}")
                            st.write(f"**Rate:** {shipment_data.get('rate') or 'N/A'}")
                            st.write(f"**Currency:** {shipment_data.get('currency') or 'N/A'}")
                            st.write(f"**Weight:** {shipment_data.get('weight') or 'N/A'}")
                        
                        # Display JSON
                        st.markdown("#### 📄 JSON Output")
                        st.json(shipment_data)
                        
                        # Download button
                        json_str = json.dumps(shipment_data, indent=2)
                        st.download_button(
                            label="⬇️ Download JSON",
                            data=json_str,
                            file_name=f"shipment_data_{st.session_state.document_id[:8]}.json",
                            mime="application/json"
                        )
                        
                    else:
                        st.error(f"❌ Error: {response.json().get('detail', 'Unknown error')}")
                        
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
