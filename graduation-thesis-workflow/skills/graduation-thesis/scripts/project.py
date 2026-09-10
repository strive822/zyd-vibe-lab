"""Initialize a private thesis project and check delivery records. Python 3.10+."""
import argparse
import hashlib
import json
from pathlib import Path
import sys


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest() if hasattr(hashlib, 'file_digest') else hashlib.sha256(stream.read()).hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def init(root):
    root = Path(root).resolve()
    if root.exists() and (not root.is_dir() or any(root.iterdir())):
        raise ValueError('Project directory must be absent or empty; nothing was overwritten.')
    root.mkdir(parents=True, exist_ok=True)
    for name in ('school', 'literature', 'data/raw', 'runs', 'manuscript', 'reviews', 'deliverables'):
        (root / name).mkdir(parents=True)
    write_json(root / 'requirements.json', {
        'schema_version': 1, 'version': 1, 'confirmed': False,
        'confirmation_path': '', 'discipline': '', 'topic': '', 'deadline': '',
        'methods': [], 'school_requirements_path': '',
        'ai_policy': {'status': 'unknown', 'source_path': ''},
        'deliverables': [], 'acceptance_criteria': []})
    write_json(root / 'state.json', {
        'schema_version': 1, 'status': 'intake', 'requirements_version': 1,
        'blockers': ['Requirements have not been confirmed.'], 'next_action': 'Run the intake interview.'})
    for name in ('evidence', 'claims', 'artifacts'):
        write_json(root / (name + '.json'), [])
    write_json(root / 'polishing.json', {'status': 'pending', 'tool': 'humanizer'})
    for name, text in {
        'README.md': '# 私有论文项目\n\n先确认需求；个人材料不得自动进入公共工作流仓库。\n',
        'NEXT.md': '# 下一步\n\n完成需求访谈并取得用户确认。\n',
        'DEVLOG.md': '# 执行记录\n\n项目已初始化，尚未进行研究或写作。\n',
        'DECISIONS.md': '# 决策记录\n\n尚无确认的研究方案。\n',
        'GOTCHAS.md': '# 问题记录\n\n按实际失败及修正追加。\n',
        'SOP.md': '# 操作流程\n\n读取需求与状态，使用 graduation-thesis 继续，交付前执行 audit。\n',
        '.gitignore': '*\n!.gitignore\n!README.md\n',
    }.items():
        (root / name).write_text(text, encoding='utf-8')
    return root


def audit(root):
    root = Path(root).resolve()
    errors = []

    def require(condition, message):
        if not condition:
            errors.append(message)

    def read(name, kind):
        try:
            value = json.loads((root / name).read_text(encoding='utf-8-sig'))
            if not isinstance(value, kind):
                raise ValueError('wrong root type')
            return value
        except (OSError, ValueError) as exc:
            errors.append(f'{name}: {exc}')
            return kind()

    def file_check(value, label, sha=None):
        if not isinstance(value, str) or not value.strip():
            errors.append(f'{label}: missing relative path')
            return None
        path = (root / value).resolve()
        if Path(value).is_absolute() or not path.is_relative_to(root):
            errors.append(f'{label}: path must stay inside project')
            return None
        if not path.is_file() or path.stat().st_size == 0:
            errors.append(f'{label}: missing or empty file {value}')
            return None
        if sha is not None and (not isinstance(sha, str) or sha != digest(path)):
            errors.append(f'{label}: SHA256 mismatch or missing hash')
        return path

    def index(items, label):
        result = {}
        for item in items:
            if not isinstance(item, dict):
                errors.append(f'{label}: entries must be objects')
                continue
            key = item.get('id')
            if not isinstance(key, str) or not key.strip() or key in result:
                errors.append(f'{label}: missing or duplicate id')
                continue
            result[key] = item
        return result

    req = read('requirements.json', dict)
    state = read('state.json', dict)
    polishing = read('polishing.json', dict)
    evidence = index(read('evidence.json', list), 'evidence')
    claims = index(read('claims.json', list), 'claims')
    artifacts = index(read('artifacts.json', list), 'artifacts')
    require(req.get('schema_version') == 1 and state.get('schema_version') == 1, 'Unsupported schema version')
    require(req.get('confirmed') is True, 'Requirements not confirmed')
    require(isinstance(req.get('version'), int) and req.get('version', 0) > 0, 'Invalid requirements version')
    require(state.get('requirements_version') == req.get('version'), 'State uses stale requirements')
    require(state.get('status') in {'intake', 'design', 'research', 'drafting', 'review', 'polishing', 'delivery', 'needs_input', 'complete'}, 'Unknown state')
    require(polishing.get('tool') == 'humanizer', 'Humanizer record missing')
    require(polishing.get('status') in ('applied', 'skipped_school_policy'), 'Humanizer stage not completed')
    file_check(polishing.get('review_path'), 'Humanizer review', polishing.get('review_sha256', ''))
    if polishing.get('status') == 'applied':
        file_check(polishing.get('before_path'), 'Before Humanizer', polishing.get('before_sha256', ''))
        file_check(polishing.get('after_path'), 'After Humanizer', polishing.get('after_sha256', ''))
    elif polishing.get('status') == 'skipped_school_policy':
        require(bool(polishing.get('reason')), 'Humanizer policy exception lacks reason')
        file_check(polishing.get('policy_source_path'), 'Humanizer policy exception source')
    require(state.get('blockers') == [], 'Unresolved or malformed blockers')
    file_check(req.get('confirmation_path'), 'User confirmation')
    file_check(req.get('school_requirements_path'), 'School requirements')
    policy = req.get('ai_policy', {})
    if not isinstance(policy, dict):
        policy = {}
    require(policy.get('status') == 'checked', 'School AI policy not checked')
    file_check(policy.get('source_path'), 'AI policy review')
    require(bool(req.get('discipline')) and bool(req.get('topic')), 'Discipline/topic missing')
    methods = req.get('methods')
    require(isinstance(methods, list) and bool(methods) and all(m in ('literature', 'quantitative', 'qualitative', 'engineering', 'experimental') for m in methods), 'Missing or unknown research methods')
    for key, item in evidence.items():
        file_check(item.get('path'), f'Evidence {key}', item.get('sha256', ''))
        require(item.get('kind') in ('literature', 'data', 'run', 'derivation', 'source'), f'Evidence {key}: invalid kind')
        require(bool(item.get('provenance')) and bool(item.get('retrieved_at')), f'Evidence {key}: missing provenance/date')
        require(item.get('verification') in ('checked', 'user_supplied_unverified'), f'Evidence {key}: verification missing')
        if item.get('kind') == 'literature':
            require(item.get('read_scope') in ('metadata', 'abstract', 'fulltext'), f'Evidence {key}: invalid read scope')
            require(bool(item.get('url')), f'Evidence {key}: missing source URL')
    require(bool(evidence), 'No evidence registered')
    require(bool(claims), 'No claims registered')
    for key, item in claims.items():
        require(item.get('status') == 'supported', f'Claim {key}: unsupported or unchecked')
        require(bool(item.get('text')) and bool(item.get('location')), f'Claim {key}: missing text/manuscript location')
        refs = item.get('evidence_ids')
        require(isinstance(refs, list) and bool(refs), f'Claim {key}: no evidence links')
        if not isinstance(refs, list):
            refs = []
        require(item.get('required_scope') in ('metadata', 'abstract', 'fulltext', 'original'), f'Claim {key}: missing scope')
        require(bool(item.get('locator')) and bool(item.get('rationale')), f'Claim {key}: missing locator/support rationale')
        rank = {'metadata': 0, 'abstract': 1, 'fulltext': 2, 'original': 3}
        for ref in refs:
            if not isinstance(ref, str) or ref not in evidence:
                errors.append(f'Claim {key}: unknown evidence id {ref}')
                continue
            source = evidence[ref]
            if source.get('kind') == 'literature':
                require(rank.get(source.get('read_scope'), -1) >= rank.get(item.get('required_scope'), 99), f'Claim {key}: reading scope insufficient')
            if source.get('verification') == 'user_supplied_unverified':
                require(bool(item.get('provenance_disclosure')), f'Claim {key}: disclose unverified user provenance')
    deliverables = req.get('deliverables', [])
    criteria = req.get('acceptance_criteria', [])
    if not isinstance(deliverables, list):
        errors.append('Deliverables must be a list')
        deliverables = []
    if not isinstance(criteria, list):
        errors.append('Acceptance criteria must be a list')
        criteria = []
    required = index(deliverables, 'deliverables')
    require(bool(required), 'No deliverables agreed')
    require(bool(criteria), 'No acceptance criteria recorded')
    for key, expected in required.items():
        artifact = artifacts.get(key)
        if not artifact:
            errors.append(f'Deliverable {key}: missing artifact')
            continue
        require(artifact.get('path') == expected.get('path'), f'Deliverable {key}: wrong path')
        require(artifact.get('status') == 'reviewed', f'Deliverable {key}: not reviewed')
        file_check(artifact.get('path'), f'Deliverable {key}', artifact.get('sha256', ''))
        file_check(artifact.get('review_path'), f'Deliverable {key} review', artifact.get('review_sha256', ''))
    for item in criteria:
        if not isinstance(item, dict):
            errors.append('Acceptance criterion must be an object')
            continue
        require(bool(item.get('id')) and bool(item.get('requirement')), 'Criterion lacks id/requirement')
        require(item.get('status') == 'met', f'Criterion {item.get("id")}: unmet')
        file_check(item.get('review_path'), 'Criterion review', item.get('review_sha256', ''))
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['init', 'audit', 'hash'])
    parser.add_argument('path')
    args = parser.parse_args()
    try:
        if args.command == 'init':
            print(f'Initialized: {init(args.path)}')
        elif args.command == 'hash':
            print(digest(args.path))
        else:
            errors = audit(args.path)
            print(json.dumps({'structural_check': 'FAIL' if errors else 'PASS', 'errors': errors,
                              'notice': 'Record consistency only; not a truth or graduation certificate.'}, ensure_ascii=False, indent=2))
            return 1 if errors else 0
    except (OSError, ValueError) as exc:
        print(f'Error: {exc}', file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
