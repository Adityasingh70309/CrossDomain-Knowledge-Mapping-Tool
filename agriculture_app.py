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
import jwt
import time

# Configure the page
st.set_page_config(
    page_title="Agriculture & Climate Dataset App",
    page_icon="🌱",
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
            color: #2e7d32;
            text-align: center;
            margin-bottom: 2rem;
            font-weight: bold;
            background: linear-gradient(45deg, #2e7d32, #4caf50);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .theme-header {
            font-size: 1.5rem;
            color: #1b5e20;
            text-align: center;
            margin-bottom: 2rem;
            font-weight: bold;
        }
        .dataset-card {
            background-color: #f1f8e9;
            padding: 1.5rem;
            border-radius: 10px;
            border-left: 4px solid #4caf50;
            margin-bottom: 1rem;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        .dataset-card:hover {
            background-color: #e8f5e9;
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        .upload-area {
            border: 2px dashed #4caf50;
            border-radius: 10px;
            padding: 2rem;
            text-align: center;
            background-color: #f1f8e9;
            margin: 1rem 0;
        }
        .success-box {
            background-color: #d4edda;
            border: 1px solid #c3e6cb;
            border-radius: 5px;
            padding: 1rem;
            margin: 1rem 0;
        }
        .topic-input {
            background-color: #f8f9fa;
            border-radius: 5px;
            padding: 1rem;
            margin: 1rem 0;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Header with theme
        st.markdown('<div class="main-header">🌱 Agriculture & Climate Dataset Selection</div>', unsafe_allow_html=True)
        st.markdown('<div class="theme-header">🌍 Explore datasets related to agriculture, climate change, and environmental sustainability</div>', unsafe_allow_html=True)
        
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
            "wikipedia": {"name": "Wikipedia Articles", "icon": "🌐", "description": "Get agriculture and climate related articles"},
            "arxiv": {"name": "Scientific Papers (Arxiv)", "icon": "📚", "description": "Research papers on agriculture and climate"},
            "news": {"name": "News Articles", "icon": "📰", "description": "Latest news on agriculture and environment"},
            "custom": {"name": "Custom Upload", "icon": "📁", "description": "Upload your own agriculture datasets"}
        }
        
        for dataset_id, dataset_info in datasets.items():
            with st.container():
                st.markdown(f"""
                <div class="dataset-card">
                    <h4>{dataset_info['icon']} {dataset_info['name']}</h4>
                    <p style='color: #666; font-size: 0.9rem;'>{dataset_info['description']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"Select {dataset_info['name']}", key=f"btn_{dataset_id}"):
                    st.session_state.selected_dataset = dataset_id
                    # Clear previous results when selecting new dataset
                    if 'processing_result' in st.session_state:
                        del st.session_state.processing_result
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
        
        # Show topic input for API-based datasets
        if st.session_state.selected_dataset in ['wikipedia', 'arxiv', 'news']:
            self.show_topic_input()
        
        # Show custom upload area if custom dataset is selected
        if st.session_state.selected_dataset == 'custom':
            self.show_custom_upload()
        
        # Process button
        if st.button("🚀 Process Selected Dataset", use_container_width=True, type="primary"):
            self.process_datasets()
        
        # Show processing results
        if 'processing_result' in st.session_state:
            self.show_results()
    
    def show_topic_input(self):
        st.markdown('<div class="topic-input">', unsafe_allow_html=True)
        
        # Default topics based on agriculture and climate
        default_topics = {
            "wikipedia": "Sustainable agriculture",
            "arxiv": "climate change agriculture",
            "news": "agriculture climate change"
        }
        
        dataset = st.session_state.selected_dataset
        default_topic = default_topics.get(dataset, "agriculture climate")
        
        st.write(f"🔍 **Enter your agriculture/climate topic for {dataset.title()}:**")
        
        topic = st.text_input(
            "Search Topic",
            value=default_topic,
            key=f"topic_{dataset}",
            placeholder="e.g., sustainable agriculture, climate change, crop yield..."
        )
        
        if topic:
            st.session_state.current_topic = topic
            st.info(f"🔎 Will search for: **{topic}**")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def show_custom_upload(self):
        st.markdown('<div class="upload-area">', unsafe_allow_html=True)
        st.write("📁 Upload your agriculture/climate dataset file")
        
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
        st.write(f"**Topic:** {result.get('topic', 'N/A')}")
        st.write(f"**Output File:** {result['output_file']}")
        st.write(f"**Records Processed:** {result.get('records', 'N/A')}")
        
        # Show preview for certain file types
        if result.get('preview_data') is not None:
            st.subheader("📊 Data Preview")
            st.dataframe(result['preview_data'], use_container_width=True)
            
            # Show additional details for API results
            if result.get('additional_info'):
                st.subheader("📋 Additional Information")
                for key, value in result['additional_info'].items():
                    st.write(f"**{key}:** {value}")
        
        # Download button
        if os.path.exists(result['output_file']):
            with open(result['output_file'], 'rb') as f:
                file_data = f.read()
            st.download_button(
                label="📥 Download Processed Data",
                data=file_data,
                file_name=result['output_file'],
                mime="application/octet-stream"
            )
        
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
        
        # Validate topic for API datasets
        if dataset in ['wikipedia', 'arxiv', 'news']:
            if 'current_topic' not in st.session_state or not st.session_state.current_topic:
                st.error("Please enter a search topic first!")
                return
        
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
        """Process Wikipedia dataset for agriculture/climate topics"""
        topic = st.session_state.current_topic
        st.info(f"🌐 Searching Wikipedia for: {topic}")
        
        try:
            # Search for pages related to the topic
            search_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{topic.replace(' ', '_')}"
            response = requests.get(search_url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Save to file
                output_file = f'wikipedia_{topic.replace(" ", "_")}.json'
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                # Create preview
                preview_data = pd.DataFrame([{
                    'Title': data.get('title', 'Unknown'),
                    'Description': data.get('description', 'No description'),
                    'Extract Length': len(data.get('extract', '')),
                    'URL': data.get('content_urls', {}).get('desktop', {}).get('page', 'N/A')
                }])
                
                return {
                    'dataset': 'Wikipedia Articles',
                    'topic': topic,
                    'output_file': output_file,
                    'records': 1,
                    'preview_data': preview_data,
                    'additional_info': {
                        'Page URL': data.get('content_urls', {}).get('desktop', {}).get('page', 'N/A'),
                        'Timestamp': data.get('timestamp', 'N/A')
                    }
                }
            else:
                # If specific page not found, try search
                st.warning("Specific page not found, trying search...")
                return self._wikipedia_search(topic)
                
        except Exception as e:
            st.warning(f"Using sample data due to API error: {e}")
            return self._create_sample_wikipedia(topic)
    
    def _wikipedia_search(self, topic):
        """Search Wikipedia for topics"""
        try:
            search_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={topic}&format=json&srlimit=3"
            response = requests.get(search_url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                search_results = data.get('query', {}).get('search', [])
                
                if search_results:
                    # Get the first result
                    page_title = search_results[0]['title']
                    return self.process_wikipedia()  # Recursive call with the found title
                
        except Exception as e:
            st.error(f"Search also failed: {e}")
        
        return self._create_sample_wikipedia(topic)
    
    def _create_sample_wikipedia(self, topic):
        """Create sample Wikipedia data"""
        sample_data = {
            "title": f"Sample: {topic}",
            "extract": f"This is sample Wikipedia content about {topic}. In a real implementation, this would contain actual Wikipedia article data about agriculture and climate-related topics.",
            "description": f"Sample article about {topic}",
            "content_urls": {
                "desktop": {
                    "page": f"https://en.wikipedia.org/wiki/{topic.replace(' ', '_')}"
                }
            }
        }
        
        output_file = f'wikipedia_{topic.replace(" ", "_")}.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(sample_data, f, indent=2)
        
        preview_data = pd.DataFrame([{
            'Title': sample_data['title'],
            'Description': sample_data['description'],
            'Content Length': len(sample_data['extract']),
            'Type': 'Sample Data'
        }])
        
        return {
            'dataset': 'Wikipedia Articles (Sample)',
            'topic': topic,
            'output_file': output_file,
            'records': 1,
            'preview_data': preview_data,
            'additional_info': {
                'Note': 'Sample data used due to API limitations'
            }
        }
    
    def process_arxiv(self):
        """Process ArXiv dataset for agriculture/climate topics"""
        topic = st.session_state.current_topic
        st.info(f"📚 Searching ArXiv for: {topic}")
        
        try:
            # Search ArXiv for agriculture and climate related papers
            query = f"all:({topic} agriculture climate)"
            url = f"http://export.arxiv.org/api/query?search_query={query}&start=0&max_results=5&sortBy=submittedDate&sortOrder=descending"
            
            response = requests.get(url, timeout=15)
            if response.status_code == 200:
                root = ET.fromstring(response.content)
                
                papers = []
                for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
                    title_elem = entry.find('{http://www.w3.org/2005/Atom}title')
                    summary_elem = entry.find('{http://www.w3.org/2005/Atom}summary')
                    published_elem = entry.find('{http://www.w3.org/2005/Atom}published')
                    
                    authors = []
                    for author in entry.findall('{http://www.w3.org/2005/Atom}author'):
                        name_elem = author.find('{http://www.w3.org/2005/Atom}name')
                        if name_elem is not None:
                            authors.append(name_elem.text)
                    
                    paper = {
                        'title': title_elem.text.strip() if title_elem is not None else 'No title',
                        'authors': authors,
                        'summary': summary_elem.text.strip() if summary_elem is not None else 'No summary',
                        'published': published_elem.text if published_elem is not None else 'Unknown',
                        'url': None
                    }
                    
                    # Find the PDF link
                    for link in entry.findall('{http://www.w3.org/2005/Atom}link'):
                        if link.get('title') == 'pdf':
                            paper['url'] = link.get('href')
                            break
                    
                    papers.append(paper)
                
                # Save to file
                output_file = f'arxiv_{topic.replace(" ", "_")}.json'
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(papers, f, indent=2, ensure_ascii=False)
                
                # Create preview
                preview_data = pd.DataFrame([{
                    'Title': paper['title'][:60] + '...' if len(paper['title']) > 60 else paper['title'],
                    'Authors': ', '.join(paper['authors'][:2]) + ('...' if len(paper['authors']) > 2 else ''),
                    'Published': paper['published'][:10],
                    'Summary Length': len(paper['summary'])
                } for paper in papers])
                
                return {
                    'dataset': 'ArXiv Papers',
                    'topic': topic,
                    'output_file': output_file,
                    'records': len(papers),
                    'preview_data': preview_data,
                    'additional_info': {
                        'Query Used': query,
                        'Total Results': len(papers)
                    }
                }
                
        except Exception as e:
            st.warning(f"Using sample data due to API error: {e}")
            return self._create_sample_arxiv(topic)
    
    def _create_sample_arxiv(self, topic):
        """Create sample ArXiv data"""
        sample_papers = [
            {
                "title": f"Impact of Climate Change on {topic}",
                "authors": ["Dr. Agriculture Expert", "Prof. Climate Scientist"],
                "summary": f"This research paper examines the effects of climate change on {topic} and proposes sustainable agricultural practices.",
                "published": datetime.now().isoformat(),
                "url": "https://arxiv.org/abs/sample"
            },
            {
                "title": f"Sustainable {topic} Practices in Modern Agriculture",
                "authors": ["Researcher A", "Researcher B"],
                "summary": f"Analysis of sustainable methods for {topic} in the context of environmental conservation.",
                "published": datetime.now().isoformat(),
                "url": "https://arxiv.org/abs/sample"
            }
        ]
        
        output_file = f'arxiv_{topic.replace(" ", "_")}.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(sample_papers, f, indent=2)
        
        preview_data = pd.DataFrame([{
            'Title': paper['title'],
            'Authors': ', '.join(paper['authors']),
            'Published': paper['published'][:10],
            'Type': 'Sample Data'
        } for paper in sample_papers])
        
        return {
            'dataset': 'ArXiv Papers (Sample)',
            'topic': topic,
            'output_file': output_file,
            'records': len(sample_papers),
            'preview_data': preview_data,
            'additional_info': {
                'Note': 'Sample data used due to API limitations'
            }
        }
    
    def process_news(self):
        """Process News Articles for agriculture/climate topics"""
        topic = st.session_state.current_topic
        st.info(f"📰 Searching news for: {topic}")
        
        # Note: In a real implementation, you would use a news API like NewsAPI
        # For demonstration, we'll create sample data
        news_data = [
            {
                "title": f"Breaking: New Developments in {topic}",
                "content": f"This article discusses recent developments in {topic} and their implications for agriculture and climate sustainability.",
                "source": "Agriculture News Network",
                "published_at": datetime.now().isoformat(),
                "category": "Agriculture",
                "url": "https://example.com/news/1"
            },
            {
                "title": f"Climate Impact on {topic} - Expert Analysis",
                "content": f"Experts analyze how climate change is affecting {topic} and what farmers can do to adapt.",
                "source": "Environmental Times",
                "published_at": datetime.now().isoformat(),
                "category": "Climate",
                "url": "https://example.com/news/2"
            },
            {
                "title": f"Sustainable Solutions for {topic} Challenges",
                "content": f"Innovative approaches to address challenges in {topic} while maintaining environmental balance.",
                "source": "Green Agriculture Journal",
                "published_at": datetime.now().isoformat(),
                "category": "Sustainability",
                "url": "https://example.com/news/3"
            }
        ]
        
        # Save to file
        output_file = f'news_{topic.replace(" ", "_")}.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(news_data, f, indent=2)
        
        # Create preview
        preview_data = pd.DataFrame([{
            'Title': article['title'],
            'Category': article['category'],
            'Source': article['source'],
            'Published': article['published_at'][:10],
            'Content Preview': article['content'][:80] + '...'
        } for article in news_data])
        
        return {
            'dataset': 'News Articles',
            'topic': topic,
            'output_file': output_file,
            'records': len(news_data),
            'preview_data': preview_data,
            'additional_info': {
                'Note': 'Sample news data. In production, integrate with NewsAPI or similar service.'
            }
        }
    
    def process_custom_upload(self):
        """Process custom uploaded file"""
        uploaded_file = st.session_state.uploaded_file
        
        st.info(f"📁 Processing {uploaded_file.name}...")
        
        file_ext = os.path.splitext(uploaded_file.name)[1].lower()
        
        if file_ext == '.csv':
            # Process CSV file
            df = pd.read_csv(uploaded_file)
            output_file = 'processed_agriculture_data.csv'
            df.to_csv(output_file, index=False)
            
            return {
                'dataset': 'Custom Agriculture CSV',
                'topic': 'Uploaded File',
                'output_file': output_file,
                'records': len(df),
                'preview_data': df.head()
            }
            
        elif file_ext == '.json':
            # Process JSON file
            data = json.load(uploaded_file)
            output_file = 'processed_agriculture_data.json'
            with open(output_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            # Convert to DataFrame for preview if possible
            if isinstance(data, list):
                preview_data = pd.DataFrame(data)
            else:
                preview_data = pd.DataFrame([data])
            
            return {
                'dataset': 'Custom Agriculture JSON',
                'topic': 'Uploaded File',
                'output_file': output_file,
                'records': len(data) if isinstance(data, list) else 1,
                'preview_data': preview_data.head()
            }
            
        elif file_ext == '.txt':
            # Process text file
            content = uploaded_file.getvalue().decode('utf-8')
            output_file = 'processed_agriculture_data.txt'
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"Agriculture & Climate Dataset\n")
                f.write(f"Processed on: {datetime.now()}\n")
                f.write("="*50 + "\n\n")
                f.write(content)
            
            # Create simple preview
            lines = content.split('\n')[:10]
            preview_content = '\n'.join(lines)
            
            return {
                'dataset': 'Custom Agriculture Text',
                'topic': 'Uploaded File',
                'output_file': output_file,
                'records': len(content.splitlines()),
                'preview_data': pd.DataFrame({'Content Preview': [preview_content[:200] + '...' if len(preview_content) > 200 else preview_content]})
            }
            
        else:
            # For other file types
            output_file = f'processed_agriculture_data{file_ext}'
            with open(output_file, 'wb') as f:
                f.write(uploaded_file.getbuffer())
            
            return {
                'dataset': f'Custom Agriculture {file_ext.upper()}',
                'topic': 'Uploaded File',
                'output_file': output_file,
                'records': 'N/A',
                'preview_data': None
            }

# Sidebar with information
def setup_sidebar():
    st.sidebar.title("ℹ️ About")
    st.sidebar.markdown("""
    **🌱 Agriculture & Climate Dataset App**
    
    A specialized tool for exploring datasets related to:
    
    - **Sustainable Agriculture**
    - **Climate Change Impacts**
    - **Environmental Conservation**
    - **Crop Science & Technology**
    
    **Data Sources:**
    - 🌐 **Wikipedia** - Agricultural & climate articles
    - 📚 **ArXiv** - Research papers & studies  
    - 📰 **News** - Latest developments
    - 📁 **Custom** - Your own datasets
    
    **How to Use:**
    1. Select a data source
    2. Enter your agriculture/climate topic
    3. Process and explore results
    4. Download the data
    """)
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("📊 Quick Stats")
    
    # Show file information if available
    if 'processing_result' in st.session_state:
        result = st.session_state.processing_result
        st.sidebar.metric("Last Processed", result['dataset'])
        st.sidebar.metric("Topic", result.get('topic', 'N/A'))
        st.sidebar.metric("Records", result.get('records', 'N/A'))
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔍 Popular Topics")
    
    popular_topics = [
        "Sustainable agriculture",
        "Climate change agriculture",
        "Precision farming",
        "Organic farming",
        "Water conservation",
        "Soil health",
        "Crop rotation",
        "Renewable energy farming"
    ]
    
    for topic in popular_topics:
        if st.sidebar.button(f"🌿 {topic}", key=f"sidebar_{topic}"):
            if 'selected_dataset' in st.session_state:
                st.session_state.current_topic = topic
                st.rerun()

# JavaScript for enhanced interactivity
def inject_custom_js():
    st.markdown("""
    <script>
    // Add custom JavaScript for enhanced interactivity
    document.addEventListener('DOMContentLoaded', function() {
        // Add click effects to dataset cards
        const cards = document.querySelectorAll('.dataset-card');
        cards.forEach(card => {
            card.addEventListener('click', function() {
                this.style.transform = 'scale(0.98)';
                setTimeout(() => {
                    this.style.transform = '';
                }, 150);
            });
        });
    });
    </script>
    """, unsafe_allow_html=True)

# Main application
def main():
    setup_sidebar()
    inject_custom_js()
    app = StreamlitDatasetApp()

if __name__ == "__main__":
    main()