import asyncio
from playwright.async_api import async_playwright
import json

async def run(playwright):
    with open('ac_data.json', 'r') as f:
        data = json.load(f)
    AcceptanceCriteria = data['Acceptance Criteria']

    # Read the users.json file
    with open('users.json') as file:
        users = json.load(file) 
    
    # Retrieve the email and password for the ai_login user
    email = users['ai_login']['email']
    password = users['ai_login']['password']

    browser = await playwright.firefox.launch(headless=False)    # Setting headless = False
    context = await browser.new_context()
    page = await context.new_page()
    await page.goto('https://www.bing.com/search?q=Bing+AI&showconv=1')
    await asyncio.sleep(1.5)  # Wait for 3 seconds


    await page.fill('#searchbox', "Turn this into manual test cases: " + AcceptanceCriteria)
    await asyncio.sleep(0.5)  # Wait for 3 seconds
    await page.click('button[aria-label="Submit"]')
    await page.wait_for_selector('button.get-started-btn-inline', timeout=0)

   # Get the text content inside the div
    manual_test_cases = await page.inner_text('div.ac-container.ac-adaptiveCard > div.ac-textBlock')
    await browser.close()
    return manual_test_cases

async def main():
    async with async_playwright() as playwright:
        result = await run(playwright)
        return result

def execute():
  MTCs = asyncio.run(main())
  return str(MTCs)