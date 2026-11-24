"""评分器 — 对 agent 的输出和工作目录变更做客观判定。

支持的方法：
- regex: 在 agent stdout 中搜索正则，匹配数 >= min_matches
- regex_all: 在指定文件中搜索多个正则模式
- test_pass: 在工作目录中执行测试代码，检查输出含 PASS
- file_match: 比对工作目录中文件内容
- files_exist: 检查多个文件存在且含指定内容
"""
import os
import re
import subprocess
import tempfile


def score(task, workspace_dir, agent_stdout):
    """对单个任务评分。返回 {score, reason, details}。"""
    scoring = task["scoring"]
    method = scoring["method"]
    
    if method == "regex":
        return _score_regex(scoring, agent_stdout)
    elif method == "regex_all":
        return _score_regex_all(scoring, workspace_dir, agent_stdout)
    elif method == "test_pass":
        return _score_test_pass(scoring, workspace_dir)
    elif method == "file_match":
        return _score_file_match(scoring, workspace_dir)
    elif method == "files_exist":
        return _score_files_exist(scoring, workspace_dir)
    else:
        return {"score": 0, "reason": f"未知评分方法: {method}"}


def _score_regex(scoring, text):
    pattern = scoring["pattern"]
    min_matches = scoring.get("min_matches", 1)
    matches = re.findall(pattern, text, re.IGNORECASE)
    unique = set(m.lower() if isinstance(m, str) else m for m in matches)
    passed = len(unique) >= min_matches
    return {
        "score": 1 if passed else 0,
        "reason": f"匹配 {len(unique)}/{min_matches} 个模式" + (" ✓" if passed else " ✗"),
        "matches": list(unique),
    }


def _score_regex_all(scoring, workspace_dir, text):
    patterns = scoring["patterns"]
    min_matches = scoring.get("min_matches", len(patterns))
    # 在 agent stdout 和 analysis.md 中搜索
    search_text = text
    for fname in ["analysis.md"]:
        fpath = os.path.join(workspace_dir, fname)
        if os.path.exists(fpath):
            with open(fpath) as f:
                search_text += "\n" + f.read()
    found = 0
    details = []
    for p in patterns:
        if re.search(p, search_text, re.IGNORECASE):
            found += 1
            details.append(f"✓ {p}")
        else:
            details.append(f"✗ {p}")
    passed = found >= min_matches
    return {
        "score": 1 if passed else 0,
        "reason": f"匹配 {found}/{len(patterns)} 个模式 (需 {min_matches})" + (" ✓" if passed else " ✗"),
        "details": details,
    }


def _score_test_pass(scoring, workspace_dir):
    test_code = scoring["test_code"]
    # 写入临时测试文件
    test_file = os.path.join(workspace_dir, "__eval_test__.py")
    with open(test_file, "w") as f:
        f.write(test_code)
    try:
        result = subprocess.run(
            ["python3", test_file],
            cwd=workspace_dir,
            capture_output=True,
            text=True,
            timeout=15,
        )
        passed = "PASS" in result.stdout
        return {
            "score": 1 if passed else 0,
            "reason": "测试通过 ✓" if passed else f"测试失败: {result.stderr[:200]}",
            "stdout": result.stdout[:500],
            "stderr": result.stderr[:500],
        }
    except subprocess.TimeoutExpired:
        return {"score": 0, "reason": "测试超时"}
    except Exception as e:
        return {"score": 0, "reason": f"测试异常: {e}"}
    finally:
        if os.path.exists(test_file):
            os.remove(test_file)


def _score_file_match(scoring, workspace_dir):
    expected_file = scoring["expected_file"]
    expected_content = scoring["expected_content"]
    fpath = os.path.join(workspace_dir, expected_file)
    if not os.path.exists(fpath):
        return {"score": 0, "reason": f"文件 {expected_file} 不存在"}
    with open(fpath) as f:
        actual = f.read()
    passed = actual.strip() == expected_content.strip()
    return {
        "score": 1 if passed else 0,
        "reason": "文件内容匹配 ✓" if passed else f"内容不匹配\n期望:\n{expected_content[:200]}\n实际:\n{actual[:200]}",
    }


def _score_files_exist(scoring, workspace_dir):
    expected_files = scoring["expected_files"]
    check_content = scoring.get("check_content", None)
    found = 0
    details = []
    for fname in expected_files:
        fpath = os.path.join(workspace_dir, fname)
        if os.path.exists(fpath):
            if check_content:
                with open(fpath) as f:
                    content = f.read()
                if check_content in content:
                    found += 1
                    details.append(f"✓ {fname} (含 {check_content})")
                else:
                    details.append(f"△ {fname} 存在但缺少 {check_content}")
            else:
                found += 1
                details.append(f"✓ {fname}")
        else:
            details.append(f"✗ {fname} 不存在")
    passed = found == len(expected_files)
    return {
        "score": 1 if passed else 0,
        "reason": f"{found}/{len(expected_files)} 个文件正确" + (" ✓" if passed else " ✗"),
        "details": details,
    }