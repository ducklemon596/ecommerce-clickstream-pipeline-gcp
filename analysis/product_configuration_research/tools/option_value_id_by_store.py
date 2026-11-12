"""Multi-vid keys: does value_id vary by store? And select_product_option label/id consistency."""
import sys, json, collections
by=collections.defaultdict(lambda: collections.defaultdict(set))  # key -> store -> vids
n=collections.Counter(); spo=collections.defaultdict(set); spo_n=0; spo_lab=collections.defaultdict(set)
with open(sys.argv[1]) as f:
    for l in f:
        d=json.loads(l); c=d.get('collection')
        if c=='select_product_option':
            for it in d.get('option') or []:
                if it.get('value_id') and it.get('value_label'):
                    spo[(d.get('product_id'),str(it['option_id']),str(it['value_id']))].add(it['value_label'])
                    spo_lab[(d.get('product_id'),str(it['option_id']),it['value_label'])].add(str(it['value_id']))
        if c not in ('view_product_detail','add_to_cart_action'): continue
        for it in d.get('option') or []:
            if it.get('value_label') or not it.get('value_id'): continue
            k=(d.get('product_id'),str(it.get('option_id'))); by[k][d.get('store_id')].add(str(it['value_id'])); n[k]+=1
multi=[k for k in by if n[k]>=5 and len(set().union(*by[k].values()))>1]
within=sum(1 for k in multi if any(len(v)>1 for v in by[k].values()))
print(f"multi-vid keys: {len(multi)}; with >1 vid inside a single store: {within} ({within/len(multi):.1%}); purely store-separated: {len(multi)-within}")
dv=collections.Counter(len(set().union(*by[k].values())) for k in multi); print('distinct vids per multi key:',sorted(dv.items())[:8])
a=sum(1 for v in spo.values() if len(v)>1); print(f"select_product_option (pid,opt,value_id) triples: {len(spo)}; with >1 distinct label: {a} ({a/len(spo):.1%})")
b=sum(1 for v in spo_lab.values() if len(v)>1); print(f"select_product_option (pid,opt,label) triples: {len(spo_lab)}; with >1 distinct value_id: {b} ({b/len(spo_lab):.1%})")
