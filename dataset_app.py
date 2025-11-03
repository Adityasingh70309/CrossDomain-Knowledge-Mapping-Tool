import streamlit as st
import requests
import pandas as pd
import json
import os
from datetime import datetime
import xml.etree.ElementTree as ET
import io
from PIL import Image
import base64

# Configure the page
st.set_page_config(
    page_title="Dataset Selection App",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

class StreamlitDatasetApp:
    def __init__(self):
        self.setup_ui()
    
    def setup_ui(self):
        # Custom CSS for styling
        st.markdown("""
        <style>
        .main-header {
            font-size: 3rem;
            color: #4a6ee0;
            text-align: center;
            margin-bottom: 2rem;
            font-weight: bold;
        }
        .dataset-card {
            background-color: #f8f9fc;
            padding: 1.5rem;
            border-radius: 10px;
            border-left: 4px solid #4a6ee0;
            margin-bottom: 1rem;
            cursor: pointer;
        }
        .dataset-card:hover {
            background-color: #e8edff;
            transform: translateY(-2px);
            transition: all 0.3s ease;
        }
        .upload-area {
            border: 2px dashed #4a6ee0;
            border-radius: 10px;
            padding: 2rem;
            text-align: center;
            background-color: #f8f9fc;
            margin: 1rem 0;
        }
        .success-box {
            background-color: #d4edda;
            border: 1px solid #c3e6cb;
            border-radius: 5px;
            padding: 1rem;
            margin: 1rem 0;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Header
        st.markdown('<div class="main-header">📊 Dataset Selection</div>', unsafe_allow_html=True)
        
        # Create two columns for layout
        col1, col2 = st.columns([1, 1])
        
        with col1:
            self.show_dataset_selection()
        
        with col2:
            self.show_processing_area()
    
    def show_dataset_selection(self):
        st.subheader("🎯 Select Data Source")
        
        # Dataset options with custom cards
        datasets = {
            "wikipedia": {"name": "Wikipedia Articles", "icon": "🌐"},
            "arxiv": {"name": "Scientific Papers (Arxiv)", "icon": "📚"},
            "news": {"name": "News Articles", "icon": "📰"},
            "custom": {"name": "Custom Upload", "icon": "📁"}
        }
        
        for dataset_id, dataset_info in datasets.items():
            with st.container():
                st.markdown(f"""
                <div class="dataset-card" onclick="this.style.backgroundColor='#e8edff'">
                    <h4>{dataset_info['icon']} {dataset_info['name']}</h4>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"Select {dataset_info['name']}", key=f"btn_{dataset_id}"):
                    st.session_state.selected_dataset = dataset_id
                    st.rerun()
        
        # Show current selection
        if 'selected_dataset' in st.session_state:
            selected_name = datasets[st.session_state.selected_dataset]['name']
            st.success(f"✅ Selected: {selected_name}")
    
    def show_processing_area(self):
        st.subheader("⚙️ Processing Options")
        
        if 'selected_dataset' not in st.session_state:
            st.info("👈 Please select a dataset source first")
            return
        
        # Show custom upload area if custom dataset is selected
        if st.session_state.selected_dataset == 'custom':
            self.show_custom_upload()
        
        # Process button
        if st.button("🚀 Process Selected Dataset", use_container_width=True):
            self.process_datasets()
        
        # Show processing results
        if 'processing_result' in st.session_state:
            self.show_results()
    
    def show_custom_upload(self):
        st.markdown('<div class="upload-area">', unsafe_allow_html=True)
        st.write("📁 Upload your dataset file")
        
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=['csv', 'json', 'txt', 'xml'],
            key="file_uploader"
        )
        
        if uploaded_file is not None:
            # Save file info to session state
            st.session_state.uploaded_file = uploaded_file
            file_size = len(uploaded_file.getvalue())
            
            st.success(f"""
            ✅ File uploaded successfully!
            - Name: {uploaded_file.name}
            - Size: {self.format_file_size(file_size)}
            - Type: {uploaded_file.type if hasattr(uploaded_file, 'type') else 'Unknown'}
            """)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def show_results(self):
        result = st.session_state.processing_result
        st.markdown('<div class="success-box">', unsafe_allow_html=True)
        st.write("🎉 Processing Complete!")
        st.write(f"**Dataset:** {result['dataset']}")
        st.write(f"**Output File:** {result['output_file']}")
        st.write(f"**Records Processed:** {result.get('records', 'N/A')}")
        
        # Show preview for certain file types
        if result.get('preview_data') is not None:
            st.subheader("📊 Data Preview")
            st.dataframe(result['preview_data'])
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def format_file_size(self, size_bytes):
        """Convert file size to human readable format"""
        if size_bytes == 0:
            return "0 Bytes"
        size_names = ["Bytes", "KB", "MB", "GB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names)-1:
            size_bytes /= 1024.0
            i += 1
        return f"{size_bytes:.2f} {size_names[i]}"
    
    def process_datasets(self):
        if 'selected_dataset' not in st.session_state:
            st.error("Please select a dataset first!")
            return
        
        dataset = st.session_state.selected_dataset
        
        # Validate custom upload
        if dataset == 'custom' and 'uploaded_file' not in st.session_state:
            st.error("Please upload a file for custom dataset!")
            return
        
        try:
            with st.spinner(f"🔄 Processing {dataset} dataset..."):
                if dataset == 'wikipedia':
                    result = self.process_wikipedia()
                elif dataset == 'arxiv':
                    result = self.process_arxiv()
                elif dataset == 'news':
                    result = self.process_news()
                elif dataset == 'custom':
                    result = self.process_custom_upload()
                
                st.session_state.processing_result = result
                st.rerun()
                
        except Exception as e:
            st.error(f"❌ Error processing dataset: {str(e)}")
    
    def process_wikipedia(self):
        """Process Wikipedia dataset"""
        st.info("🌐 Fetching random Wikipedia article...")
        
        try:
            response = requests.get(
                "https://en.wikipedia.org/api/rest_v1/page/random/summary",
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                
                # Save to file
                output_file = 'wikipedia_data.json'
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
                
                # Create preview
                preview_data = pd.DataFrame([{
                    'Title': data.get('title', 'Unknown'),
                    'Description': data.get('description', 'No description'),
                    'Extract Length': len(data.get('extract', ''))
                }])
                
                return {
                    'dataset': 'Wikipedia Articles',
                    'output_file': output_file,
                    'records': 1,
                    'preview_data': preview_data
                }
                
        except Exception as e:
            st.warning(f"Using sample data due to API error: {e}")
            # Create sample data
            sample_data = {
                "title": "Sample Wikipedia Article",
                "content": "This is sample Wikipedia content for demonstration.",
                "timestamp": datetime.now().isoformat()
            }
            
            output_file = 'wikipedia_data.json'
            with open(output_file, 'w') as f:
                json.dump(sample_data, f, indent=2)
            
            preview_data = pd.DataFrame([{
                'Title': sample_data['title'],
                'Description': 'Sample data',
                'Content Length': len(sample_data['content'])
            }])
            
            return {
                'dataset': 'Wikipedia Articles (Sample)',
                'output_file': output_file,
                'records': 1,
                'preview_data': preview_data
            }
    
    def process_arxiv(self):
        """Process ArXiv dataset"""
        st.info("📚 Fetching AI research papers from ArXiv...")
        
        try:
            response = requests.get(
                "http://export.arxiv.org/api/query?search_query=all:ai&start=0&max_results=5",
                timeout=15
            )
            if response.status_code == 200:
                root = ET.fromstring(response.content)
                
                papers = []
                for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
                    title_elem = entry.find('{http://www.w3.org/2005/Atom}title')
                    summary_elem = entry.find('{http://www.w3.org/2005/Atom}summary')
                    
                    paper = {
                        'title': title_elem.text if title_elem is not None else 'No title',
                        'authors': [author.find('{http://www.w3.org/2005/Atom}name').text 
                                  for author in entry.findall('{http://www.w3.org/2005/Atom}author')],
                        'summary': summary_elem.text if summary_elem is not None else 'No summary',
                        'published': entry.find('{http://www.w3.org/2005/Atom}published').text
                    }
                    papers.append(paper)
                
                # Save to file
                output_file = 'arxiv_papers.json'
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(papers, f, indent=2, ensure_ascii=False)
                
                # Create preview
                preview_data = pd.DataFrame([{
                    'Title': paper['title'][:50] + '...' if len(paper['title']) > 50 else paper['title'],
                    'Authors': ', '.join(paper['authors'][:2]) + ('...' if len(paper['authors']) > 2 else ''),
                    'Published': paper['published'][:10]
                } for paper in papers])
                
                return {
                    'dataset': 'ArXiv Papers',
                    'output_file': output_file,
                    'records': len(papers),
                    'preview_data': preview_data
                }
                
        except Exception as e:
            st.warning(f"Using sample data due to API error: {e}")
            # Create sample data
            sample_papers = [
                {
                    "title": "Sample AI Research Paper",
                    "authors": ["John Doe", "Jane Smith"],
                    "summary": "This is a sample research paper about artificial intelligence.",
                    "published": datetime.now().isoformat()
                }
            ]
            
            output_file = 'arxiv_papers.json'
            with open(output_file, 'w') as f:
                json.dump(sample_papers, f, indent=2)
            
            preview_data = pd.DataFrame([{
                'Title': paper['title'],
                'Authors': ', '.join(paper['authors']),
                'Published': paper['published'][:10]
            } for paper in sample_papers])
            
            return {
                'dataset': 'ArXiv Papers (Sample)',
                'output_file': output_file,
                'records': len(sample_papers),
                'preview_data': preview_data
            }
    
    def process_news(self):
        """Process News Articles dataset"""
        st.info("📰 Generating sample news articles...")
        
        news_data = [
            {
                "title": "Sample News Article 1",
                "content": "This is sample news content for demonstration purposes.",
                "source": "Sample News Source",
                "published_at": datetime.now().isoformat(),
                "category": "Technology"
            },
            {
                "title": "Sample News Article 2",
                "content": "Another sample news article for the dataset.",
                "source": "Sample News Source",
                "published_at": datetime.now().isoformat(),
                "category": "Science"
            }
        ]
        
        # Save to file
        output_file = 'news_articles.json'
        with open(output_file, 'w') as f:
            json.dump(news_data, f, indent=2)
        
        # Create preview
        preview_data = pd.DataFrame([{
            'Title': article['title'],
            'Category': article['category'],
            'Source': article['source'],
            'Published': article['published_at'][:10]
        } for article in news_data])
        
        return {
            'dataset': 'News Articles',
            'output_file': output_file,
            'records': len(news_data),
            'preview_data': preview_data
        }
    
    def process_custom_upload(self):
        """Process custom uploaded file"""
        uploaded_file = st.session_state.uploaded_file
        
        st.info(f"📁 Processing {uploaded_file.name}...")
        
        file_ext = os.path.splitext(uploaded_file.name)[1].lower()
        
        if file_ext == '.csv':
            # Process CSV file
            df = pd.read_csv(uploaded_file)
            output_file = 'processed_custom_data.csv'
            df.to_csv(output_file, index=False)
            
            return {
                'dataset': 'Custom CSV Upload',
                'output_file': output_file,
                'records': len(df),
                'preview_data': df.head()
            }
            
        elif file_ext == '.json':
            # Process JSON file
            data = json.load(uploaded_file)
            output_file = 'processed_custom_data.json'
            with open(output_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            # Convert to DataFrame for preview if possible
            if isinstance(data, list):
                preview_data = pd.DataFrame(data)
            else:
                preview_data = pd.DataFrame([data])
            
            return {
                'dataset': 'Custom JSON Upload',
                'output_file': output_file,
                'records': len(data) if isinstance(data, list) else 1,
                'preview_data': preview_data.head()
            }
            
        elif file_ext == '.txt':
            # Process text file
            content = uploaded_file.getvalue().decode('utf-8')
            output_file = 'processed_custom_data.txt'
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"Processed on: {datetime.now()}\n\n")
                f.write(content)
            
            return {
                'dataset': 'Custom Text Upload',
                'output_file': output_file,
                'records': len(content.splitlines()),
                'preview_data': None
            }
            
        else:
            # For other file types
            output_file = f'processed_custom_data{file_ext}'
            with open(output_file, 'wb') as f:
                f.write(uploaded_file.getbuffer())
            
            return {
                'dataset': f'Custom {file_ext.upper()} Upload',
                'output_file': output_file,
                'records': 'N/A',
                'preview_data': None
            }

# Sidebar with information
def setup_sidebar():
    st.sidebar.title("ℹ️ About")
    st.sidebar.markdown("""
    **Dataset Selection Application**
    
    A web-based tool for processing datasets from multiple sources:
    
    - 🌐 **Wikipedia Articles** - Live API data
    - 📚 **ArXiv Papers** - Research publications  
    - 📰 **News Articles** - Sample data generator
    - 📁 **Custom Upload** - Your own files (CSV/JSON/TXT)
    
    **Features:**
    ✅ Real-time data processing
    ✅ Multiple file format support
    ✅ Data preview
    ✅ Error handling
    """)
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("📊 Quick Stats")
    
    # Show file information if available
    if 'processing_result' in st.session_state:
        result = st.session_state.processing_result
        st.sidebar.metric("Last Processed", result['dataset'])
        st.sidebar.metric("Records", result.get('records', 'N/A'))
        st.sidebar.metric("Output File", result['output_file'])

# Main application
def main():
    setup_sidebar()
    app = StreamlitDatasetApp()

if __name__ == "__main__":
    main()