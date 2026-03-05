import json

def build_silver_dataset(input_filepath, clean_filepath, quarantine_filepath, no_answer_no_explanation_filepath):
    print(f"Reading raw data from: {input_filepath}\n")
    
    metrics = {
        "total_processed": 0,
        "corrupt_dropped": 0,
        "empty_text_quarantined": 0,
        "unknown_type_dropped": 0,
        "mcq_missing_opts_dropped": 0,
        "unsolved_noise_dropped": 0,
        "pristine_kept": 0
    }
    
    with open(input_filepath, 'r', encoding='utf-8') as infile, \
         open(clean_filepath, 'w', encoding='utf-8') as clean_out, \
         open(quarantine_filepath, 'w', encoding='utf-8') as quar_out, \
         open(no_answer_no_explanation_filepath, 'w', encoding='utf-8') as no_ans_exp_out:
        
        for line in infile:
            if not line.strip():
                continue
            
            metrics["total_processed"] += 1
            
            # corrupt JSON
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                metrics["corrupt_dropped"] += 1
                continue

            q_text = data.get('question', '').strip()
            q_type = data.get('question_type', 'UNKNOWN')
            opts = data.get('options')
            exps = data.get('explanations', [])
            has_explicit_answer = data.get('correct_option') is not None
            
            # empty questions
            if not q_text:
                quar_out.write(json.dumps(data, ensure_ascii=False) + '\n')
                metrics["empty_text_quarantined"] += 1
                continue
                
            # UNKNOWN question types
            if q_type == 'UNKNOWN':
                metrics["unknown_type_dropped"] += 1
                continue
                
            # broken MCQs
            if q_type in ['MCQ', 'MSQ'] and not opts:
                metrics["mcq_missing_opts_dropped"] += 1
                continue
                
            # unsolved noise
            if not has_explicit_answer and len(exps) == 0:
                metrics["unsolved_noise_dropped"] += 1
                no_ans_exp_out.write(json.dumps(data, ensure_ascii=False) + '\n')
                continue

            clean_out.write(json.dumps(data, ensure_ascii=False) + '\n')
            metrics["pristine_kept"] += 1

    print("CLEAN DATASET REPORT")
    print(f"Total Raw Records:           {metrics['total_processed']:,}\n")

    print(f"Quarantined (Empty/Image):   {metrics['empty_text_quarantined']:,}")
    print(f"Dropped (Corrupt JSON):      {metrics['corrupt_dropped']:,}")
    print(f"Dropped (UNKNOWN Type):      {metrics['unknown_type_dropped']:,}")
    print(f"Dropped (Broken MCQ/MSQ):    {metrics['mcq_missing_opts_dropped']:,}")
    print(f"Dropped (No Ans & No Exp):   {metrics['unsolved_noise_dropped']:,}")
    print(f"Pristine Records Kept:       {metrics['pristine_kept']:,}\n")

if __name__ == "__main__":
    RAW_FILE = "./data/questions_dataset.jsonl" 
    CLEAN_FILE = "./data/questions_clean.jsonl"
    QUARANTINE_FILE = "./data/quarantine_image_only.jsonl"
    NO_ANSWER_NO_EXPLANATION_FILE = "./data/no_answer_no_explanation.jsonl"
    
    build_silver_dataset(RAW_FILE, CLEAN_FILE, QUARANTINE_FILE, NO_ANSWER_NO_EXPLANATION_FILE) 