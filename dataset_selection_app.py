import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import requests
import pandas as pd
import json
import os
from datetime import datetime
import xml.etree.ElementTree as ET

class DatasetSelectionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Dataset Selection")
        self.root.geometry("600x500")
        self.root.configure(bg='#f5f7fa')
        
        self.selected_dataset = None
        self.uploaded_file_path = None
        
        self.setup_ui()
        
    def setup_ui(self):
        # Header
        header_frame = tk.Frame(self.root, bg='#4a6ee0', height=80)
        header_frame.pack(fill='x', padx=0, pady=0)
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(header_frame, text="Dataset Selection", 
                              font=('Segoe UI', 16, 'bold'), 
                              bg='#4a6ee0', fg='white')
        title_label.pack(expand=True)
        
        # Main content
        content_frame = tk.Frame(self.root, bg='white', padx=30, pady=30)
        content_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Dataset options frame
        options_frame = tk.Frame(content_frame, bg='white')
        options_frame.pack(fill='x', pady=(0, 20))
        
        # Dataset options
        self.dataset_var = tk.StringVar()
        
        datasets = [
            ("Wikipedia Articles", "wikipedia"),
            ("Scientific Papers (Arxiv)", "arxiv"),
            ("News Articles", "news"),
            ("Custom Upload", "custom")
        ]
        
        for i, (text, value) in enumerate(datasets):
            option_frame = tk.Frame(options_frame, bg='#f8f9fc', relief='raised', bd=1)
            option_frame.pack(fill='x', pady=5)
            option_frame.bind("<Button-1>", lambda e, v=value: self.select_dataset(v))
            
            # Make the entire frame clickable
            for child in [option_frame]:
                child.bind("<Button-1>", lambda e, v=value: self.select_dataset(v))
            
            rb = tk.Radiobutton(option_frame, text=text, variable=self.dataset_var, 
                               value=value, command=lambda v=value: self.select_dataset(v),
                               font=('Segoe UI', 10), bg='#f8f9fc', 
                               selectcolor='#e8edff', activebackground='#edf1fc')
            rb.pack(side='left', padx=15, pady=12)
            
            # Bind radio button events
            rb.bind("<Button-1>", lambda e, v=value: self.select_dataset(v))
        
        # Custom upload area
        self.upload_frame = tk.Frame(content_frame, bg='#f8f9fc', relief='sunken', bd=2)
        self.upload_frame.pack(fill='x', pady=10)
        self.upload_frame.pack_forget()  # Initially hidden
        
        upload_label = tk.Label(self.upload_frame, text="Drag and drop your file here or click to browse",
                               font=('Segoe UI', 9), bg='#f8f9fc', fg='#666')
        upload_label.pack(pady=20)
        
        upload_btn = tk.Button(self.upload_frame, text="Select File", 
                              command=self.upload_file,
                              font=('Segoe UI', 9, 'bold'),
                              bg='#4a6ee0', fg='white',
                              relief='flat', padx=20, pady=8)
        upload_btn.pack(pady=(0, 15))
        
        self.file_info_label = tk.Label(self.upload_frame, text="", 
                                       font=('Segoe UI', 8), bg='#f8f9fc', fg='#666')
        self.file_info_label.pack(pady=(0, 10))
        
        # Process button
        self.process_btn = tk.Button(content_frame, text="Process Selected Datasets", 
                                    command=self.process_datasets,
                                    font=('Segoe UI', 11, 'bold'),
                                    bg='#4a6ee0', fg='white',
                                    relief='flat', padx=30, pady=12,
                                    state='disabled')
        self.process_btn.pack(fill='x', pady=20)
        
    def select_dataset(self, dataset):
        self.selected_dataset = dataset
        self.dataset_var.set(dataset)
        
        # Show/hide upload area
        if dataset == 'custom':
            self.upload_frame.pack(fill='x', pady=10)
        else:
            self.upload_frame.pack_forget()
            self.uploaded_file_path = None
            self.file_info_label.config(text="")
        
        self.update_process_button()
        
    def upload_file(self):
        file_types = [
            ('CSV files', '*.csv'),
            ('JSON files', '*.json'),
            ('Text files', '*.txt'),
            ('XML files', '*.xml'),
            ('All files', '*.*')
        ]
        
        filename = filedialog.askopenfilename(
            title="Select dataset file",
            filetypes=file_types
        )
        
        if filename:
            self.uploaded_file_path = filename
            file_size = os.path.getsize(filename)
            file_info = f"Selected file: {os.path.basename(filename)} ({self.format_file_size(file_size)})"
            self.file_info_label.config(text=file_info)
            self.update_process_button()
    
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
    
    def update_process_button(self):
        if self.selected_dataset:
            if self.selected_dataset == 'custom':
                self.process_btn.config(state='normal' if self.uploaded_file_path else 'disabled')
            else:
                self.process_btn.config(state='normal')
        else:
            self.process_btn.config(state='disabled')
    
    def process_datasets(self):
        if not self.selected_dataset:
            messagebox.showwarning("Warning", "Please select a dataset first!")
            return
        
        if self.selected_dataset == 'custom' and not self.uploaded_file_path:
            messagebox.showwarning("Warning", "Please select a file to upload!")
            return
        
        try:
            # Process based on selected dataset
            if self.selected_dataset == 'wikipedia':
                self.process_wikipedia()
            elif self.selected_dataset == 'arxiv':
                self.process_arxiv()
            elif self.selected_dataset == 'news':
                self.process_news()
            elif self.selected_dataset == 'custom':
                self.process_custom_upload()
                
            messagebox.showinfo("Success", f"Successfully processed {self.selected_dataset} dataset!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to process dataset: {str(e)}")
    
    def process_wikipedia(self):
        """Process Wikipedia dataset"""
        print("Processing Wikipedia Articles...")
        # Example: Fetch random Wikipedia article
        try:
            response = requests.get(
                "https://en.wikipedia.org/api/rest_v1/page/random/summary",
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                print(f"Retrieved Wikipedia article: {data.get('title', 'Unknown')}")
                
                # Save to file
                with open('wikipedia_data.json', 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Wikipedia API error: {e}")
            # Create sample data for demo
            sample_data = {
                "title": "Sample Wikipedia Article",
                "content": "This is sample Wikipedia content for demonstration.",
                "timestamp": datetime.now().isoformat()
            }
            with open('wikipedia_data.json', 'w') as f:
                json.dump(sample_data, f, indent=2)
    
    def process_arxiv(self):
        """Process ArXiv dataset"""
        print("Processing ArXiv Papers...")
        # Example: Fetch recent papers from ArXiv
        try:
            response = requests.get(
                "http://export.arxiv.org/api/query?search_query=all:ai&start=0&max_results=5",
                timeout=15
            )
            if response.status_code == 200:
                root = ET.fromstring(response.content)
                
                papers = []
                for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
                    paper = {
                        'title': entry.find('{http://www.w3.org/2005/Atom}title').text,
                        'authors': [author.find('{http://www.w3.org/2005/Atom}name').text 
                                  for author in entry.findall('{http://www.w3.org/2005/Atom}author')],
                        'summary': entry.find('{http://www.w3.org/2005/Atom}summary').text,
                        'published': entry.find('{http://www.w3.org/2005/Atom}published').text
                    }
                    papers.append(paper)
                
                # Save to file
                with open('arxiv_papers.json', 'w', encoding='utf-8') as f:
                    json.dump(papers, f, indent=2, ensure_ascii=False)
                    
        except Exception as e:
            print(f"ArXiv API error: {e}")
            # Create sample data for demo
            sample_papers = [
                {
                    "title": "Sample AI Research Paper",
                    "authors": ["John Doe", "Jane Smith"],
                    "summary": "This is a sample research paper about artificial intelligence.",
                    "published": datetime.now().isoformat()
                }
            ]
            with open('arxiv_papers.json', 'w') as f:
                json.dump(sample_papers, f, indent=2)
    
    def process_news(self):
        """Process News Articles dataset"""
        print("Processing News Articles...")
        # For demo purposes, create sample news data
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
        with open('news_articles.json', 'w') as f:
            json.dump(news_data, f, indent=2)
    
    def process_custom_upload(self):
        """Process custom uploaded file"""
        if not self.uploaded_file_path:
            raise ValueError("No file selected for upload")
        
        print(f"Processing custom file: {self.uploaded_file_path}")
        
        file_ext = os.path.splitext(self.uploaded_file_path)[1].lower()
        
        if file_ext == '.csv':
            # Process CSV file
            df = pd.read_csv(self.uploaded_file_path)
            print(f"CSV file loaded with {len(df)} rows and {len(df.columns)} columns")
            
            # Save processed data
            df.to_csv('processed_custom_data.csv', index=False)
            
        elif file_ext == '.json':
            # Process JSON file
            with open(self.uploaded_file_path, 'r') as f:
                data = json.load(f)
            print(f"JSON file loaded with {len(data) if isinstance(data, list) else 1} records")
            
            # Save processed data
            with open('processed_custom_data.json', 'w') as f:
                json.dump(data, f, indent=2)
                
        elif file_ext == '.txt':
            # Process text file
            with open(self.uploaded_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            print(f"Text file loaded with {len(content)} characters")
            
            # Save processed data
            with open('processed_custom_data.txt', 'w', encoding='utf-8') as f:
                f.write(f"Processed on: {datetime.now()}\n\n")
                f.write(content)
                
        else:
            # For other file types, just copy
            import shutil
            shutil.copy2(self.uploaded_file_path, 'processed_custom_data' + file_ext)
            print(f"File copied to processed_custom_data{file_ext}")

def main():
    root = tk.Tk()
    app = DatasetSelectionApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()