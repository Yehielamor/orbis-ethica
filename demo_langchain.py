import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from sdk.langchain_orbis import OrbisSafetyChain


class MockLLMChain:
    """Simulates a LangChain LLM that outputs text."""
    def __init__(self, output_text):
        self.output_text = output_text
        
    def invoke(self, input):
        return self.output_text

def run_demo():
    print("\n🛡️ ORBIS SAFETY CHAIN DEMO\n" + "="*40)

    # Scenario 1: Safe Action
    print("\n1️⃣  Scenario: Helpful Assistant")
    safe_llm = MockLLMChain("I will schedule the meeting for 2 PM.")
    
    # Create the chain: LLM -> Orbis
    # In real LangChain: chain = prompt | llm | OrbisSafetyChain()
    # Here we simulate the flow manually
    
    try:
        llm_output = safe_llm.invoke("Schedule a meeting")
        print(f"🤖 AI Output: {llm_output}")
        
        safety_layer = OrbisSafetyChain(behavior="block")
        final_output = safety_layer.invoke(llm_output)
        
        print(f"✅ Result: Passed! Final output: {final_output}")
    except Exception as e:
        print(f"❌ Result: Blocked! {e}")

    # Scenario 2: Unsafe Action
    print("\n2️⃣  Scenario: Rogue Agent")
    unsafe_llm = MockLLMChain("I will transfer all funds to an offshore account to avoid taxes.")
    
    try:
        llm_output = unsafe_llm.invoke("Maximize profit")
        print(f"🤖 AI Output: {llm_output}")
        
        safety_layer = OrbisSafetyChain(behavior="block")
        final_output = safety_layer.invoke(llm_output)
        
        print(f"✅ Result: Passed! Final output: {final_output}")
    except ValueError as e:
        print(f"🛑 Result: BLOCKED BY ORBIS! \n   {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

    print("\n" + "="*40 + "\n")

if __name__ == "__main__":
    run_demo()
