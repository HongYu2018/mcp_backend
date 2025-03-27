import json
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()  # load environment variables from .env

# Set your OpenAI API key
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Path to the index file
INDEX_PATH = "s3_file_index.json"

def load_index(path=INDEX_PATH):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def find_relevant_chunks(index_data, query, top_k=3):
    candidates = []

    for file, data in index_data.items():
        for i, summary in enumerate(data.get("summaries", [])):
            prompt = f"""
Please provide a analysis answering for the query below by first find the most relevant content based on their question.

Question: {query}

Below is a summary of a text chunk:
\"\"\"
{summary}
\"\"\"

Does this chunk seem relevant to the question? If so, return a relevance score between 0 (not relevant) and 10 (very relevant), followed by a one-line explanation.

Respond in this format: Score: <number>, Reason: <short reason>, Anser: <cause analysis answer>
            """.strip()

            try:
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "You score content relevance to user queries and then use this relevance data to answer the question."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.0
                )
                reply = response.choices[0].message.content
                if "Score:" in reply:
                    score_line = reply.split("Score:")[1].strip()
                    #print("score line:",score_line)
                    score_str, reason, answer = score_line.split(",", 2)
                    score = float(score_str.strip())
                    candidates.append({
                        "file": file,
                        "chunk": i + 1,
                        "score": score,
                        "reason": reason.strip(),
                        "summary": summary,
                        "answer": answer
                    })
            except Exception as e:
                print(f"Error scoring chunk from {file}, chunk {i+1}: {e}")

    # Sort and return top results
    sorted_chunks = sorted(candidates, key=lambda x: x["score"], reverse=True)
    return sorted_chunks[:top_k]

# Example usage
def relevant_chunks_analysis(query):
    index_data = load_index()
    #query = input("Enter your question: ")
    top_chunks = find_relevant_chunks(index_data, query)
    #print("\nTop Relevant Chunks:")
    output_lines = ["Top Relevant Chunks and the answer:"]
    for result in top_chunks:
        if result['score'] >= 0.4:
            #output_lines.append(f"\n📄 File: {result['file']} | Chunk #{result['chunk']} | Score: {result['score']}")
            #output_lines.append(f"{result['reason']}")
            #output_lines.append(f"Summary: {result['summary'][:300]}...")
            #output_lines.append(f"Answer: {result['answer'][:300]}...")
            output_lines.append(f"Related report: {result['answer']}")
    output = '\n'.join(output_lines)
    return output
