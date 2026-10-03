const enc = new TextEncoder();

export const canonical = (value: unknown): unknown => {
  if (Array.isArray(value)) return value.map(canonical);
  if (value && typeof value === "object") {
    const obj = value as Record<string, unknown>;
    return Object.fromEntries(Object.keys(obj).sort().map((k) => [k, canonical(obj[k])]));
  }
  return value;
};

export const stable = (value: unknown): string => JSON.stringify(canonical(value));

const bytesToHex = (bytes: Uint8Array): string =>
  [...bytes].map((b) => b.toString(16).padStart(2, "0")).join("");

const hexToBytes = (hex: string): Uint8Array | null => {
  if (!/^[0-9a-f]{64}$/i.test(hex)) return null;
  return new Uint8Array(hex.match(/../g)!.map((x) => Number.parseInt(x, 16)));
};

export async function sha256Hex(text: string): Promise<string> {
  const hash = new Uint8Array(await crypto.subtle.digest("SHA-256", enc.encode(text)));
  return bytesToHex(hash);
}

async function hmacKey(secret: string, usages: KeyUsage[]): Promise<CryptoKey> {
  return crypto.subtle.importKey(
    "raw",
    enc.encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    usages,
  );
}

export async function hmacHex(value: unknown, secret: string): Promise<string> {
  if (typeof secret !== "string" || secret.length < 32) throw new Error("HMAC_KEY_REQUIRED");
  const key = await hmacKey(secret, ["sign"]);
  const sig = new Uint8Array(await crypto.subtle.sign("HMAC", key, enc.encode(stable(value))));
  return bytesToHex(sig);
}

export async function verifyIssuerMac(
  value: unknown,
  issuerMacHex: string,
  secret: string,
): Promise<boolean> {
  if (typeof secret !== "string" || secret.length < 32) return false;
  const sig = hexToBytes(String(issuerMacHex || ""));
  if (!sig) return false;
  const key = await hmacKey(secret, ["verify"]);
  return crypto.subtle.verify("HMAC", key, sig, enc.encode(stable(value)));
}
