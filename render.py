import json
import os
import webbrowser

def visualize_extracted_json(json_data):
    q_images_html = ""
    for img_url in json_data.get("question_image_content", []):
        q_images_html += f'<img src="{img_url}" style="max-width:100%; border: 1px solid #ddd; margin-top: 10px; border-radius: 4px;">'

    options_html = ""
    correct_opt = json_data.get("correct_option")
    
    if json_data.get("options"):
        options_html = "<h4 style='margin-bottom: 5px;'>Options:</h4><ul style='list-style-type: none; padding-left: 0;'>"
        for key, val in json_data["options"].items():

            is_correct = False
            if isinstance(correct_opt, list):
                is_correct = key in correct_opt
            elif isinstance(correct_opt, str):
                is_correct = key == correct_opt
                
            color = "#155724" if is_correct else "#333"
            bg_color = "#d4edda" if is_correct else "transparent"
            border = "1px solid #c3e6cb" if is_correct else "1px solid transparent"
            weight = "bold" if is_correct else "normal"
            
            options_html += f'<li style="color:{color}; background-color:{bg_color}; border:{border}; font-weight:{weight}; padding: 8px; margin-bottom: 4px; border-radius: 4px;"><b>{key})</b> {val}</li>'
        options_html += "</ul>"

    explanations_html = ""
    if json_data.get("explanations"):
        explanations_html = "<h3>Extracted Explanations:</h3>"
        for exp in json_data["explanations"]:
            badge = "<span style='background: #4CAF50; color: white; padding: 2px 8px; border-radius: 12px; font-size: 12px; margin-left: 10px;'>Official / Best Answer</span>" if exp["is_best_answer"] else ""
            explanations_html += f"<div style='background: white; padding: 20px; margin-bottom: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); border-left: 4px solid #007bff;'>"
            explanations_html += f"<h4 style='margin-top: 0;'>Explanation Rank {exp['rank']} {badge}</h4>"

            text_formatted = exp['explanation'].replace('\n', '<br>')
            explanations_html += f"<p style='white-space: pre-wrap;'>{text_formatted}</p>"
            
            for img_url in exp.get("explanation_image_content", []):
                explanations_html += f'<img src="{img_url}" style="max-width:100%; border: 1px solid #ccc; margin-top: 10px; border-radius: 4px;"><br>'
            
            explanations_html += "</div>"
    else:
        explanations_html = "<div style='background: #fff3cd; color: #856404; padding: 15px; border-radius: 8px;'><i>No explanations available for this question.</i></div>"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Gate JSON Extraction Verifier</title>
        
        <script>
        MathJax = {{
          tex: {{
            inlineMath: [['$', '$'], ['\\\\(', '\\\\)']],
            displayMath: [['$$', '$$'], ['\\\\[', '\\\\]']],
            processEscapes: true
          }},
          svg: {{ fontCache: 'global' }}
        }};
        </script>
        <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
        
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; padding: 20px; max-width: 900px; margin: auto; background-color: #f4f7f6; color: #333; }}
            .card {{ background: white; padding: 30px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); margin-bottom: 25px; }}
            .meta-bar {{ display: flex; flex-wrap: wrap; gap: 10px; padding-bottom: 15px; border-bottom: 2px solid #f0f0f0; margin-bottom: 20px; font-size: 0.9em; }}
            .badge {{ background: #e2e8f0; color: #475569; padding: 4px 10px; border-radius: 6px; font-weight: 500; }}
            .badge.subject {{ background: #dbeafe; color: #1e40af; }}
            .badge.type {{ background: #fef3c7; color: #92400e; }}
            .badge.solved {{ background: #d1fae5; color: #065f46; }}
            .tags-container {{ margin-top: 10px; }}
            .tag {{ display: inline-block; background: #f1f5f9; border: 1px solid #cbd5e1; color: #64748b; padding: 2px 8px; border-radius: 12px; font-size: 0.8em; margin-right: 5px; margin-bottom: 5px; }}
        </style>
    </head>
    <body>
        <h2 style="text-align: center; color: #1e293b; margin-bottom: 30px;">GATE JSON Extraction Verifier</h2>
        
        <div class="card">
            <div class="meta-bar">
                <span class="badge subject">Subject: {json_data.get('subject', 'N/A')}</span>
                <span class="badge">Exam: {json_data.get('exam', 'N/A')}</span>
                <span class="badge type">Type: {json_data.get('question_type', 'N/A')}</span>
                <span class="badge solved">Solved: {json_data.get('is_solved', False)}</span>
                <span class="badge">Expl. Available: {json_data.get('is_explanation_available', False)}</span>
            </div>
            
            <div style="margin-bottom: 20px;">
                <h3 style="margin-top: 0;">Extracted Question:</h3>
                <p style="white-space: pre-wrap; font-size: 1.1em;">{json_data.get('question', '')}</p>
                {q_images_html}
            </div>
            
            {options_html}
            
            <div style="margin-top: 20px; padding-top: 15px; border-top: 1px dashed #ccc;">
                <b>Correct Answer Extracted:</b> <span style="font-family: monospace; background: #eee; padding: 2px 6px; border-radius: 4px;">{json_data.get('correct_option', 'None')}</span>
            </div>
            
            <div class="tags-container">
                <b>Tags:</b> {''.join([f'<span class="tag">{t}</span>' for t in json_data.get('tags', [])])}
            </div>
        </div>
        
        {explanations_html}

    </body>
    </html>
    """

    file_path = os.path.abspath("temp_render.html")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"Opening visualization in browser: {file_path}")
    webbrowser.open(f"file:///{file_path}")

if __name__ == "__main__":
    sample_json ={
        "question_id": "523566",
        "exam": "GATE_DA",
        "subject": "Calculus",
        "tags": [
            "goclasses2026-iiith-mock-6",
            "goclasses",
            "one-mark",
            "calculus"
        ],
        "question_type": "MCQ",
        "question": "The infinite series $\\sum_{k=1}^{\\infty} k e^{-k^2}$ $\\_\\_\\_\\_$ (converges/diverges) because the integral $\\int_1^{\\infty} x e^{-x^2} d x=$ $\\_\\_\\_\\_$ .",
        "question_image_content": [],
        "is_solved": True,
        "is_explanation_available": False,
        "options": {
            "A": "diverges, $\\frac{1}{2 e}$",
            "B": "converges, $\\frac{1}{e}$",
            "C": "diverges, $\\frac{1}{e}$",
            "D": "converges, $\\frac{1}{2 e}$"
        },
        "correct_option": "D",
        "explanations": []
    }
    visualize_extracted_json(sample_json)