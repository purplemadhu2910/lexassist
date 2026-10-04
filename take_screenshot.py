import time
import os
from selenium import webdriver
from selenium.webdriver.edge.options import Options

options = Options()
options.add_argument("--headless=new")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1400,1800")

driver = webdriver.Edge(options=options)
try:
    print("Navigating to http://127.0.0.1:8000/docs...")
    driver.get("http://127.0.0.1:8000/docs")
    time.sleep(4)
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "api_documentation_screenshot.png")
    driver.save_screenshot(out_path)
    print(f"Screenshot saved successfully to: {out_path}")
finally:
    driver.quit()
