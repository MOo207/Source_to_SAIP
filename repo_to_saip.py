#!/usr/bin/env python3
"""
Script to traverse a directory, respect .gitignore files, and compile all non-ignored
text file contents into a single PDF document.
"""

import os
import re
import sys
import tempfile
import zipfile
import tarfile
from pathlib import Path
import chardet
from typing import List, Set, Optional
import fnmatch
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

# Try to import PDF generation libraries
try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Preformatted
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

class GitIgnoreProcessor:
    """Processes .gitignore files to determine which files should be ignored."""
    
    def __init__(self):
        self.ignores = []
        self.includes = []
    
    def add_pattern(self, pattern: str, is_negative: bool = False):
        """Add a pattern to the ignore list."""
        if pattern.startswith('!'):
            # This is a negative pattern (include)
            pattern = pattern[1:]
            self.includes.append(self._compile_pattern(pattern))
        else:
            self.ignores.append(self._compile_pattern(pattern))
    
    def _compile_pattern(self, pattern: str):
        """Compile a gitignore pattern to a regex."""
        # Normalize the pattern
        pattern = pattern.strip()
        
        # If it starts with /, it's anchored to the directory
        anchored = pattern.startswith('/')
        if anchored:
            pattern = pattern[1:]
        
        # If it ends with /, it only matches directories
        dir_only = pattern.endswith('/')
        if dir_only:
            pattern = pattern[:-1]
        
        # Convert gitignore pattern to regex
        regex_pattern = self._gitignore_to_regex(pattern)
        
        # Anchor to start if originally anchored
        if anchored:
            regex_pattern = '^' + regex_pattern
        else:
            # Allow matching at any level
            regex_pattern = '(/|^)' + regex_pattern
        
        return re.compile(regex_pattern), dir_only
    
    def _gitignore_to_regex(self, pattern: str) -> str:
        """Convert a gitignore pattern to a regex pattern."""
        # Escape special regex characters
        pattern = re.escape(pattern)
        
        # Replace gitignore wildcards with regex equivalents
        pattern = pattern.replace('\\*', '.*')
        pattern = pattern.replace('\\?', '.')
        pattern = pattern.replace('\\[\\!', '[^')
        pattern = pattern.replace('\\]', ']')
        
        # Handle double asterisk (**) for directory recursion
        pattern = pattern.replace('.*.*', '.*')  # Simplified handling
        
        # Add end anchor if pattern doesn't contain wildcards that span directories
        if not ('.*' in pattern or '/' in pattern):
            pattern += '$'
        else:
            pattern += '(/|$)'
        
        return pattern
    
    def is_ignored(self, file_path: str, is_dir: bool = False) -> bool:
        """Check if a file or directory should be ignored based on patterns."""
        # Check include patterns first (negative patterns)
        for pattern, dir_only in self.includes:
            if dir_only and not is_dir:
                continue
            if pattern.search(file_path):
                return False  # This file is explicitly included
        
        # Check ignore patterns
        for pattern, dir_only in self.ignores:
            if dir_only and not is_dir:
                continue
            if pattern.search(file_path):
                return True  # This file is ignored
        
        return False


def extract_archive(archive_path: str, extract_to: str) -> Optional[Path]:
    """Extract archive (ZIP, TAR, etc.) to temporary directory and return the path."""
    archive_path = Path(archive_path)
    extract_to = Path(extract_to)
    
    try:
        if not archive_path.exists():
            print(f"Archive file does not exist: {archive_path}")
            return None
        
        if archive_path.suffix.lower() == '.zip':
            with zipfile.ZipFile(str(archive_path), 'r') as zip_ref:
                zip_ref.extractall(str(extract_to))
        elif archive_path.suffix.lower() in ('.tar', '.tar.gz', '.tgz', '.tar.bz2'):
            with tarfile.open(str(archive_path), 'r:*') as tar_ref:
                tar_ref.extractall(str(extract_to))
        else:
            print(f"Unsupported archive format: {archive_path.suffix}")
            return None
        
        # Return the extracted directory
        return extract_to
    except zipfile.BadZipFile:
        print(f"Invalid ZIP file: {archive_path}")
        return None
    except tarfile.TarError as e:
        print(f"Invalid TAR file: {archive_path} - {e}")
        return None
    except PermissionError:
        print(f"Permission denied when extracting: {archive_path}")
        return None
    except Exception as e:
        print(f"Error extracting archive {archive_path}: {e}")
        return None


def load_gitignore_patterns(directory: Path) -> GitIgnoreProcessor:
    """Load and process .gitignore files in a directory hierarchy."""
    processor = GitIgnoreProcessor()
    
    # Walk up the directory tree to get all parent .gitignore files
    current = directory
    while current != current.parent:
        gitignore_path = current / '.gitignore'
        if gitignore_path.exists():
            with open(str(gitignore_path), 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and not line.startswith('!'):
                        processor.add_pattern(line)
                    elif line.startswith('!'):
                        processor.add_pattern(line, is_negative=True)
        
        current = current.parent
    
    return processor

def is_binary_file(file_path: Path) -> bool:
    """Check if a file is binary by reading the first few bytes."""
    try:
        with open(str(file_path), 'rb') as f:
            chunk = f.read(1024)  # Read first 1KB
            # Check for null bytes or other binary indicators
            if b'\x00' in chunk:
                return True
            
            # Try to decode as text - if it fails, it's likely binary
            try:
                chunk.decode('utf-8')
                return False
            except UnicodeDecodeError:
                return True
    except:
        return True

def detect_encoding(file_path: Path) -> str:
    """Detect the encoding of a file."""
    with open(str(file_path), 'rb') as f:
        raw_data = f.read()
        result = chardet.detect(raw_data)
        encoding = result['encoding']
        confidence = result['confidence']
        
        # If confidence is low, default to utf-8
        if confidence < 0.7:
            return 'utf-8'
        
        return encoding

def read_file_content(file_path: Path) -> Optional[str]:
    """Read file content with proper encoding detection."""
    try:
        # First try UTF-8
        try:
            with open(str(file_path), 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # If UTF-8 fails, detect encoding
            encoding = detect_encoding(file_path)
            with open(str(file_path), 'r', encoding=encoding) as f:
                return f.read()
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return None

def collect_files_with_gitignore(root_path: Path) -> List[Path]:
    """Collect all non-ignored files in the directory tree."""
    all_files = []
    
    # Get gitignore processor for the root
    root_gitignore = load_gitignore_patterns(root_path)
    
    for current_dir, dirs, files in os.walk(root_path):
        current_path = Path(current_dir)
        
        # Load gitignore for this specific directory (for nested gitignores)
        dir_gitignore = load_gitignore_patterns(current_path)
        
        # Filter out directories that should be ignored
        dirs_to_remove = []
        for d in dirs:
            dir_path = current_path / d
            rel_path = dir_path.relative_to(root_path).as_posix()
            
            # Check if this directory should be ignored by any gitignore in the hierarchy
            if root_gitignore.is_ignored(rel_path, is_dir=True) or dir_gitignore.is_ignored(d, is_dir=True):
                dirs_to_remove.append(d)
        
        for d in dirs_to_remove:
            dirs.remove(d)
        
        # Process files in this directory
        for file in files:
            file_path = current_path / file
            rel_path = file_path.relative_to(root_path).as_posix()
            
            # Check if file should be ignored by any gitignore in the hierarchy
            if not root_gitignore.is_ignored(rel_path) and not dir_gitignore.is_ignored(file):
                all_files.append(file_path)
    
    return all_files

def create_pdf_report(files_content: List[tuple], output_path: str):
    """Create a PDF report with the collected file contents."""
    if not PDF_AVAILABLE:
        print("Error: ReportLab library is not installed.")
        print("Install it using: pip install reportlab")
        return False
    
    doc = SimpleDocTemplate(str(output_path), pagesize=A4)
    styles = getSampleStyleSheet()
    
    # Create a custom style for file content
    file_content_style = ParagraphStyle(
        'FileContent',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8,
        leading=10,
        spaceAfter=12
    )
    
    story = []
    
    # Add title
    title = Paragraph("Directory Content Report", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 0.2 * inch))
    
    # Add content for each file
    for file_path, content in files_content:
        # Add file path as header
        header = Paragraph(f"File: {file_path}", styles['Heading2'])
        story.append(header)
        story.append(Spacer(1, 0.1 * inch))
        
        # Add file content (limit length to prevent huge PDFs)
        if len(content) > 10000:  # Limit content length
            content = content[:10000] + "\n... [Content truncated for PDF]"
        
        # Split content into paragraphs to handle long lines
        lines = content.split('\n')
        for line in lines:
            # Replace special characters that might cause issues
            clean_line = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            p = Preformatted(clean_line, file_content_style)
            story.append(p)
        
        # Add spacing between files
        story.append(Spacer(1, 0.2 * inch))
    
    doc.build(story)
    return True

def process_input_path(input_path: str, output_pdf: str = "directory_report.pdf", temp_dir: Optional[str] = None, progress_callback=None) -> bool:
    """Process either a directory or an archive file to create a PDF."""
    input_path = Path(input_path).resolve()
    output_pdf = Path(output_pdf).resolve()
    
    # Validate input path
    if not input_path.exists():
        print(f"Error: Path {input_path} does not exist.")
        if progress_callback:
            progress_callback(0, f"Error: Path {input_path} does not exist.")
        return False
    
    # Check if output directory is writable
    output_dir = output_pdf.parent
    if not output_dir.exists():
        print(f"Error: Output directory {output_dir} does not exist.")
        if progress_callback:
            progress_callback(0, f"Error: Output directory {output_dir} does not exist.")
        return False
    
    try:
        # Test write permission by creating a temporary file
        test_file = output_dir / ".write_test"
        test_file.touch()
        test_file.unlink()  # Remove the test file
    except PermissionError:
        print(f"Error: No write permission in output directory {output_dir}.")
        if progress_callback:
            progress_callback(0, f"Error: No write permission in output directory {output_dir}.")
        return False
    
    # Check if it's an archive file
    archive_extensions = {'.zip', '.tar', '.tar.gz', '.tgz', '.tar.bz2'}
    is_archive = input_path.suffix.lower() in archive_extensions
    
    extracted_path = None
    
    if is_archive:
        # Create a temporary directory for extraction if not provided
        if temp_dir is None:
            temp_dir_obj = tempfile.TemporaryDirectory()
            extract_dir = temp_dir_obj.name
        else:
            extract_dir = temp_dir
        
        print(f"Extracting archive: {input_path}")
        if progress_callback:
            progress_callback(5, f"Extracting archive: {input_path}")
        extracted_path = extract_archive(input_path, extract_dir)
        
        if extracted_path is None:
            print("Failed to extract archive.")
            if progress_callback:
                progress_callback(0, "Failed to extract archive.")
            return False
        
        # If archive contains a single top-level directory, use that
        # Otherwise use the extraction directory
        contents = list(extracted_path.iterdir())
        if len(contents) == 1 and contents[0].is_dir():
            root_path = contents[0]
        else:
            root_path = extracted_path
        
        print(f"Using directory: {root_path}")
    else:
        if not input_path.is_dir():
            print(f"Error: {input_path} is not a directory or supported archive.")
            if progress_callback:
                progress_callback(0, f"Error: {input_path} is not a directory or supported archive.")
            return False
        root_path = input_path
    
    print(f"Scanning: {root_path}")
    if progress_callback:
        progress_callback(10, f"Scanning directory: {root_path}")
    
    # Collect all non-ignored files
    files = collect_files_with_gitignore(root_path)
    print(f"Found {len(files)} non-ignored files")
    if progress_callback:
        progress_callback(20, f"Found {len(files)} files to process")
    
    # Process each file and collect content
    files_content = []
    processed_count = 0
    total_files = len(files)
    
    for i, file_path in enumerate(files):
        if is_binary_file(file_path):
            print(f"Skipping binary file: {file_path}")
            continue
        
        content = read_file_content(file_path)
        if content is not None:
            files_content.append((str(file_path.relative_to(root_path)), content))
            processed_count += 1
            
            # Update progress (20-80% for file processing)
            progress_percent = 20 + int((i / total_files) * 60) if total_files > 0 else 20
            if progress_callback:
                progress_callback(progress_percent, f"Processed {processed_count} of {total_files} files")
            
            if processed_count % 100 == 0:  # Progress indicator
                print(f"Processed {processed_count} files...")
    
    print(f"Successfully processed {processed_count} text files")
    if progress_callback:
        progress_callback(85, f"Successfully processed {processed_count} text files. Creating PDF...")
    
    if not files_content:
        print("No text files found to include in PDF.")
        if progress_callback:
            progress_callback(0, "No text files found to include in PDF.")
        return False
    
    # Create the PDF report
    print(f"Creating PDF report: {output_pdf}")
    success = create_pdf_report(files_content, output_pdf)
    
    if success:
        print(f"PDF report created successfully: {output_pdf}")
        if progress_callback:
            progress_callback(100, f"PDF report created successfully: {output_pdf}")
        return True
    else:
        print("Failed to create PDF report.")
        if progress_callback:
            progress_callback(0, "Failed to create PDF report.")
        return False

def main(input_path: str, output_pdf: str = "directory_report.pdf", progress_callback=None):
    """Main function to process directory or archive and create PDF."""
    return process_input_path(input_path, output_pdf, progress_callback=progress_callback)

class PDFGeneratorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Source Code to PDF Generator")
        self.root.geometry("600x500")
        
        # Variables
        self.input_path = tk.StringVar()
        self.output_path = tk.StringVar(value="directory_report.pdf")
        
        self.setup_ui()
    
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Input section
        ttk.Label(main_frame, text="Input Source:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        input_frame = ttk.Frame(main_frame)
        input_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        input_frame.columnconfigure(0, weight=1)
        
        ttk.Entry(input_frame, textvariable=self.input_path, state="readonly").grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        ttk.Button(input_frame, text="Browse...", command=self.browse_input).grid(row=0, column=1)
        
        # Output section
        ttk.Label(main_frame, text="Output PDF:", font=("Arial", 10, "bold")).grid(row=2, column=0, sticky=tk.W, pady=(10, 5))
        
        output_frame = ttk.Frame(main_frame)
        output_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        output_frame.columnconfigure(0, weight=1)
        
        ttk.Entry(output_frame, textvariable=self.output_path).grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        ttk.Button(output_frame, text="Browse...", command=self.browse_output).grid(row=0, column=1)
        
        # Progress section
        ttk.Label(main_frame, text="Progress:", font=("Arial", 10, "bold")).grid(row=4, column=0, sticky=tk.W, pady=(10, 5))
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, mode='determinate')
        self.progress.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Status label
        self.status_label = ttk.Label(main_frame, text="Ready", foreground="blue")
        self.status_label.grid(row=6, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        
        # Log display
        ttk.Label(main_frame, text="Log:", font=("Arial", 10, "bold")).grid(row=7, column=0, sticky=tk.W, pady=(0, 5))
        
        self.log_text = scrolledtext.ScrolledText(main_frame, height=8, state='disabled')
        self.log_text.grid(row=8, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=9, column=0, columnspan=2, pady=(10, 0))
        
        self.generate_btn = ttk.Button(button_frame, text="Generate PDF", command=self.generate_pdf)
        self.generate_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(button_frame, text="Clear", command=self.clear_fields).pack(side=tk.LEFT)
        
        # Configure grid weights for main frame
        main_frame.rowconfigure(8, weight=1)
    
    def browse_input(self):
        # Ask user if they want to select a file or directory
        choice = messagebox.askquestion("Input Type", "Do you want to select a directory?\n(Click 'No' to select an archive file)")
        
        if choice == 'yes':
            # Select directory
            dir_path = filedialog.askdirectory(title="Select Source Directory")
            if dir_path:
                self.input_path.set(dir_path)
        else:
            # Select archive file
            file_path = filedialog.askopenfilename(
                title="Select Source Archive",
                filetypes=[
                    ("All Supported", ["*.zip", "*.tar", "*.tar.gz", "*.tgz", "*.tar.bz2"]),
                    ("ZIP files", "*.zip"),
                    ("TAR files", "*.tar"),
                    ("TAR.GZ files", "*.tar.gz"),
                    ("TGZ files", "*.tgz"),
                    ("TAR.BZ2 files", "*.tar.bz2"),
                    ("All files", "*.*")
                ]
            )
            if file_path:
                self.input_path.set(file_path)
    
    def browse_output(self):
        file_path = filedialog.asksaveasfilename(
            title="Save PDF Report As",
            defaultextension=".pdf",
            filetypes=[("PDF files", ".pdf"), ("All files", ".*")]
        )
        if file_path:
            self.output_path.set(file_path)
    
    def log_message(self, message):
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, message + '\n')
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')
        self.root.update_idletasks()  # Update the GUI
    
    def update_status(self, message):
        self.status_label.config(text=message)
        self.root.update_idletasks()
    
    def update_progress(self, value):
        self.progress['value'] = value
        self.root.update_idletasks()
    
    def generate_pdf(self):
        input_path = self.input_path.get()
        output_path = self.output_path.get()
        
        if not input_path:
            messagebox.showerror("Error", "Please select an input source.")
            return
        
        if not output_path:
            messagebox.showerror("Error", "Please specify an output PDF file.")
            return
        
        # Validate input path exists
        input_path_obj = Path(input_path)
        if not input_path_obj.exists():
            messagebox.showerror("Error", f"Input path does not exist: {input_path}")
            return
        
        # If it's a file (archive), check if it has a supported extension
        if input_path_obj.is_file():
            archive_extensions = {'.zip', '.tar', '.tar.gz', '.tgz', '.tar.bz2'}
            if input_path_obj.suffix.lower() not in archive_extensions and not input_path_obj.is_dir():
                messagebox.showerror("Error", f"Unsupported file format: {input_path_obj.suffix}.\nSupported formats: .zip, .tar, .tar.gz, .tgz, .tar.bz2")
                return
        
        # Validate output path
        output_path_obj = Path(output_path)
        output_dir = output_path_obj.parent
        if not output_dir.exists():
            messagebox.showerror("Error", f"Output directory does not exist: {output_dir}")
            return
        
        # Check if output directory is writable
        try:
            test_file = output_dir / ".write_test"
            test_file.touch()
            test_file.unlink()  # Remove the test file
        except PermissionError:
            messagebox.showerror("Error", f"No write permission in output directory: {output_dir}")
            return
        
        # Reset progress
        self.progress['value'] = 0
        self.log_text.config(state='normal')
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state='disabled')
        
        # Start the processing in a separate thread to keep the GUI responsive
        import threading
        processing_thread = threading.Thread(target=self.process_files, args=(input_path, output_path))
        processing_thread.daemon = True
        processing_thread.start()
    
    def process_files(self, input_path, output_path):
        try:
            self.update_status("Processing...")
            
            # This is where we call the main processing function
            success = process_input_path(input_path, output_path, progress_callback=self.update_progress_callback)
            
            if success:
                self.update_status("PDF generated successfully!")
                self.log_message(f"Successfully created PDF: {output_path}")
                messagebox.showinfo("Success", f"PDF report created successfully: {output_path}")
            else:
                self.update_status("Failed to generate PDF")
                messagebox.showerror("Error", "Failed to generate PDF report.")
        
        except Exception as e:
            self.update_status(f"Error: {str(e)}")
            self.log_message(f"Error: {str(e)}")
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
        
        finally:
            self.progress['value'] = 100
    
    def update_progress_callback(self, value, message):
        # Update progress bar and status in the GUI
        self.progress['value'] = value
        self.update_status(message)
        self.log_message(message)
        
        # Update the GUI to keep it responsive
        self.root.update_idletasks()
    
    def clear_fields(self):
        self.input_path.set("")
        self.output_path.set("directory_report.pdf")
        self.progress['value'] = 0
        self.status_label.config(text="Ready")
        self.log_text.config(state='normal')
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state='disabled')


def run_gui():
    root = tk.Tk()
    app = PDFGeneratorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    if len(sys.argv) == 1:
        # No arguments provided, run GUI
        run_gui()
    elif len(sys.argv) < 2:
        print("Usage: python repo_to_saip.py <input_path> [output_pdf]")
        print("  <input_path> can be a directory or an archive file (ZIP, TAR, etc.)")
        print("  Or run without arguments to start the GUI")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_pdf = sys.argv[2] if len(sys.argv) > 2 else "directory_report.pdf"
    
    success = main(input_path, output_pdf)
    sys.exit(0 if success else 1)