"""Test: is value_id in ID-only options invariant per (product_id, option_id) while URL tokens vary?"""
import sys, json, collections
from urllib.parse import urlsplit, parse_qsl
URLKEY={'alloy':'alloy','diamond':'diamond'}
vids=collections.defaultdict(set); toks=collections.defaultdict(set); n=collections.Counter()
sel=collections.defaultdict(lambda: collections.defaultdict(set))  # select_product_option: (pid,oid) -> value_id -> labels
with open(sys.argv[1]) as f:
    for l in f:
        d=json.loads(l); c=d.get('collection')
        if c=='select_product_option':
            for it in d.get('option') or []:
                if it.get('value_id') and it.get('option_id'):
                    sel[(d.get('product_id'),str(it['option_id']))][str(it['value_id'])].add(it.get('value_label'))
            continue
        if c not in ('view_product_detail','add_to_cart_action'): continue
        q=dict(parse_qsl(urlsplit(d.get('current_url') or '').query))
        for it in d.get('option') or []:
            if it.get('value_label') or not it.get('value_id'): continue
            k=(d.get('product_id'),str(it.get('option_id')),it.get('option_label'))
            vids[k].add(str(it['value_id'])); n[k]+=1
            toks[k].add(q.get(URLKEY.get(it.get('option_label'),'_'),'<absent>'))
keys=[k for k in vids if n[k]>=5]
inv=sum(1 for k in keys if len(vids[k])==1)
var_url=[k for k in keys if len(toks[k]-{'<absent>'})>=2]
inv_var=sum(1 for k in var_url if len(vids[k])==1)
print(f"(product,option) keys with >=5 ID-only events: {len(keys)}")
print(f"  single value_id: {inv} ({inv/len(keys):.1%})")
print(f"  keys whose URL shows >=2 different tokens: {len(var_url)}; of those single value_id: {inv_var} ({inv_var/max(1,len(var_url)):.1%})")
multi=[k for k in keys if len(vids[k])>1][:5]
for k in multi: print('  multi-vid example',k,n[k],sorted(vids[k])[:5],sorted(toks[k])[:6])
# cross-ref: ID-only value_id vs labels seen for that same id in select_product_option events
hit=lab=0; ex=[]
for k in keys:
    pid,oid,_=k; v=next(iter(vids[k])) if len(vids[k])==1 else None
    if v is None: continue
    m=sel.get((pid,oid),{})
    if v in m:
        hit+=1; labs={x for x in m[v] if x}
        if labs: lab+=1; ex.append((k[2],pid,v,sorted(labs)[:3],sorted(toks[k])[:4]))
print(f"single-vid keys whose value_id also appears in select_product_option: {hit}; with nonempty label: {lab}")
for e in ex[:8]: print('  ',e)
