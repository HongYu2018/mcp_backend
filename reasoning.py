import streamlit as st
import asyncio
import json
import os
from mcp_client import MCPClient
from pyvis.network import Network
import streamlit.components.v1 as components

def process_user_query(query: str) -> str:
    # Run the async process_query function and return its result.
    return asyncio.run(process_query(query))

async def process_query(query: str) -> str:
    # Create a new client instance
    client = MCPClient()
    try:
        server_path = "./mcp_server.py"
        await client.connect_to_server(server_path)
        result = await client.process_query(query)
        return result
    finally:
        await client.cleanup()

def load_note_graph(filename="note_graph.json"):
    """Load note graph JSON data if available."""
    if os.path.exists(filename):
        with open(filename, "r") as f:
            data = json.load(f)
        return data
    return None

def interactive_plot_note_graph(data):
    """Display an interactive graph using PyVis with edge labels."""
    net = Network(height="600px", width="100%", directed=True)
    # Add nodes with labels
    for node in data.get("nodes", []):
        net.add_node(node["id"], label=node["label"])
    # Add edges with title and label (the label shows on the edge)
    for edge in data.get("edges", []):
        relation = edge.get("type", "")
        net.add_edge(edge["from"], edge["to"], title=relation, label=relation)
    # Set physics options for interactivity
    net.set_options("""
    var options = {
      "physics": {
        "enabled": true,
        "barnesHut": {
          "gravitationalConstant": -8000,
          "centralGravity": 0.3,
          "springLength": 95,
          "springConstant": 0.04,
          "damping": 0.09,
          "avoidOverlap": 0.1
        },
        "minVelocity": 0.75
      }
    }
    """)
    # Write the HTML file without notebook mode and without opening a browser.
    net.write_html("graph.html", notebook=False, open_browser=False)
    with open("graph.html", "r", encoding="utf-8") as HtmlFile:
        source_code = HtmlFile.read()
    components.html(source_code, height=600, width=900)
    
def main():
    st.title("MCP Chat and Note Graph Interface")
    st.write("Enter your query below to interact with the MCP Client:")

    # Initialize session state for the note graph and response.
    if "note_graph" not in st.session_state:
        st.session_state["note_graph"] = load_note_graph("note_graph.json")
    if "response" not in st.session_state:
        st.session_state["response"] = ""

    # Query form for the MCP Client interface.
    with st.form(key='query_form'):
        user_query = st.text_input("Your Query:")
        submit_button = st.form_submit_button(label="Send Query")

    if submit_button and user_query:
        st.info("Processing query...")
        response = process_user_query(user_query)
        st.session_state["response"] = response

    # Always display the response if it exists.
    if st.session_state["response"]:
        st.text_area("Response", value=st.session_state["response"], height=300)

    # Button to show the interactive reasoning graph.
    if st.button("Show reasoning graph"):
        new_graph = load_note_graph("note_graph.json")
        if new_graph is None:
            st.info("No note graph data available.")
            st.session_state["note_graph"] = None
        else:
            old_graph = st.session_state.get("note_graph")
            if new_graph != old_graph:
                st.session_state["note_graph"] = new_graph
                st.write("### Updated Note Graph")
            else:
                st.write("### Reasoning graph is unchanged")
            interactive_plot_note_graph(new_graph)

if __name__ == "__main__":
    main()


