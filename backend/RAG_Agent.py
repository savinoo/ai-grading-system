import os
import sys
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langgraph.graph import StateGraph, START, MessagesState
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver

load_dotenv()

llm = ChatOpenAI(model='gpt-5-nano', temperature=0)
embeddings = OpenAIEmbeddings(model='text-embedding-3-small')

pdf_file = "your_pdf.pdf"
name_file_without_ext = os.path.splitext(os.path.basename(pdf_file))[0]
persist_directory = os.path.join(os.getcwd(), "chroma_db")

if os.path.exists(persist_directory) and os.path.isdir(persist_directory):
    print("Vector Store found. Loading...")
    vectorstore = Chroma(
        persist_directory=persist_directory,
        embedding_function=embeddings,
        collection_name=name_file_without_ext
    )
else:
    print("Vector Store not found. Creating...")
    if not os.path.exists(pdf_file):
        print(f"\n❌ ERROR: PDF file not found: {pdf_file}")
        sys.exit(1)
    print(f"Loading PDF: {pdf_file}")
    loader = PyPDFLoader(pdf_file)
    docs = loader.load()
    print(f"Loaded {len(docs)} pages from PDF")

    if not docs:
        print("\n❌ ERROR: PDF loaded but no pages were found.")
        sys.exit(1)

    total_chars = sum(len(doc.page_content) for doc in docs)
    print(f"Total characters extracted: {total_chars}")

    if total_chars == 0:
        print("\n❌ ERROR: This PDF appears to contain scanned images without text.")
        print("💡 To process this PDF, you would need OCR (Optical Character Recognition).")
        print("🔧 Consider using tools like Tesseract OCR or Adobe Acrobat to convert it to searchable text first.")
        sys.exit(1)

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = text_splitter.split_documents(docs)

    print(f"Split into {len(splits)} chunks")

    if not splits:
        print("\n❌ ERROR: Text splitting resulted in no chunks.")
        sys.exit(1)

    # Filtrar chunks vazios
    splits = [s for s in splits if s.page_content.strip()]

    if not splits:
        print("\n❌ ERROR: All text chunks are empty after filtering.")
        sys.exit(1)

    print(f"Creating vector store with {len(splits)} non-empty chunks...")

    try:
        vectorstore = Chroma.from_documents(
            documents=splits,
            embedding=embeddings,
            persist_directory=persist_directory,
            collection_name=name_file_without_ext
        )
        print("✅ Vector store created successfully!")
    except Exception as e:
        print(f"\n❌ ERROR: Failed to create vector store: {str(e)}")
        sys.exit(1)

retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 5})

@tool
def retriever_tool(query: str) -> str:
    """Searches for information within the PDF document."""
    docs = retriever.invoke(query)
    if not docs:
        return "No relevant information found."
    return "\n\n".join([f"Doc {i+1}: {d.page_content}" for i, d in enumerate(docs)])

tools = [retriever_tool]
llm_with_tools = llm.bind_tools(tools)

def call_model(state: MessagesState):
    messages = state['messages']
    if not isinstance(messages[0], SystemMessage):
        sys_msg = SystemMessage(content=f"""
You are an intelligent AI assistant who answers questions about {name_file_without_ext} based on the PDF document loaded into your knowledge base.
Use the retriever tool available to answer questions about {name_file_without_ext}. You can make multiple calls if needed.
If you need to look up information before asking a follow-up question, you are allowed to do that!
Please always cite the specific part of the documents you use in your answers.
""")
        messages = [sys_msg] + messages

    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

workflow = StateGraph(MessagesState)

workflow.add_node("agent", call_model)
workflow.add_node("tools", ToolNode(tools))

workflow.add_edge(START, "agent")
workflow.add_conditional_edges(
    "agent",
    tools_condition,
)
workflow.add_edge("tools", "agent")

checkpointer = MemorySaver()
app = workflow.compile(checkpointer=checkpointer)

def running_agent():
    thread_id = "user_session_1"
    config = {"configurable": {"thread_id": thread_id}}

    print("\n--- Agent Started ---")

    while True:
        user_input = input("\nYour question: ")
        if user_input.lower() in ['exit', 'quit']:
            break

        events = app.stream(
            {"messages": [HumanMessage(content=user_input)]},
            config,
            stream_mode="values"
        )

        for event in events:
            if "messages" in event:
                current_message = event["messages"][-1]

                if isinstance(current_message, AIMessage) and current_message.tool_calls:
                    for tool_call in current_message.tool_calls:
                        print(f"\n  REASONING: The Agent decided to call '{tool_call['name']}'")
                        print(f"    Arguments: {tool_call['args']}")

                elif isinstance(current_message, ToolMessage):
                    print(f"\n DATA: The tool '{current_message.name}' returned results.")
                    preview = str(current_message.content)[:150].replace('\n', ' ')
                    print(f"    Content: {preview}...")

                elif isinstance(current_message, AIMessage) and not current_message.tool_calls:
                    print(f"\n--- ANSWER ---:\n{current_message.content}")

if __name__ == "__main__":
    running_agent()
