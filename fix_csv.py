import re

with open('qa_sheet_polite.csv', encoding='utf-8') as fin:
    text = fin.read()

# 正規表現で「? ->,」または「？ ->,」で区切る
pattern = r'([^\n]+?[\?？])\s*->,\s*([^\n]+)'
results = re.findall(pattern, text, re.DOTALL)

with open('qa_sheet_polite_fixed.csv', 'w', encoding='utf-8', newline='') as fout:
    fout.write('prompt,completion\n')
    for prompt, completion in results:
        prompt = prompt.strip().replace('\n', ' ')
        completion = completion.strip().replace('\n', ' ')
        fout.write(f'"{prompt}","{completion}"\n') 