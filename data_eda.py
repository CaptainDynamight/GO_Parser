import json
from collections import Counter

def run_sanity_check(jsonl_filepath):
    print(f"Analyzing {jsonl_filepath}...\n")

    total_records = 0
    corrupt_lines = 0
    math_heavy_questions = 0
    answer_distribution = Counter()
    question_lengths = []
    explanation_counts = []
    best_answer_count = 0

    exams = Counter()
    subjects = Counter()
    question_types = Counter()

    has_solution = 0
    has_explanation = 0
    has_question_image = 0
    has_explanation_image = 0

    empty_question_text = 0
    missing_correct_option = 0
    mcq_without_options = 0

    urls_to_investigate = []

    with open(jsonl_filepath, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            if not line.strip():
                continue
            
            try:
                data = json.loads(line)
                total_records += 1

                exams[data.get('exam', 'UNKNOWN')] += 1
                subjects[data.get('subject', 'UNKNOWN')] += 1
                q_type = data.get('question_type', 'UNKNOWN')
                question_types[q_type] += 1

                if data.get('is_solved'):
                    has_solution += 1
                if data.get('is_explanation_available'):
                    has_explanation += 1

                if data.get('question_image_content'):
                    has_question_image += 1

                explanations = data.get('explanations', [])
                if any(exp.get('explanation_image_content') for exp in explanations):
                    has_explanation_image += 1

                is_anomalous = False
                
                if not data.get('question'):
                    empty_question_text += 1
                    is_anomalous = True
                    
                if not data.get('correct_option'):
                    missing_correct_option += 1
                    is_anomalous = True
                    
                if q_type in ['MCQ', 'MSQ'] and not data.get('options'):
                    mcq_without_options += 1
                    is_anomalous = True

                if is_anomalous and len(urls_to_investigate) < 5:
                    urls_to_investigate.append(data.get('source_url', f'Line {line_num}'))

                if '$' in data.get('question', ''):
                    math_heavy_questions += 1

                ans = data.get('correct_option')
                if isinstance(ans, str) and ans in ['A', 'B', 'C', 'D']:
                    answer_distribution[ans] += 1
                elif isinstance(ans, list):
                    for a in ans:
                        if a in ['A', 'B', 'C', 'D']: answer_distribution[a] += 1

                question_text = data.get('question', '')
                if question_text:
                    question_lengths.append(len(question_text))

                exps = data.get('explanations', [])
                explanation_counts.append(len(exps))
                if any(exp.get('is_best_answer') for exp in exps):
                    best_answer_count += 1
                    
            except json.JSONDecodeError:
                corrupt_lines += 1

    print(f"Total Records Parsed: {total_records:,}")
    if corrupt_lines > 0:
        print(f"Corrupt JSON Lines:   {corrupt_lines:,}")    

    print(f"Have Answer Key (is_solved):      {has_solution:,} ({(has_solution/total_records)*100:.1f}%)")
    print(f"Have Explanations:                {has_explanation:,} ({(has_explanation/total_records)*100:.1f}%)")
    print(f"Questions w/ Images:              {has_question_image:,} ({(has_question_image/total_records)*100:.1f}%)")
    print(f"Explanations w/ Images:           {has_explanation_image:,} ({(has_explanation_image/total_records)*100:.1f}%)")

    print(f"Math/LaTeX Heavy Questions:       {math_heavy_questions:,}")
    print(f"Average Question Length (chars):  {sum(question_lengths)//len(question_lengths) if question_lengths else 0:,}")
    print(f"Average Explanations per Q:       {sum(explanation_counts)/len(explanation_counts) if explanation_counts else 0:.2f}")
    print(f"Questions with a 'Best Answer':   {best_answer_count:,}")
    print(f"Correct Option Distribution:      {dict(answer_distribution)}")

    for qt, count in question_types.most_common():
        print(f"  {qt}: {count:,}")

    print(f"Empty Question Text:      {empty_question_text:,}")
    print(f"Missing Correct Option:   {missing_correct_option:,}")
    print(f"MCQ/MSQ missing Options:  {mcq_without_options:,}")

if __name__ == "__main__":
    DATASET_PATH = "./data/questions_dataset.jsonl" 
    run_sanity_check(DATASET_PATH)