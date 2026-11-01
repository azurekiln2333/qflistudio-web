/** Validate the original preview URL without DNS, endpoint lookup or rewriting. */
export function isOfflinePreviewUrl(input: string): boolean {
  // A channel type assertion does not validate its runtime value. Reject raw
  // whitespace, C0/C1 controls and backslashes before matching the authority.
  if (typeof input !== 'string' || /[\\\s\u0000-\u001F\u007F-\u009F]/.test(input)) {
    return false;
  }
  // Only canonical literal loopbacks and an explicit decimal port are accepted.
  // A path/query/fragment may follow; none can become part of the authority.
  const match = /^https?:\/\/(?:127\.0\.0\.1|\[::1\]):([1-9][0-9]{0,4})(?:[/?#].*)?$/i.exec(input);
  if (match === null) {
    return false;
  }
  const port = Number(match[1]);
  return port >= 1 && port <= 65535;
}
