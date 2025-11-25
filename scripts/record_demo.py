import asyncio
import os
from playwright.async_api import async_playwright

async def record_demo():
    """
    Records a video of the Orbis Ethica Real-Time Deliberation Dashboard.
    Requires: pip install playwright && playwright install
    """
    # Ensure videos directory exists
    os.makedirs("videos", exist_ok=True)
    
    async with async_playwright() as p:
        print("🎥 Starting browser...")
        browser = await p.chromium.launch(headless=True) # Set headless=False to watch it live
        
        # Create context with video recording enabled
        context = await browser.new_context(
            record_video_dir="videos/",
            record_video_size={"width": 1280, "height": 720},
            viewport={"width": 1280, "height": 800}
        )
        
        page = await context.new_page()
        
        print("🔗 Navigating to dashboard...")
        await page.goto("http://localhost:4930")
        
        # Wait for page to load
        await page.wait_for_selector("text=Submit Proposal")
        
        print("📝 Filling proposal form...")
        await page.fill("input[type='text']", "Universal Basic Compute")
        await page.select_option("select", "HIGH_IMPACT")
        await page.fill("textarea", "Provide free access to computational resources for all citizens to bridge the digital divide and ensure equal opportunity in the AI era.")
        
        print("🚀 Starting deliberation...")
        await page.click("button[type='submit']")
        
        # Wait for deliberation to complete
        # We look for the "Final Verdict" text which appears at the end
        print("⏳ Waiting for deliberation to complete (this may take a minute)...")
        try:
            await page.wait_for_selector("text=Final Verdict", timeout=60000)
            print("✅ Deliberation complete!")
            
            # Wait a few more seconds to capture the final state
            await page.wait_for_timeout(5000)
            
        except Exception as e:
            print(f"⚠️ Timed out or error: {e}")
        
        # Close context to save video
        await context.close()
        await browser.close()
        
        # Rename the video file (it has a random name by default)
        # Find the latest video file in the directory
        files = [f for f in os.listdir("videos") if f.endswith(".webm")]
        if files:
            latest_video = max([os.path.join("videos", f) for f in files], key=os.path.getctime)
            new_name = "videos/deliberation_demo.webm"
            if os.path.exists(new_name):
                os.remove(new_name)
            os.rename(latest_video, new_name)
            print(f"💾 Video saved to: {new_name}")
        else:
            print("❌ No video file found.")

if __name__ == "__main__":
    asyncio.run(record_demo())
