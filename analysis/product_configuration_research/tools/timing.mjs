// Investigate the selected key only. Never emit an overlaid configuration.
const mongo = new Mongo("mongodb://127.0.0.1:27017/?directConnection=true");
if (!mongo.getDB("admin").auth(process.env.RESEARCH_MONGO_USER, process.env.RESEARCH_MONGO_PASSWORD)) throw new Error("auth failed");
const collection = mongo.getDB("countly").getCollection("summary");
const anchors = JSON.parse(process.env.RESEARCH_TARGET_IDS || "[]");
const projection = {_id: 1, collection: 1, device_id: 1, store_id: 1, product_id: 1,
  viewing_product_id: 1, time_stamp: 1, current_url: 1, option: 1, api_version: 1};

function queryValues(raw, key) {
  try {
    const url = new URL(String(raw).replace(/&amp;/gi, "&"));
    return [...new Set(url.searchParams.getAll(key).filter(value => value !== ""))];
  } catch (_) { return []; }
}

function selected(document, key) {
  return Array.isArray(document.option) ? document.option.filter(item => item && item.option_label === key
    && typeof item.value_label === "string" && item.value_label).map(item => item.value_label) : [];
}

print(JSON.stringify({_metadata: {method: "stratified selector timing study; indexed 1000-row windows each side; same device/product/store; actual time_stamp ordering within +/-1800 seconds", max_documents_per_anchor: 2001, no_session_completeness_claim: true}}));
let emitted = 0;
for (const id of anchors) {
  const anchor = collection.findOne({_id: ObjectId(id)}, projection);
  if (!anchor) throw new Error("missing source anchor");
  const choices = Array.isArray(anchor.option) ? anchor.option.filter(item => item && typeof item.option_label === "string"
    && typeof item.value_label === "string" && item.value_label) : [];
  const choice = choices.find(item => {const values = queryValues(anchor.current_url, item.option_label);return values.length && !values.includes(item.value_label);})
    || choices.find(item => !queryValues(anchor.current_url, item.option_label).length) || choices[0];
  if (!choice) throw new Error("cohort anchor no longer has an inspectable selected value");
  const key = choice.option_label, product = anchor.product_id;
  const old = queryValues(anchor.current_url, key);
  const kind = old.length ? old.includes(choice.value_label) ? "match" : "conflict" : "missing_key";
  const matches = [];
  let scanned = 0, outOfTime = 0, invalidTime = 0;
  for (const direction of [-1, 1]) {
    const predicate = {_id: direction < 0 ? {$lt: anchor._id} : {$gt: anchor._id}};
    const cursor = collection.find(predicate, projection).hint({_id: 1}).sort({_id: direction}).limit(1000).maxTimeMS(15000);
    while (cursor.hasNext()) {
      const document = cursor.next(); scanned++;
      if (!anchor.device_id || document.device_id !== anchor.device_id || document.store_id !== anchor.store_id
        || String(document.product_id || document.viewing_product_id || "") !== String(product)) continue;
      const delta = Number(document.time_stamp) - Number(anchor.time_stamp);
      if (!Number.isFinite(delta)) {invalidTime++;continue;}
      if (Math.abs(delta) > 1800) {outOfTime++;continue;}
      matches.push({_id: String(document._id), collection: document.collection, seconds_from_anchor: delta,
        url_values_for_key: queryValues(document.current_url, key), selected_values_for_key: selected(document, key)});
    }
  }
  matches.sort((a,b) => a.seconds_from_anchor - b.seconds_from_anchor);
  print(JSON.stringify({_id:id,collection:anchor.collection,kind,key,product_id:product,store_id:anchor.store_id,
    api_version:anchor.api_version,selected_value:choice.value_label,anchor_url_values:old,
    device_id_available:Boolean(anchor.device_id),scanned,matched_count:matches.length,out_of_time:outOfTime,invalid_time:invalidTime,matches}));
  emitted++;
  if (emitted % 20 === 0) console.error("Research: timing anchors inspected " + emitted + "/" + anchors.length);
}
print(JSON.stringify({_completed:{emitted}}));
