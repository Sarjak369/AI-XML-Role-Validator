# 🤖 AI Role Validator

**XML ↔ PDF Job Role Comparison powered by LangChain, OpenAI, and ChromaDB**
An intelligent AI-powered validator that compares structured XML-defined job roles against unstructured PDF documents. The system extracts roles from XML, identifies roles in PDFs via Retrieval-Augmented Generation (RAG), and generates a comprehensive validation report showing matched, fuzzy, and incorrect roles—fully automated.

---

## 🌟 Features

### ✨ Core Capabilities

- **📄 XML Role Extraction** - Parse XML files to extract master list of defined job roles
- **📋 PDF Content Extraction** - Extract text and tables from PDFs using PyMuPDF
- **🧠 LLM-Powered Role Extraction** - Uses OpenAI GPT models to identify roles in complex documents
- **🔍 RAG-Based Enhancement** - ChromaDB vector store for semantic search and context retrieval
- **≈ Fuzzy Matching** - Handles typos, abbreviations, and formatting inconsistencies
- **📊 Detailed Validation Reports** - Categorizes roles as direct matches, fuzzy matches, or incorrect
- **⚙️ Configurable Thresholds** - Tune fuzzy matching sensitivity
- **💻 Dual Interface** - CLI and Streamlit web UI

### 🎯 Matching Strategies

1. **Direct Matching** - Exact matches after normalization
2. **Fuzzy Matching** - Catches typos (e.g., "Managar" → "Manager")
3. **Partial Matching** - Handles abbreviations (e.g., "SW Eng" → "Software Engineer")

---

## 🏗️ Project Structure

```bash
AI-Role-Validator/
│
├── .env                              # 🔑 Environment variables (API keys, configs)
├── .gitignore                        # 🚫 Files to exclude from git
├── README.md                         # 📘 Project documentation
├── requirements.txt                  # 📦 Python dependencies
├── app.py                            # 💻 Streamlit web UI
│
├── config/
│   └── config.py                     # ⚙️ Configuration management
│
├── data/                             # 📂 Sample data for testing
│   ├── xml_data/
│   │   └── defined_roles.xml         # XML with correct roles
│   └── pdf_data/
│       └── document_with_roles.pdf   # PDF to validate
│
├── src/                              # 🧠 Core application logic
│   ├── langchain_client.py           # 🔮 LLM and embeddings via LangChain
│   ├── vectorstore_client.py         # 🗄️ ChromaDB vector store operations
│   ├── pdf_extractor_rag.py          # 📘 PDF extraction and RAG pipeline
│   ├── xml_parser.py                 # 📄 XML parsing with XPath
│   ├── role_comparer.py              # ⚖️ Role comparison with fuzzy matching
│   ├── utils.py                      # 🔧 Helper functions
│   └── main.py                       # 🚀 CLI pipeline runner
│
└── chroma_store/                     # 💾 Auto-created ChromaDB storage
    └── role_validator/               # (SQLite + embeddings)
```

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.9+**
- **OpenAI API Key** ([Get one here](https://platform.openai.com/api-keys))
- **UV package manager** (recommended) or pip

### Installation

#### Option 1: Using UV (Recommended)

```bash
# Install UV if you haven't
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone the repository
git clone <your-repo-url>
cd AI-Role-Validator

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
```

#### Option 2: Using pip

```bash
# Clone the repository
git clone <your-repo-url>
cd AI-Role-Validator

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

1. **Create `.env` file** in the project root:

```env
# Copy the example .env file
cp .env .env.local

# Edit .env and add your OpenAI API key
```

2.**Set your OpenAI API Key** in `.env`:

```env
OPENAI_API_KEY=sk-your-api-key-here
```

3.**Optional configurations** in `.env`:

```bash
# Vector database (default: chroma)
VECTOR_DB=chroma

# ChromaDB storage location
CHROMA_PERSIST_DIR=./chroma_store

# PDF chunking settings
PDF_CHUNK_SIZE=1000
PDF_CHUNK_OVERLAP=100

# Fuzzy matching threshold (0-100)
FUZZY_MATCH_THRESHOLD=80

# OpenAI model selection
LLM_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small
```

---

## 📖 Usage

### Method 1: Streamlit Web UI (Recommended for beginners)

```bash
# Run the Streamlit app
streamlit run app.py
```

Then:

1. Open your browser to `http://localhost:8501`
2. Upload your XML file (defined roles)
3. Upload your PDF file (document to validate)
4. Click **"Start Validation"**
5. View the detailed report

### Method 2: Command Line Interface

```bash
# Run the CLI version
python src/main.py
```

**Requirements:**

- Place your XML file at: `data/xml_data/defined_roles.xml`
- Place your PDF file at: `data/pdf_data/document_with_roles.pdf`

The CLI will:

1. Extract roles from XML
2. Process and index the PDF
3. Extract roles from PDF using AI
4. Compare and generate a report
5. Save results to console

---

## 📝 Example Files

### Sample XML (`data/xml_data/defined_roles.xml`)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<roles>
    <role>Software Engineer</role>
    <role>Project Manager</role>
    <role>Senior Developer</role>
    <role>QA Tester</role>
    <role>Business Analyst</role>
    <role>Data Scientist</role>
</roles>
```

### Sample PDF Content

Create a PDF with content like:

```bash
Our team includes a Software Engineer, Project Manager, and Senior Developer.
We are also looking for a Quality Assurance Tester and a Data Analyst.

Staffing Table:
| Role              | Count |
|-------------------|-------|
| Software Engineer | 3     |
| Project Manager   | 1     |
| Marketing Lead    | 2     |
```

---

## 🧪 How It Works

### 1. XML Role Extraction

- Parses XML using `lxml`
- Extracts role text via XPath expressions
- Returns list of ground truth roles

### 2. PDF Processing & RAG

- **Extract**: PyMuPDF extracts text and tables
- **Chunk**: RecursiveCharacterTextSplitter creates semantic chunks
- **Embed**: OpenAI embeddings convert chunks to vectors
- **Store**: ChromaDB stores vectors for retrieval

### 3. Role Extraction from PDF

- Full PDF text sent to OpenAI LLM
- Custom prompt instructs role extraction
- Response parsed into clean role list

### 4. Intelligent Comparison

```bash
For each PDF role:
├─ Try exact match (normalized)
├─ Try fuzzy match (Levenshtein distance)
├─ Try partial match (substring matching)
└─ Mark as incorrect if no matches
```

### 5. Report Generation

- ✅ **Matched**: Roles found in both
- ≈ **Fuzzy**: Similar roles (typos/abbreviations)
- ❌ **Incorrect**: PDF roles not in XML
- ⚠️ **Missing**: XML roles not found in PDF

---

## 🔧 Configuration Options

### Fuzzy Matching Threshold

Controls how similar roles need to be for a fuzzy match (0-100):

- **90-100**: Very strict (only minor typos)
- **80-89**: Moderate (default, handles typos and minor variations)
- **70-79**: Lenient (accepts more abbreviations)
- **Below 70**: Very lenient (may cause false positives)

### LLM Model Selection

In `.env`:

```env
# Cost-effective (recommended for most cases)
LLM_MODEL=gpt-4o-mini

# More powerful (for complex documents)
LLM_MODEL=gpt-4o

# Embeddings
EMBEDDING_MODEL=text-embedding-3-small  # 1536 dimensions
# EMBEDDING_MODEL=text-embedding-3-large  # 3072 dimensions (more accurate, higher cost)
```

---

## 📊 Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **LLM Orchestration** | LangChain | AI workflow management |
| **Language Model** | OpenAI GPT-4 | Role extraction & Q&A |
| **Embeddings** | OpenAI Embeddings | Vector representations |
| **Vector Store** | ChromaDB | Semantic search & retrieval |
| **PDF Processing** | PyMuPDF (fitz) | Text & table extraction |
| **XML Parsing** | lxml | XPath-based extraction |
| **Fuzzy Matching** | thefuzz | String similarity |
| **Web UI** | Streamlit | Interactive interface |

---

## 🐛 Troubleshooting

### Issue: "No roles extracted from PDF"

**Possible causes:**

1. PDF is image-based (needs OCR)
2. Roles are in non-standard format
3. LLM prompt needs adjustment

**Solutions:**

- Use text-based PDFs
- Adjust `ROLE_EXTRACTION_PROMPT` in `config/config.py`
- Try a more powerful model (`gpt-4o`)

### Issue: "OpenAI API key not found"

**Solution:**

- Ensure `.env` file exists in project root
- Verify `OPENAI_API_KEY=sk-...` is set correctly
- Restart your terminal/IDE after creating `.env`

### Issue: "ChromaDB connection error"

**Solution:**

- Delete `chroma_store/` directory
- Restart the application (will recreate)

### Issue: Too many fuzzy matches

**Solution:**

- Increase `FUZZY_MATCH_THRESHOLD` in `.env`
- Default is 80, try 85 or 90

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **LangChain** - Powerful LLM orchestration framework
- **OpenAI** - State-of-the-art language models
- **ChromaDB** - Efficient vector database
- **PyMuPDF** - Excellent PDF processing library

---

## 📧 Contact

For questions or support, please open an issue on GitHub.

---

### Made with ❤️ for automation using AI
