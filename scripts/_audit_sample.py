"""One-off helper for the extraction accuracy audit (read-only).
Draws a stratified random sample of S2E entries and locates each entry's true
source page via the page-text index (page_number field is unreliable).
Does NOT modify any production data."""
import json, re, random, sys, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def out(s): sys.stdout.buffer.write((str(s)+'\n').encode('utf-8','replace'))

s2e = json.load(open(os.path.join(ROOT,'Dictionary Data','skiri_to_english_respelled.json'), encoding='utf-8'))
index = json.load(open(os.path.join(ROOT,'reports','_s2e_page_index.json'), encoding='utf-8'))
pagelines = {int(p):[l.strip() for l in v['text'].splitlines()] for p,v in index.items()}

def primary_class(gc):
    if not gc: return 'UNKNOWN'
    g = re.split(r'[,/]', gc)[0]
    g = re.sub(r'\(.*?\)','',g).strip()
    return g or 'UNKNOWN'

def locate(hw):
    cands=[hw, re.split(r'[,/]',hw)[0].strip()]
    res=[]
    for p in sorted(pagelines):
        hit=False
        for ln in pagelines[p]:
            for c in cands:
                if c and ln.startswith(c):
                    nxt=ln[len(c):len(c)+1]
                    if nxt in ('',' ','[','(','/',','):
                        res.append(p); hit=True; break
            if hit: break
    return res

# group
groups={}
for x in s2e:
    gc=x.get('part_I',{}).get('grammatical_info',{}).get('grammatical_class')
    groups.setdefault(primary_class(gc),[]).append(x)

# allocation plan (sums to 50) — proportional with floor coverage of minor classes
plan={'N':18,'VT':9,'VI':8,'VD':5,'LOC':2,'ADV':2,'VP':1,'VL':1,'NUM':1}
# 3 from minor/combination classes
minor_pool=['VR','INTERJ','N-KIN','N-DEP','CONJ','ADJ','DEM','PRON','ADV-P','EXCL','QUAN','INTER']

random.seed(42)
sample=[]
for cls,n in plan.items():
    pool=groups.get(cls,[])
    pick=random.sample(pool, min(n,len(pool)))
    for x in pick: sample.append((cls,x))
# minor: pick 3 distinct classes present
present_minor=[c for c in minor_pool if groups.get(c)]
chosen_minor=random.sample(present_minor,3)
for c in chosen_minor:
    x=random.choice(groups[c]); sample.append((c,x))

out('Stratification (primary class -> sampled):')
from collections import Counter
cc=Counter(c for c,_ in sample)
for k,v in cc.most_common(): out('  %s: %d (pool %d)'%(k,v,len(groups.get(k,[]))))
out('Total sample: %d'%len(sample))
out('')

work=[]
for cls,x in sample:
    hw=x['headword']; pI=x.get('part_I',{})
    pages=locate(hw)
    work.append({
        'entry_id':x['entry_id'],'headword':hw,'primary_class':cls,
        'json_page':x['entry_metadata']['page_number'],'column':x['entry_metadata'].get('column'),
        'located_pages':pages,
        'normalized_form':x.get('normalized_form'),
        'phonetic_form':pI.get('phonetic_form'),
        'simplified':pI.get('simplified_pronunciation'),
        'gram':pI.get('grammatical_info'),
        'glosses':pI.get('glosses'),
        'etymology':pI.get('etymology'),
        'cognates':pI.get('cognates'),
        'paradigmatic':x.get('part_II',{}).get('paradigmatic_forms'),
        'examples':x.get('part_II',{}).get('examples'),
    })
json.dump(work, open(os.path.join(ROOT,'reports','_audit_s2e_sample.json'),'w',encoding='utf-8'), ensure_ascii=False, indent=1)
out('Wrote reports/_audit_s2e_sample.json (%d entries)'%len(work))
# show located page summary + any with 0 hits
miss=[w for w in work if not w['located_pages']]
out('Entries with no located page: %d'%len(miss))
for w in work:
    out('  %s | %s | json p%s | located %s'%(w['primary_class'],w['headword'],w['json_page'],w['located_pages']))
