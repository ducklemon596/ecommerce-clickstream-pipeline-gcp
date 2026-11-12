"""Classify current_url of ID-only option events; pick a probe set."""
import sys, json, re, collections, hashlib
from urllib.parse import urlsplit, parse_qsl
OPT={'alloy','diamond','stone1','stone2','stone3','pearl'}
cls=collections.Counter(); probes={'with':[], 'without':[]}; same_val=collections.Counter()
weird=collections.Counter()
def kind(u):
    p=urlsplit(u or ''); path=p.path
    if '/checkout/cart/configure/' in path: return 'cart_configure'
    if path.endswith('.html') or path.endswith('.html/'): return 'product_html'
    if '/catalog/product/view/' in path: return 'catalog_view_id'
    if not u: return 'empty'
    return 'other:'+re.sub(r'\d+','N',path)[:40]
with open(sys.argv[1]) as f:
    for l in f:
        d=json.loads(l); c=d.get('collection')
        if c=='select_product_option_quality':
            for it in d.get('option') or []: weird['spoq_label:'+str(it.get('option_label'))]+=1
        if c=='select_product_option':
            for it in d.get('option') or []:
                if it.get('option_label') in ('pear','stonetow'): weird[f"spo:{it.get('option_label')} vid={it.get('value_id')!r} vl={str(it.get('value_label'))[:20]}"]+=1
        if c not in ('view_product_detail','add_to_cart_action'): continue
        o=d.get('option') or []
        if not (o and all(i.get('value_label') in ('',None) for i in o) and any(i.get('value_id') for i in o)): continue
        u=d.get('current_url') or ''; q={k:v for k,v in parse_qsl(urlsplit(u).query) if k in OPT}
        k=kind(u); cls[(c,k,bool(q))]+=1
        h=int(hashlib.sha1(d['_id'].encode()).hexdigest(),16)
        host=urlsplit(u).hostname or ''
        if host in ('www.glamira.de','www.glamira.co.uk','www.glamira.fr','www.glamira.it','www.glamira.com') and h%997==0:
            rec={'_id':d['_id'],'c':c,'pid':d.get('product_id'),'store':d.get('store_id'),'host':host,'kind':k,'url_opts':q,'ids':[(i['option_label'],i.get('option_id'),i.get('value_id')) for i in o]}
            probes['with' if q else 'without'].append(rec)
for k,v in cls.most_common(): print(k,v)
print(); [print(k,v) for k,v in weird.most_common(25)]
json.dump({k:v[:8] for k,v in probes.items()},open(sys.argv[2],'w'),indent=0)
print({k:len(v) for k,v in probes.items()})
