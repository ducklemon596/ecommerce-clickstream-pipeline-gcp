"""Profile option shapes per event type in the redacted random pool."""
import sys, json, collections
from urllib.parse import urlsplit, parse_qsl
OPT_KEYS={'alloy','diamond','stone1','stone2','stone3','stone4','pearl','shapediamond'}
S=collections.defaultdict(collections.Counter)
items_per_event=collections.Counter()
examples={}
def url_opts(u):
    try: return {k for k,_ in parse_qsl(urlsplit(u or '').query) if k in OPT_KEYS}
    except Exception: return set()
def item_lists(d):
    if isinstance(d.get('option'),(list,dict)): yield 'root', d.get('option')
    for cp in d.get('cart_products') or []:
        if isinstance(cp,dict): yield 'cart', cp.get('option')
with open(sys.argv[1]) as f:
    for l in f:
        d=json.loads(l)
        c=d.get('collection')
        if not c: continue
        s=S[c]; s['events']+=1
        has_url_opt=bool(url_opts(d.get('current_url')))
        for where,o in item_lists(d):
            t=type(o).__name__
            s[f'{where}:{t}']+=1
            if isinstance(o,list):
                if not o: s[f'{where}:list_empty']+=1; continue
                labels=[ (it or {}).get('value_label') for it in o if isinstance(it,dict)]
                ids=[ (it or {}).get('value_id') for it in o if isinstance(it,dict)]
                blank=all(v in ('',None) for v in labels); anyid=any(v not in ('',None) for v in ids)
                key=f'{where}:list:'+('ID_ONLY' if blank and anyid else 'LABEL+ID' if anyid else 'LABEL_ONLY' if not blank else 'NOTHING')
                s[key]+=1
                if blank and anyid:
                    s[f'{where}:ID_ONLY&url_has_opts' if has_url_opt else f'{where}:ID_ONLY&url_no_opts']+=1
                    examples.setdefault((c,has_url_opt),{k:d.get(k) for k in ('_id','store_id','product_id','option','current_url')} if where=='root' else {'_id':d['_id'],'store_id':d.get('store_id'),'cart_item':o})
                for it in o:
                    if isinstance(it,dict):
                        s['optlabel:'+str(it.get('option_label'))[:25]]+=1
                        s['vid_type:'+type(it.get('value_id')).__name__]+=1
            elif isinstance(o,dict):
                s[f'{where}:dict_keys:'+','.join(sorted(o))[:60]]+=1
for c in sorted(S):
    s=S[c]; print(f"\n## {c}  n={s['events']}")
    for k,v in sorted(s.items(), key=lambda x:-x[1]):
        if k!='events' and (v>=3 or 'ID_ONLY' in k): print(f'   {k}: {v}')
print('\n### EXAMPLES')
for k,v in examples.items(): print(k, json.dumps(v,ensure_ascii=False)[:600])
