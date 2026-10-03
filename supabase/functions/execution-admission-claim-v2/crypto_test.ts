import { hmacHex, sha256Hex, stable, verifyIssuerMac } from "./crypto.ts";

const KEY = "0123456789abcdef0123456789abcdef";
const admission = {
  gateway_version:"ROLE_EXECUTION_GATEWAY_V1",
  control_plane_version:"EXECUTION_CONTROL_PLANE_V2",
  surface:"KAGGLE",
  operation:"R020_FRAMEPACK_EXECUTION",
  role:"BIG_TECH_TECH_RND",
  task_id:"AH_EXECUTION_ADMISSION_REPLAY_HARDENING_20260926",
  issued_at:"2026-10-03T12:55:00.000Z",
  expires_at:"2026-10-03T13:10:00.000Z",
  nonce:"00112233445566778899aabbccddeeff",
  evidence_digest:"evidence",
  issuer_id:"TEST_ISSUER",
};

function assert(condition: unknown, message: string) {
  if (!condition) throw new Error(message);
}

Deno.test("recursive canonicalization is deterministic and nested-sensitive", async () => {
  assert(stable({b:2,a:{y:2,x:1}}) === stable({a:{x:1,y:2},b:2}), "canonical order mismatch");
  const a=await sha256Hex(stable({evidence:{nested:{x:1,y:2}}}));
  const b=await sha256Hex(stable({evidence:{nested:{x:1,y:3}}}));
  assert(a !== b, "nested evidence collision");
});

Deno.test("valid issuer MAC verifies", async () => {
  const admission_id=await sha256Hex(stable(admission));
  const value={admission_id,admission};
  const mac=await hmacHex(value,KEY);
  assert(await verifyIssuerMac(value,mac,KEY), "valid MAC rejected");
});

Deno.test("fresh forged payload with recomputed public digest but stale MAC is denied", async () => {
  const originalId=await sha256Hex(stable(admission));
  const original={admission_id:originalId,admission};
  const mac=await hmacHex(original,KEY);
  const forged={...admission,nonce:"ffeeddccbbaa99887766554433221100"};
  const forgedId=await sha256Hex(stable(forged));
  assert(!(await verifyIssuerMac({admission_id:forgedId,admission:forged},mac,KEY)), "forged MAC accepted");
});

Deno.test("missing or malformed issuer MAC fails closed", async () => {
  const admission_id=await sha256Hex(stable(admission));
  const value={admission_id,admission};
  assert(!(await verifyIssuerMac(value,"",KEY)), "empty MAC accepted");
  assert(!(await verifyIssuerMac(value,"00",KEY)), "malformed MAC accepted");
  assert(!(await verifyIssuerMac(value,await hmacHex(value,KEY),"short")), "short verifier key accepted");
});
