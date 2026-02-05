# Agentic RAG with LangGraph & ChromaDB 🦜🕸️

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![LangChain](https://img.shields.io/badge/LangChain-v0.3-green)
![LangGraph](https://img.shields.io/badge/LangGraph-Stateful-orange)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--5-black)

A stateful **Agentic RAG (Retrieval-Augmented Generation)** system capable of reasoning and maintaining conversation history while chatting with PDF documents.

Built using **LangGraph** for workflow management, **ChromaDB** for vector storage, and **OpenAI** for embeddings and inference.

## 🚀 Features

- **Agentic Workflow**: Uses `LangGraph` to manage state, allowing the model to decide when to call tools (retriever) or answer directly.
- **Persistent Memory**: Uses `MemorySaver` to maintain context across multiple interaction turns within a session.
- **Vector Search**: Ingests PDF documents, chunks them, and stores embeddings in a local `ChromaDB` persistence directory.
- **Smart Retrieval**: Fetches the most relevant document chunks only when necessary.

## 🛠️ Tech Stack

- **LangGraph**: Orchestrates the agent's flow (StateGraph, Nodes, Edges).
- **LangChain**: Handles document loading, text splitting, and tool definitions.
- **ChromaDB**: Local vector database for efficient semantic search.
- **OpenAI API**: Uses `gpt-5` (or similar) for reasoning and `text-embedding-3-small` for embeddings.

## 📂 Project Structure

```text
.
├── chroma_db/                  # Created automatically (Vector Store data)
├── your_pdf.pdf                # Your PDF file here
├── RAG_Agents.py               # The main application script
├── .env                        # API Keys (not committed)
├── .gitignore                  # Git ignore rules
└── requirements.txt            # Python dependencies
```

## ⚙️ Setup & Installation

1. **Clone the repository**
   
   ```bash
   git clone [https://github.com/seu-usuario/nome-do-repo.git](https://github.com/seu-usuario/nome-do-repo.git)
   cd nome-do-repo
   ```
2. **Create a Virtual Environment**
   
   ```bash
   python -m venv venv

   # Windows:
   venv\Scripts\activate
  
   # Mac/Linux:
   source venv/bin/activate
   ```

3. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**

   ```Ini, TOML
   OPENAI_API_KEY=sk-your-openai-key-here
   ```
5. **Add your Document** Place your PDF file in the root directory. 


## ▶️ Usage
Run the agent via the terminal:

   ```bash
   python RAG_Agent.py
   ```
   
The system will:
1. Check if the Vector Store exists. If not, it will process the PDF.
2. Start an interactive session.
3. You can ask questions about the document, and the agent will use the retrieval tool to answer.

Type `exit` or `quit` to stop the application.

## 🤝 Contributing

Feel free to submit issues or pull requests to improve the agent's logic or retrieval accuracy.
