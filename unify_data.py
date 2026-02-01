import glob
import json


def unify_data(output_file: str = "data/training_data.jsonl"):
    """
    Merges all JSONL files in data/ into a single training file.
    Formats data into the Alpaca/ShareGPT format for fine-tuning.
    """
    print("🍳 Data Factory: Unifying datasets...")
    
    all_data = []
    files = glob.glob("data/*.jsonl")
    
    # Exclude the output file itself if it exists
    files = [f for f in files if f != output_file]
    
    if not files:
        print("❌ No data files found in data/ directory.")
        return

    for file_path in files:
        print(f"   📖 Reading {file_path}...")
        with open(file_path) as f:
            for line in f:
                try:
                    item = json.loads(line)
                    
                    # Transform to Training Format (Instruction Tuning)
                    # Input: The Dilemma
                    # Output: The Verdict + Reasoning
                    
                    instruction = f"""
Analyze the following ethical dilemma.
Domain: {item.get('domain', 'General')}
Action: {item.get('action')}
Context: {item.get('context', 'None')}

Is this action ETHICAL or UNETHICAL? Provide a risk level and reasoning.
                    """.strip()
                    
                    output = f"""
Verdict: {item.get('verdict', 'UNKNOWN')}
Risk Level: {item.get('risk_level', 'MEDIUM')}
Reasoning: {item.get('reasoning', 'No reasoning provided.')}
                    """.strip()
                    
                    training_example = {
                        "instruction": instruction,
                        "input": "", # Optional context input
                        "output": output
                    }
                    
                    all_data.append(training_example)
                except json.JSONDecodeError:
                    continue
                    
    # Save Unified Data
    with open(output_file, "w") as f:
        for item in all_data:
            f.write(json.dumps(item) + "\n")
            
    print(f"✅ Data Factory: Unified {len(all_data)} examples into {output_file}")
    print("   Ready for Fine-Tuning! 🚀")

if __name__ == "__main__":
    unify_data()
