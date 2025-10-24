#!/usr/bin/env python3
# 使用方法: python3 k8s_rule_checker2.py <yamlファイル> <kubectl-describe出力ファイル> [rules.json]

import sys, re, json
from pathlib import Path

# 指定されたファイルを読み込み、行ごとのリストと全文を返す関数
def read_file_lines(p):
    txt = Path(p).read_text(encoding='utf-8')
    return txt.splitlines(), txt

# ルール定義をJSONファイルから読み込む関数
def load_rules_from_file(json_path="rules.json"):
    try:
        with open(json_path, encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"ルールファイルの読み込みに失敗しました: {e}")
        sys.exit(1)

# YAMLファイルの中から、指定されたキーに関連する行を探す関数
def find_yaml_matches(lines, key, finder_type):
    if not key:
        return []
    snippet = key.strip().split('/')[-1] if '/' in key else key.strip()
    out = []
    for i, line in enumerate(lines):
        if key in line or snippet in line:
            out.append((i + 1, line.strip()))
        elif 'args:' in line and i + 1 < len(lines) and snippet in lines[i + 1]:
            out.append((i + 2, lines[i + 1].strip()))
    return out

# 指定された行番号の前後数行を抽出して表示用に整形する関数
def context_snippet(lines, lineno, window=2):
    i = lineno - 1
    s = max(0, i - window)
    e = min(len(lines), i + window + 1)
    snippet = []
    for idx in range(s, e):
        snippet.append(f"{idx + 1:3d} {lines[idx]}")
    return "\n".join(snippet)

# describe出力とYAMLファイルを照合し、ルールに一致する箇所を抽出する関数
def analyze(yaml_lines, describe_text, rules):
    results = []
    for r in rules:
        pat = re.compile(r["pattern"], re.IGNORECASE)
        for m in pat.finditer(describe_text):
            key = None
            for g in m.groups():
                if g and ('/' in g or ':' in g or g.endswith('.sh')):
                    key = g
                    break
            key = key or m.group(0)
            matches = find_yaml_matches(yaml_lines, key, r["finder"])
            if matches:
                for lineno, content in matches:
                    results.append({
                        "id": r["id"],
                        "line": lineno,
                        "content": content,
                        "context": context_snippet(yaml_lines, lineno),
                        "template": r["template"]
                    })
            else:
                results.append({
                    "id": r["id"],
                    "line": None,
                    "content": key,
                    "context": None,
                    "template": r["template"]
                })
    return results

# メイン処理関数
def main():
    if len(sys.argv) < 3:
        print("Usage: python3 k8s_rule_checker2.py <yaml-file> <kubectl-describe.txt> [rules.json]")
        sys.exit(1)

    yaml_file, describe_file = sys.argv[1], sys.argv[2]
    rules_file = sys.argv[3] if len(sys.argv) > 3 else "rules.json"

    yaml_lines, _ = read_file_lines(yaml_file)
    _, describe_text = read_file_lines(describe_file)

    rules = load_rules_from_file(rules_file)
    results = analyze(yaml_lines, describe_text, rules)

    has_direct_cause = any(r["id"] in ("missing_file", "exec_failed") for r in results)
    filtered = [r for r in results if not (has_direct_cause and r["id"] == "backoff")]

    shown_lines = set()
    for r in filtered:
        if r["line"] and r["line"] not in shown_lines:
            shown_lines.add(r["line"])
            print(r["context"])
            print()
            print(r["template"].format(line=r["line"], content=r["content"]))
            print()

# スクリプトのエントリーポイント
if __name__ == "__main__":
    main()

