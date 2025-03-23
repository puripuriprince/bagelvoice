import selenium.webdriver as webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import markdownify as md

def scrape_website(website):
    print("Lauching chrome browser...")

    chrome_driver_path = "./chromedriver"
    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(service=Service(), options=options)

    try:
        driver.get(website)

        print("Website opened successfully")

        WebDriverWait(driver, 10).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )

        html = driver.page_source

        return html
    finally:
        driver.quit()


def extract_body_content(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    body = soup.body
    if body:
        return str(body)
    return ""

def clean_body_content(body_content):
    soup = BeautifulSoup(body_content, "html.parser")

    for script_or_style in soup(["script", "style"]):
        script_or_style.extract()

    cleaned_content = soup.get_text(separator="\n")
    cleaned_content = "\n".join(line.strip() for line in cleaned_content.splitlines() if line.strip())

    return cleaned_content

def split_dom_content(dom_content, max_length=7000):
    return [dom_content[i:i + max_length] for i in range(0, len(dom_content), max_length)]

html = scrape_website("https://docs.python.org/3/whatsnew/3.13.html#asyncio")
markdown_text = md.markdownify(html)

data = extract_body_content(html)
cleaned_data = clean_body_content(data)

# Save Markdown content to markdown.txt
with open("markdown.txt", "w", encoding="utf-8") as md_file:
    md_file.write(markdown_text)

# Save cleaned body content to cleaned_data.txt
with open("cleaned_data.txt", "w", encoding="utf-8") as data_file:
    data_file.write(cleaned_data)
