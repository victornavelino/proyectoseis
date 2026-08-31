// RFC 7636 (PKCE): code_verifier aleatorio + code_challenge = base64url(sha256(code_verifier)).
// Usa la Web Crypto API del navegador (crypto.subtle), disponible en contextos seguros
// (https:// o localhost) — no depende de ninguna librería externa.

function base64UrlEncode(bytes: ArrayBuffer): string {
  const binary = String.fromCharCode(...new Uint8Array(bytes))
  return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '')
}

function randomUrlSafeString(byteLength: number): string {
  const array = new Uint8Array(byteLength)
  crypto.getRandomValues(array)
  return base64UrlEncode(array.buffer)
}

export async function generarParPkce(): Promise<{ codeVerifier: string; codeChallenge: string }> {
  // 64 bytes aleatorios en base64url ≈ 86 caracteres, dentro del rango 43-128 que exige el RFC.
  const codeVerifier = randomUrlSafeString(64)
  const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(codeVerifier))
  const codeChallenge = base64UrlEncode(digest)
  return { codeVerifier, codeChallenge }
}

export function generarState(): string {
  return randomUrlSafeString(16)
}
