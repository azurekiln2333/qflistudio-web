/** Raw self-only Unix transport. Does not enable ArkWeb or implement CDP. */
export interface OpenResult {
  /** 0 means a handle was allocated, possibly still connecting; otherwise -errno. */
  status: number;
  /** Positive int64 decimal string on success, empty string on failure. */
  handle: string;
}

export interface ReadResult {
  /** Positive byte count, 0 EOF, or negative errno (including EAGAIN). */
  status: number;
  /** Exactly status bytes when positive, otherwise an empty ArrayBuffer. */
  bytes: ArrayBuffer;
}

export function openSelf(): OpenResult;
/** capacity must be an integer in 1..65536. Stale/foreign handles return -EBADF. */
export function read(handle: string, capacity: number): ReadResult;
/** ArrayBuffer length must be 1..65536; returns actual accepted bytes or -errno. */
export function write(handle: string, bytes: ArrayBuffer): number;
/** Idempotent for a valid positive decimal handle; cannot close another environment's handle. */
export function close(handle: string): number;
