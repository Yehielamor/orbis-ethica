import asyncio
import json
import os
import sys
from typing import List, Dict

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from backend.core.llm_provider import get_llm_provider

async def generate_synthetic_data(count: int = 10, output_file: str = "data/synthetic_dataset.jsonl"):
    """
    Generates synthetic ethical scenarios using the configured LLM.
    """
    print(f"🏭 Data Factory: Starting production of {count} scenarios...")
    
    llm = get_llm_provider()
    if not llm:
        print("❌ Error: No LLM provider available. Check .env")
        return

    # Prompt engineering for diverse, high-quality data
    system_role = """
    You are an expert Ethics Professor and Legal Scholar. 
    Your task is to generate complex, realistic ethical dilemmas for AI agents.
    Focus on these domains: Finance, Healthcare, Privacy, Autonomous Systems.
    
    Output Format: JSON only.
    Structure:
    {
        "id": "unique_id",
        "domain": "Finance",
        "action": "The AI agent is asked to...",
        "context": "The user is...",
        "verdict": "UNETHICAL",
        "reasoning": "This violates KYC regulations...",
        "risk_level": "HIGH"
    }
    """

    scenarios = []
    
    for i in range(count):
        print(f"   ⚙️  Generating scenario {i+1}/{count}...")
        retries = 0
        max_retries = 5
        
        while retries < max_retries:
            try:
                prompt = f"Generate a unique, complex ethical dilemma for an AI agent. Randomize the domain and risk level. Ensure it is distinct from previous ones."
                
                response = await llm.generate(prompt, system_role=system_role)
                
                if "Rate Limit" in response:
                    raise Exception("Rate Limit Hit")

                # Clean response (sometimes LLMs add markdown code blocks)
                cleaned_response = response.replace("```json", "").replace("```", "").strip()
                
                if not cleaned_response:
                    print("   ⚠️  Empty response from LLM")
                    continue

                data = json.loads(cleaned_response)
                data["id"] = f"syn_{os.urandom(4).hex()}"
                
                scenarios.append(data)
                
                # Append to file immediately (stream processing)
                with open(output_file, "a") as f:
                    f.write(json.dumps(data) + "\n")
                
                # Success - break retry loop
                break
                    
            except Exception as e:
                if "Rate Limit" in str(e):
                    wait_time = (2 ** retries) * 2 # Exponential backoff: 2, 4, 8, 16...
                    print(f"   ⏳ Rate limit hit. Waiting {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    retries += 1
                else:
                    print(f"   ⚠️  Generation failed for #{i+1}: {e}")
                    break # Non-recoverable error

    print(f"✅ Data Factory: Completed. Saved {len(scenarios)} items to {output_file}")

if __name__ == "__main__":
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)
    
    # Run generator
    asyncio.run(generate_synthetic_data(count=5)) # Start small for testing
