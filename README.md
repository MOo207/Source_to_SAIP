# 🚀 Source Code to PDF Generator
*Transform your entire codebase into a professional PDF for IP rights applications in seconds!*

## ✨ Why This Tool?
Tired of manually copying and pasting source code for intellectual property applications? This tool automatically generates a comprehensive, organized PDF containing ALL your source code files while intelligently filtering out build artifacts, logs, and temporary files.

## 🌟 Key Features
- **Smart Filtering**: Honors `.gitignore` files to exclude unwanted files automatically
- **Multi-Format Support**: Handles directories, ZIP, TAR, TAR.GZ, TGZ, and TAR.BZ2 archives
- **Encoding Magic**: Automatically detects and handles different file encodings
- **Dual Interface**: Choose between CLI or user-friendly GUI
- **Professional Output**: Clean, organized PDF with file paths and preserved formatting

## 🛠️ Quick Setup

### Install Dependencies
```bash
pip install reportlab chardet
```

### Command Line Usage
```bash
# Basic usage
python repo_to_saip.py <input_path> [output_pdf]

# Examples
python repo_to_saip.py /path/to/your/project              # Default output
python repo_to_saip.py /path/to/your/project output.pdf   # Custom output
python repo_to_saip.py archive.zip source_code.pdf        # Process archive
```

### GUI Mode
```bash
python repo_to_saip.py  # Launch GUI interface
```

## 📸 Screenshots

### GUI Interface
![GUI Interface](https://github.com/MOo207/Source_to_SAIP/blob/master/Usecases/dirs%20showcase.png?raw=true)

*Graphical user interface showing directory selection, output configuration, and progress tracking.*

### PDF Output Example
[PDF output example](https://github.com/MOo207/Source_to_SAIP/blob/master/Usecases/directory_report.pdf?raw=true)

*Example of the generated PDF showing organized source code with proper formatting and file headers.*

## 🎯 Perfect For

### IP Applications
- 📋 **Patent Applications**: Complete documentation for software patents
- 📝 **Copyright Registration**: Professional source code compilation
- 🏷️ **Trademark Submissions**: Software evidence for trademarks
- 🤝 **Licensing**: Complete code documentation for agreements

### Other Use Cases
- 🔍 **Code Audits**: Organized review documentation
- 🔄 **Project Handoffs**: Complete handover documentation
- 💾 **Backup**: Source code preservation in PDF
- ⚖️ **Legal Discovery**: Organized code for legal proceedings

## 💡 Pro Tips

### IP Rights Success
1. 🔍 **Complete Coverage**: Ensure all relevant source files are included
2. 📂 **GitIgnore Check**: Verify .gitignore settings before processing
3. 👀 **Review Output**: Always check the PDF for completeness
4. 💾 **Backup Originals**: Keep source files as reference

### Organization
- 📝 Use descriptive output filenames
- 🧹 Clean directory structure before processing
- 🚫 Update .gitignore for proper exclusions

## 📄 License

This tool helps developers and IP professionals meet documentation requirements. Users are responsible for ensuring their submissions comply with applicable laws and regulations.
