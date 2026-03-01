import asyncio
import json
import re
from urllib.parse import urljoin
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

def extract_text_safely(html_content):
    if not html_content:
        return ""

    el = BeautifulSoup(str(html_content), 'html.parser')

    for math_script in el.find_all('script', type=lambda t: t and 'math/tex' in t):
        latex = math_script.string
        if latex:

            delim = "$$" if 'mode=display' in math_script.get('type', '') else "$"

            prev = math_script.find_previous_sibling()
            if prev and any(c in prev.get('class', []) for c in ['MathJax', 'MathJax_Display', 'mjx-chtml', 'MathJax_Preview']):
                prev.decompose()

            math_script.replace_with(f" {delim}{latex.strip()}{delim} ")

    for mjx in el.find_all(class_=lambda c: c and 'mjx-chtml' in c):
        mjx.decompose()

    for br in el.find_all('br'):
        br.replace_with('\n')

    block_tags = ['p', 'div', 'li', 'h1', 'h2', 'h3', 'h4', 'blockquote', 'pre', 'td', 'tr']
    for tag in block_tags:
        for node in el.find_all(tag):
            node.insert_before('\n')
            node.insert_after('\n')

    raw_text = el.get_text(separator=' ')

    raw_text = re.sub(r'[ \t]+', ' ', raw_text)       
    raw_text = re.sub(r'\n[ \t]*\n+', '\n\n', raw_text) 
    
    return raw_text.strip()


async def fetch_question(url: str, exam: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(java_script_enabled=False)
        page = await context.new_page()
        
        print(f"Navigating to {url} ...")
        await page.goto(url, wait_until="domcontentloaded")
        html_content = await page.content()
        await browser.close()

    soup = BeautifulSoup(html_content, 'html.parser')
    
    question_data = {
        "question_id": url.split('/')[-2] if len(url.split('/')) > 2 else "UNKNOWN", 
        "exam": exam,
        "subject": "UNKNOWN", 
        "tags": [],
        "question_type": "UNKNOWN", 
        "question": "",
        "question_image_content": [],
        "is_solved": False,
        "is_explanation_available": False,
        "options": {}, 
        "correct_option": None,
        "explanations": []
    }

    category_element = soup.select_one('.qa-q-view-where-data a, .qa-category-link')
    if category_element:
        question_data["subject"] = category_element.text.strip()

    tag_elements = soup.select('.qa-q-view-tags .qa-tag-link') or soup.select('.qa-tag-link')
    question_data["tags"] = list(dict.fromkeys([tag.text.strip() for tag in tag_elements]))

    q_content_div = soup.select_one('.qa-q-view-content, [itemprop="text"], .entry-content')
    
    if q_content_div:
        for img in q_content_div.find_all('img'):
            if img.get('src'): question_data["question_image_content"].append(urljoin(url, img.get('src')))

        options_extracted = False
        
        list_elements = q_content_div.find_all(['ol', 'ul'])
        if list_elements:
            last_list = list_elements[-1]
            list_items = last_list.find_all('li')
            
            if 2 <= len(list_items) <= 5:
                letters = ['A', 'B', 'C', 'D', 'E']
                for idx, li in enumerate(list_items):
                    question_data["options"][letters[idx]] = extract_text_safely(li)
                
                options_extracted = True
                question_data["question_type"] = "MCQ" 
                last_list.decompose() 

        raw_text = extract_text_safely(q_content_div)
        if not options_extracted:
            option_start_match = re.search(r'(?:\n|\s|^)(\(A\)|A\)|A\.)\s', raw_text, re.IGNORECASE)
            
            if option_start_match:
                start_idx = option_start_match.start()
                question_data["question"] = raw_text[:start_idx].strip()
                options_text = raw_text[start_idx:]
                
                opt_pattern = r'(?:\n|\s|^)(?:\()?([A-D])(?:[\.\)])\s*(.*?)(?=(?:\n|\s|^)(?:\()?[A-D][\.\)]\s*|$)'
                for letter, text in re.findall(opt_pattern, options_text, re.DOTALL | re.IGNORECASE):
                    question_data["question_type"] = "MCQ"
                    question_data["options"][letter.upper()] = text.strip()
            else:
                question_data["question"] = raw_text.strip()
                question_data["question_type"] = "NAT"
                question_data["options"] = None
        else:
            question_data["question"] = raw_text.strip()

    entire_page_text = soup.get_text(separator=' ')
    answer_match = re.search(r'Answer\s*:\s*([A-D](?:\s*[,;]\s*[A-D])*|[\d\.\-]+(?:\s*to\s*[\d\.\-]+)?)', entire_page_text, re.IGNORECASE)
    
    if answer_match:
        raw_ans = answer_match.group(1).upper().strip()
        if ',' in raw_ans or ';' in raw_ans:
            question_data["correct_option"] = [x.strip() for x in re.split(r'[,;]', raw_ans)]
            question_data["question_type"] = "MSQ"
        else:
            question_data["correct_option"] = raw_ans
        question_data["is_solved"] = True 

    answer_items = soup.select('.qa-a-list .qa-a-item-main')
    
    if answer_items:
        question_data["is_solved"] = True
        question_data["is_explanation_available"] = True
        
        for index, ans in enumerate(answer_items):
            ans_content = ans.select_one('.qa-a-item-content')
            if not ans_content: continue

            explanation_text = extract_text_safely(ans_content)
            
            explanation_images = [urljoin(url, img.get('src')) for img in ans_content.find_all('img') if img.get('src')]
            is_best = 'qa-a-item-selected' in ans.parent.get('class', [])

            question_data["explanations"].append({
                "rank": index + 1,
                "is_best_answer": is_best,
                "explanation": explanation_text,
                "explanation_image_content": explanation_images
            })

    return question_data

if __name__ == "__main__":
    test_url = "https://gateoverflow.in/523566/go-classes-iiith-pgee-2026-mock-test-6-question-50"
    
    result = asyncio.run(fetch_question(url=test_url, exam="GATE_DA"))
    
    print("\n--- Extracted JSON Payload ---")
    print(json.dumps(result, indent=2, ensure_ascii=False))