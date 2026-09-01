"""One-off helper for the extraction audit (read-only): stratified E2S sample."""
import json, re, random, sys, os
from collections import Counter
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def out(s): sys.stdout.buffer.write((str(s)+'\n').encode('utf-8','replace'))

e2s = json.load(open(os.path.join(ROOT,'Dictionary Data','english_to_skiri_linked.json'), encoding='utf-8'))
e2s_index = json.load(open(os.path.join(ROOT,'reports','_e2s_page_index.json'), encoding='utf-8'))
pagelines = {int(p):[l.strip() for l in v['text'].splitlines()] for p,v in e2s_index.items()}

def primary_class(gc):
    if not gc: return 'NONE'
    g=re.split(r'[,/]',gc)[0]; g=re.sub(r'\(.*?\)','',g).strip()
    return g or 'NONE'

def locate(word, pn):
    cands=[]
    for p in sorted(pagelines):
        for ln in pagelines[p]:
            if ln==word or ln.startswith(word+' ') or ln.startswith(word+','):
                cands.append(p); break
    formula = pn+62 if pn < 63 else pn
    if formula in cands: return formula, cands
    return (cands[0] if cands else formula), cands

# Flatten to (entry, subentry) and classify
records=[]
for e in e2s:
    w=e['english_entry_word']; md=e['entry_metadata']
    for sub in e.get('subentries',[]):
        pI=sub.get('part_I',{}) or {}
        gc=(pI.get('grammatical_classification') or {}).get('class_abbr')
        records.append({'word':w,'pn':md['page_number'],'sub':sub,'cls':primary_class(gc),
                        's2e_id':sub.get('s2e_entry_id'),'mt':sub.get('s2e_match_type'),'pI':pI,
                        'part_II':sub.get('part_II'),'part_III':sub.get('part_III')})

# only linked records for cross-check (need s2e_id) — but keep a couple unlinked to verify
linked=[r for r in records if r['s2e_id']]
unlinked=[r for r in records if not r['s2e_id']]
out('Total subentries: %d | linked: %d | unlinked: %d'%(len(records),len(linked),len(unlinked)))
out('Match-type distribution (linked): %s'%Counter(r['mt'] for r in linked).most_common())

groups={}
for r in linked: groups.setdefault(r['cls'],[]).append(r)
out('Class distribution (linked): %s'%Counter(r['cls'] for r in linked).most_common(15))

# allocation: 27 linked stratified + 3 unlinked
plan={'N':10,'VT':5,'VI':4,'VD':3,'ADV':1,'LOC':1,'NUM':1,'VP':1,'INTERJ':1}
random.seed(7)
sample=[]
for cls,n in plan.items():
    pool=groups.get(cls,[])
    for r in random.sample(pool, min(n,len(pool))): sample.append(r)
# ensure mix of match types: swap some to gloss_disambiguated
gd=[r for r in linked if r['mt']=='gloss_disambiguated']
for r in random.sample(gd,3):
    if r not in sample: sample.append(r)
# 3 unlinked
for r in random.sample(unlinked,3): sample.append(r)

out('Sample size: %d'%len(sample))
work=[]
for r in sample:
    pg,cands=locate(r['word'], r['pn']) if True else (None,None)
    work.append({'word':r['word'],'class':r['cls'],'pn':r['pn'],'located':pg,'cands':cands[:6],
                 's2e_id':r['s2e_id'],'match_type':r['mt'],'part_I':r['pI'],
                 'part_II':r['part_II'],'part_III':r['part_III']})
json.dump(work, open(os.path.join(ROOT,'reports','_audit_e2s_sample.json'),'w',encoding='utf-8'), ensure_ascii=False, indent=1)
out('Wrote reports/_audit_e2s_sample.json')
for w in work:
    out('  [%s] %r pn=%s located=printed%s mt=%s s2e=%s'%(w['class'],w['word'],w['pn'],w['located'],w['match_type'],w['s2e_id']))
