import json
import os
import re
from openai import OpenAI
from chunk_retrival import relevant_chunks_analysis
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_reasoning_and_graph(query):
    # Get top relevant text only (summarized or merged)
    relevant_text = relevant_chunks_analysis(query)

    # Truncate text to ~3000 tokens worth (~12K characters)
    if len(relevant_text) > 12000:
        relevant_text = relevant_text[:4000]

    # Short prompt for summary
    reasoning_prompt = (
        f"Summarize and analyze the key points related to this query: '{query}'. "
        "Use simple, clear language, and provide key findings and a brief conclusion.\n\n"
        f"Context:\n{relevant_text}"
    )

    reasoning_response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "user", "content": reasoning_prompt}
        ],
        temperature=0.2
    )
    human_summary = reasoning_response.choices[0].message.content.strip()

    # Short prompt for JSON graph
    graph_prompt = (
        "Based on the following context, extract a JSON object representing a knowledge graph.\n\n"
        "Format:\n"
        '{ "nodes": [{"id": "N1", "label": "Key point"}], '
        '"edges": [{"from": "N1", "to": "N2", "type": "causes"}] }\n\n'
        "Only output the raw JSON. Use double quotes. No comments, no markdown.\n\n"
        f"Context:\n{relevant_text}"
    )
    #print("[DEBUG] Sending reasoning prompt to OpenAI...", flush=True)

    graph_response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": graph_prompt}],
        temperature=0.2
    )

    graph_json_raw = graph_response.choices[0].message.content.strip()

    try:
        if "```" in graph_json_raw:
            graph_json_raw = re.search(r"```(?:json)?(.*?)```", graph_json_raw, re.DOTALL).group(1).strip()

        graph_data = json.loads(graph_json_raw)

        with open("note_graph.json", "w", encoding="utf-8") as f:
            json.dump(graph_data, f, indent=2, ensure_ascii=False)

        #print("[OK] Note graph saved to note_graph.json", flush=True)

    except Exception as e:
        print(f"[ERROR] Could not parse graph JSON: {e}", flush=True)
        print(f"[DEBUG] Raw output:\n{graph_json_raw[:300]}", flush=True)
        graph_data = {}
        
    #print("[DEBUG] MCP Client finishing. Cleaning up...", flush=True)

    return human_summary, graph_data
