// Research only: read one random pool, redact on the VM, and stream evidence.
// Authentication is passed in the process environment by capture.py.
const sampleSize = Number(process.env.RESEARCH_SAMPLE_SIZE || 300000);
const targetIds = JSON.parse(process.env.RESEARCH_TARGET_IDS || "[]");
const knownOptions = new Set([
  "alloy", "diamond", "stone", "stone2", "stone3", "stone4", "pearl",
  "pearlcolor", "synthetic", "accent", "leather", "quality", "quality2",
  "quality3", "finish", "profile", "shape", "shapediamond", "width",
  "bandwidth", "size", "ring_size", "ringsize",
]);
const mongo = new Mongo("mongodb://127.0.0.1:27017/?directConnection=true");
if (!mongo.getDB("admin").auth(process.env.RESEARCH_MONGO_USER, process.env.RESEARCH_MONGO_PASSWORD)) {
  throw new Error("MongoDB authentication failed");
}
const database = mongo.getDB(process.env.RESEARCH_DATABASE || "countly");
const collection = database.getCollection(process.env.RESEARCH_COLLECTION || "summary");
console.error("Research: authenticated; collecting source metadata");

function privateText(value) {
  return typeof value === "string" && (/[^\s@]+@[^\s@]+\.[^\s@]+/.test(value)
    || /(?:\d{1,3}\.){3}\d{1,3}/.test(value));
}

function safeOption(value) {
  if (Array.isArray(value)) return value.map(safeOption);
  if (!value || typeof value !== "object") return privateText(value) ? "[REDACTED]" : value;
  const freeText = Object.entries(value).some(([key, text]) => /label|name/i.test(key)
    && /engrav|inscri|message|personal|free.?text/i.test(String(text)));
  return Object.fromEntries(Object.entries(value).map(([key, text]) => [key,
    freeText && /value|text/i.test(key) ? "[REDACTED]" : safeOption(text)]));
}

function productFields(value) {
  if (Array.isArray(value)) return value.map(productFields);
  if (!value || typeof value !== "object") return value;
  return Object.fromEntries(Object.entries(value)
    .filter(([key]) => /product|sku|option|store/i.test(key))
    .map(([key, item]) => [key, /option/i.test(key) ? safeOption(item) : productFields(item)]));
}

function safeUrl(raw) {
  const observations = {html_escaped: typeof raw === "string" && /&amp;/i.test(raw)};
  if (typeof raw !== "string" || !raw) return {value: raw, observations};
  observations.bad_percent = /%(?![0-9a-f]{2})/i.test(raw);
  observations.control_or_space = /[\x00-\x20\x7f]/.test(raw);
  const decoded = raw.replace(/&amp;/gi, "&");
  try {
    const url = new URL(decoded);
    observations.scheme = url.protocol;
    if (!["http:", "https:"].includes(url.protocol) || url.username || url.password) {
      return {value: "[REDACTED-NON-WEB-URL]", observations};
    }
    const addressHost = require("net").isIP(url.hostname.replace(/^\[|\]$/g, "")) !== 0;
    observations.address_host_redacted = addressHost;
    const merchant = !addressHost && /(^|\.)(glamira\.[a-z.]+|ring-paare\.de)$/i.test(url.hostname);
    const redacted = [];
    const query = new URLSearchParams();
    const seen = new Map();
    for (const [key, value] of url.searchParams) {
      if (seen.has(key)) observations[seen.get(key) === value ? "repeated_equal_key" : "repeated_conflicting_key"] = true;
      seen.set(key, value);
      if (merchant && knownOptions.has(key.toLowerCase()) && !privateText(value)) query.append(key, value);
      else { query.append(key, "[REDACTED]"); redacted.push(key); }
    }
    observations.redacted_query_keys = [...new Set(redacted)];
    const path = merchant ? url.pathname.replace(/\/(token|key|session|sid|email)\/[^/]+/gi, "/$1/[REDACTED]") : "/[REDACTED-EXTERNAL-PATH]";
    return {value: url.protocol + "//" + (addressHost ? "redacted-address.invalid" : url.host) + path + (query.size ? "?" + query.toString() : ""), observations};
  } catch (_) {
    observations.parse_failed = true;
    return {value: "[REDACTED-MALFORMED-URL]", observations};
  }
}

function redact(document) {
  const result = { _id: String(document._id), collection: document.collection,
    _research: {root_types: document.root_types, nonempty_link_fields: document.link_presence} };
  Object.assign(result, productFields(document.product_fields));
  for (const key of ["current_url", "referrer_url"]) {
    if (Object.hasOwn(document, key)) {
      const safe = safeUrl(document[key]);
      result[key] = safe.value;
      result._research[key] = safe.observations;
    }
  }
  return result;
}

const info = database.getCollectionInfos({name: collection.getName()})[0];
console.error("Research: metadata ready");
print(JSON.stringify({_metadata: {
  captured_at: new Date().toISOString(), namespace: collection.getFullName(),
  collection_uuid: info.info.uuid.toString(), server_version: mongo.getDB("admin").version(),
  estimated_documents: collection.estimatedDocumentCount(),
  indexes: collection.getIndexes().map(index => ({name: index.name, key: index.key})),
  method: targetIds.length ? "indexed _id point verification; redact before SSH output" : "$sample first, no seed; redact before SSH output", requested_sample_size: sampleSize,
}}));

// Sampling comes first so MongoDB can use its random cursor. No event filter,
// sort, distinct, index creation, $out, or $merge is issued by this script.
const cursor = collection.aggregate([
  targetIds.length ? {$match: {_id: {$in: targetIds.map(id => ObjectId(id))}}} : {$sample: {size: sampleSize}},
  {$project: {
    collection: 1, current_url: 1, referrer_url: 1,
    product_fields: {$arrayToObject: {$filter: {
      input: {$objectToArray: "$$ROOT"}, as: "field",
      cond: {$regexMatch: {input: "$$field.k", regex: "product|sku|option|store", options: "i"}},
    }}},
    root_types: {$map: {input: {$objectToArray: "$$ROOT"}, as: "field",
      in: {key: "$$field.k", bson_type: {$type: "$$field.v"}}}},
    link_presence: {
      device_id: {$and: [{$eq: [{$type: "$device_id"}, "string"]}, {$ne: ["$device_id", ""]}]},
      user_id_db: {$and: [{$eq: [{$type: "$user_id_db"}, "string"]}, {$ne: ["$user_id_db", ""]}]},
      session_id: {$and: [{$eq: [{$type: "$session_id"}, "string"]}, {$ne: ["$session_id", ""]}]},
    },
  }},
], {maxTimeMS: 600000}).batchSize(1000);
let emitted = 0;
console.error("Research: streaming bounded sample");
while (cursor.hasNext()) { print(JSON.stringify(redact(cursor.next()))); emitted++; }
print(JSON.stringify({_completed: {emitted}}));
console.error("Research: sample completed (" + emitted + " events)");
