from flask import Flask, request, jsonify
from flask_cors import CORS
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import regex as re

from rag_retriever import RAGRetriever

# Load a small open model for demonstration
MODEL_NAME = "gpt2"

print("Loading model...", flush=True)
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)
model.eval()

retriever = RAGRetriever()

app = Flask(__name__)
CORS(app)


def clean_output(text: str) -> str:
    text = re.sub(r"((\p{Emoji_Presentation}|\p{Extended_Pictographic})\uFE0F?\s?){2,}", lambda m: m.group(0).split()[0] + " ", text)
    text = re.sub(r"([!?.,])\1{2,}", r"\1", text)
    text = re.sub(r"([!?.,]){2,}", lambda m: ''.join(set(m.group(0))), text)
    text = re.sub(r"\b(\w{2,})\b(?:\s+\1\b)+", r"\1", text, flags=re.IGNORECASE)
    text = re.sub(r"�{2,}", "", text)
    text = re.sub(r"[^\w\s.,!?🤔😐😂💀🔥☝️🗣️🔊]+$", "", text)
    return text.strip()


@app.route("/generate", methods=["POST"])
def generate():
    data = request.json
    prompt = data.get("prompt", "").strip()
    if not prompt:
        return jsonify({"response": ""})

    # Retrieve relevant docs and augment the prompt
    retrieved = retriever.retrieve(prompt)
    context = "\n".join(retrieved)
    final_prompt = f"{context}\n{prompt}\nGurt:"

    inputs = tokenizer(final_prompt, return_tensors="pt")
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=60,
            do_sample=True,
            temperature=0.7,
            top_p=0.95,
            pad_token_id=tokenizer.eos_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )

    full_output = tokenizer.decode(outputs[0], skip_special_tokens=True)
    if "Gurt:" in full_output:
        reply = full_output.split("Gurt:")[-1].strip().split("\n")[0]
    else:
        reply = full_output[len(final_prompt):].strip().split("\n")[0]

    reply = clean_output(reply)
    return jsonify({"response": reply})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
