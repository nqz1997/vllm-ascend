import json, sys
exp=json.load(open('/tmp/gradeable/expected.json'))
for path in sys.argv[1:]:
    mode=path.split('/')[-2]
    for line in open(path):
        if '\t' not in line: continue
        name,r=line.split('\t',1)
        try: j=json.loads(r)
        except Exception: print(f'{mode}/{name}: BAD-JSON'); continue
        if 'choices' not in j: print(f'{mode}/{name}: NO-CHOICES(bad)'); continue
        t=j['choices'][0]['text']; e=exp[name]['expected_contains']
        ok=e.lower() in t.lower(); rep=len(set(t.split()))<4
        print(f'{mode}/{name}: {"PASS" if ok else "FAIL"} exp~{e!r} got={t[:50]!r} repetitive={rep} finish={j["choices"][0].get("finish_reason")}')
