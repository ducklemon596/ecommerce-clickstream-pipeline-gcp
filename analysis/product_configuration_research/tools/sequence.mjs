// Bound each probe by the _id index. This is NOT a full session export.
const mongo = new Mongo("mongodb://127.0.0.1:27017/?directConnection=true");
if (!mongo.getDB("admin").auth(process.env.RESEARCH_MONGO_USER, process.env.RESEARCH_MONGO_PASSWORD)) throw new Error("auth failed");
const collection = mongo.getDB("countly").getCollection("summary");
const anchors = JSON.parse(process.env.RESEARCH_TARGET_IDS || "[]");
const keys = new Set(["alloy", "diamond", "stone", "stone2", "stone3", "stone4", "pearl", "synthetic", "leather", "quality", "finish", "profile"]);
const projection = {_id: 1, collection: 1, device_id: 1, store_id: 1, product_id: 1,
  viewing_product_id: 1, time_stamp: 1, current_url: 1, option: 1};

function safePage(raw) {
  try {
    const url = new URL(String(raw).replace(/&amp;/gi, "&"));
    if (!["http:", "https:"].includes(url.protocol) || !/glamira\.[a-z.]+$/i.test(url.hostname)) return null;
    const query = new URLSearchParams();
    for (const [key, value] of url.searchParams) if (keys.has(key)) query.append(key, value);
    return url.protocol + "//" + url.host + url.pathname + (query.size ? "?" + query.toString() : "");
  } catch (_) { return null; }
}

print(JSON.stringify({_metadata: {method: "exact _id anchors plus at most 1000 indexed predecessors and successors per anchor; device+product+store equality applied on VM", window_each_side: 1000, no_full_session_claim: true}}));
let emitted = 0;
for (const id of anchors) {
  const anchor = collection.findOne({_id: ObjectId(id)}, projection);
  if (!anchor) throw new Error("source anchor missing");
  const product = anchor.product_id || anchor.viewing_product_id;
  let scanned = 0;
  const matched = [];
  for (const direction of [-1, 1]) {
    const predicate = {_id: direction < 0 ? {$lt: anchor._id} : {$gt: anchor._id}};
    const cursor = collection.find(predicate, projection).hint({_id: 1}).sort({_id: direction}).limit(1000).maxTimeMS(15000);
    while (cursor.hasNext()) {
      const document = cursor.next(); scanned++;
      if (!anchor.device_id || document.device_id !== anchor.device_id || document.store_id !== anchor.store_id
        || String(document.product_id || document.viewing_product_id || "") !== String(product)) continue;
      const selections = Array.isArray(document.option) ? document.option.map(item => ({
        option_label: item.option_label, value_label: item.value_label,
        quality: item.quality, quality_label: item.quality_label,
      })) : undefined;
      matched.push({_id: String(document._id), collection: document.collection,
        seconds_from_anchor: Number(document.time_stamp) - Number(anchor.time_stamp),
        current_url: safePage(document.current_url), option: selections});
    }
  }
  matched.sort((a, b) => Math.abs(a.seconds_from_anchor) - Math.abs(b.seconds_from_anchor));
  print(JSON.stringify({_id: id, collection: anchor.collection, scanned, matched_count: matched.length,
    device_id_available: Boolean(anchor.device_id), session_id_not_tested: true,
    anchor_current_url: safePage(anchor.current_url),
    matches: matched.slice(0, 16), truncated_matches: matched.length > 16}));
  emitted++;
}
print(JSON.stringify({_completed: {emitted}}));
