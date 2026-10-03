import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { sha256Hex, stable, verifyIssuerMac } from "./crypto.ts";

const URL = Deno.env.get("SUPABASE_URL") ?? "";
const SERVICE = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? "";
const CLAIM_KEY = Deno.env.get("EXECUTION_ADMISSION_CLAIM_SECRET") ?? "";
const VERIFY_KEY = Deno.env.get("AH_EXECUTION_ADMISSION_VERIFY_KEY_V2") ?? "";
const TABLE = "execution_admission_nonces_v2";
const MAX_TTL_MS = 900_000;
const SKEW_MS = 60_000;
const enc = new TextEncoder();

const json = (body: unknown, status=200) => new Response(JSON.stringify(body), {
  status, headers: {"content-type":"application/json","cache-control":"no-store"}
});

async function digestBytes(text: string) {
  return new Uint8Array(await crypto.subtle.digest("SHA-256", enc.encode(text)));
}

async function secretEqual(a: string, b: string) {
  if (!a || !b) return false;
  const [ah,bh] = await Promise.all([digestBytes(a), digestBytes(b)]);
  if (ah.length !== bh.length) return false;
  let diff = 0;
  for (let i=0; i<ah.length; i++) diff |= ah[i] ^ bh[i];
  return diff === 0;
}

async function rest(path: string, init: RequestInit={}) {
  if (!URL || !SERVICE) throw new Error("SUPABASE_SERVER_CONFIG_REQUIRED");
  return fetch(`${URL}/rest/v1/${path}`, {
    ...init,
    headers: {
      "apikey": SERVICE,
      "authorization": `Bearer ${SERVICE}`,
      "content-type":"application/json",
      ...(init.headers ?? {}),
    }
  });
}

function validateAdmission(a: Record<string,any>, nowMs: number) {
  if (!Number.isFinite(nowMs)) return "ADMISSION_CLOCK_INVALID";
  const required=["gateway_version","control_plane_version","surface","operation","role","task_id",
    "issued_at","expires_at","nonce","evidence_digest","issuer_id"];
  for (const f of required) if (!a?.[f]) return `ADMISSION_FIELD_REQUIRED:${f}`;
  if (a.gateway_version !== "ROLE_EXECUTION_GATEWAY_V1") return "ADMISSION_GATEWAY_VERSION_MISMATCH";
  if (a.control_plane_version !== "EXECUTION_CONTROL_PLANE_V2") return "ADMISSION_CONTROL_PLANE_VERSION_MISMATCH";
  if (a.surface !== "KAGGLE" || a.operation !== "R020_FRAMEPACK_EXECUTION") return "V2_SURFACE_POLICY_NOT_ADMITTED";
  if (typeof a.nonce !== "string" || a.nonce.length < 32) return "ADMISSION_NONCE_ENTROPY_FAILURE";
  const issued=Date.parse(a.issued_at), expires=Date.parse(a.expires_at);
  if (!Number.isFinite(issued) || !Number.isFinite(expires)) return "ADMISSION_TIMESTAMP_INVALID";
  if (expires <= issued) return "ADMISSION_EXPIRY_ORDER_FAILURE";
  if (expires-issued > MAX_TTL_MS) return "ADMISSION_TTL_POLICY_FAILURE";
  if (nowMs < issued-SKEW_MS) return "ADMISSION_NOT_YET_VALID";
  if (nowMs > expires+SKEW_MS) return "ADMISSION_EXPIRED";
  return null;
}

Deno.serve(async (req: Request) => {
  const request_id = crypto.randomUUID();
  try {
    if (!CLAIM_KEY) return json({state:"DENIED",decision:"CLAIM_SECRET_NOT_CONFIGURED",request_id},503);
    if (!await secretEqual(req.headers.get("x-execution-admission-key") ?? "", CLAIM_KEY)) {
      return json({state:"DENIED",decision:"CLAIM_AUTH_FAILED",request_id},401);
    }
    if (req.method !== "POST") return json({state:"DENIED",decision:"POST_REQUIRED",request_id},405);
    const body = await req.json();
    if (body?.action === "read") {
      const aid=String(body.admission_id ?? ""), nonce=String(body.nonce ?? "");
      if (!aid || !nonce) return json({state:"DENIED",decision:"READ_IDENTITY_REQUIRED",request_id},400);
      const filter = encodeURIComponent(`(admission_id.eq.${aid},nonce.eq.${nonce})`);
      const r=await rest(`${TABLE}?or=${filter}&select=nonce,admission_id,surface,operation,role_name,task_id,claim_state,claimed_at,claim_writer,request_id,receipt&limit=1`);
      if (!r.ok) return json({state:"UNKNOWN_STATE",decision:"READBACK_PROVIDER_ERROR",request_id,http_status:r.status},503);
      const rows=await r.json();
      return json(rows?.[0] ? {state:"FOUND",request_id,row:rows[0]} : {state:"NOT_FOUND",request_id});
    }
    if (body?.action !== "claim") return json({state:"DENIED",decision:"UNKNOWN_ACTION",request_id},400);

    const admission_id=String(body.admission_id ?? "");
    const issuer_mac=String(body.issuer_mac ?? "");
    const a=body.admission as Record<string,any>;
    if (!admission_id || !issuer_mac || !a) return json({state:"DENIED",decision:"ADMISSION_TOKEN_REQUIRED",request_id},400);
    const integrity=await sha256Hex(stable(a));
    if (integrity !== admission_id) return json({state:"DENIED",decision:"ADMISSION_INTEGRITY_FAILURE",request_id},400);
    if (!VERIFY_KEY || VERIFY_KEY.length < 32) {
      return json({state:"DENIED",decision:"VERIFIER_KEY_NOT_CONFIGURED",request_id},503);
    }
    if (!await verifyIssuerMac({admission_id,admission:a}, issuer_mac, VERIFY_KEY)) {
      return json({state:"DENIED",decision:"ISSUER_AUTHENTICATION_FAILURE",request_id},401);
    }
    const invalid=validateAdmission(a,Date.now());
    if (invalid) return json({state:"DENIED",decision:invalid,request_id},400);

    const row={
      nonce:a.nonce, admission_id, surface:a.surface, operation:a.operation, role_name:a.role,
      task_id:a.task_id, issued_at:a.issued_at, expires_at:a.expires_at,
      claim_state:"CLAIMED", claim_writer:String(req.headers.get("x-execution-claim-writer") ?? "KAGGLE_RUNTIME"),
      request_id, receipt:{issuer_id:a.issuer_id,evidence_digest:a.evidence_digest}
    };
    const r=await rest(TABLE,{
      method:"POST",
      headers:{"prefer":"return=representation"},
      body:JSON.stringify(row),
    });
    if (r.ok) {
      const rows=await r.json();
      return json({state:"CLAIMED",request_id,admission_id,nonce:a.nonce,row:rows?.[0] ?? row});
    }
    const err=await r.json().catch(()=>({}));
    if (r.status===409 || err?.code==="23505") {
      return json({state:"REPLAY_DENIED",decision:"NONCE_OR_ADMISSION_ALREADY_CLAIMED",request_id,admission_id,nonce:a.nonce},409);
    }
    return json({state:"UNKNOWN_STATE",decision:"CLAIM_PROVIDER_ERROR",request_id,http_status:r.status,provider_code:err?.code ?? null},503);
  } catch (error) {
    return json({state:"UNKNOWN_STATE",decision:"CLAIM_EXCEPTION",request_id,error:String(error?.message ?? error)},503);
  }
});
