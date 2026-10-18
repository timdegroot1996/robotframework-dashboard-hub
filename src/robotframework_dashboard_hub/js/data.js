// the hub payload written by generator.py: {title, generated, version, sources: [{label, status, runs, ...}]}
const hub = { title: "", generated: "", version: "", sources: [] };

// the payload is zlib compressed JSON, inflated with the native DecompressionStream like robotdashboard's data.js
async function load_hub_data() {
    const base64Str = "placeholder_hub_data";
    if (base64Str.includes("placeholder_")) return hub;
    const binaryStr = atob(base64Str);
    const compressedData = new Uint8Array(binaryStr.length);
    for (let i = 0; i < binaryStr.length; i++) {
        compressedData[i] = binaryStr.charCodeAt(i);
    }
    const stream = new Blob([compressedData]).stream().pipeThrough(new DecompressionStream("deflate"));
    Object.assign(hub, await new Response(stream).json());
    return hub;
}

export {
    hub,
    load_hub_data,
};
