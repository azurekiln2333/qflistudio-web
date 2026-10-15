export function version(): string;
export function start(options: { prefix: string; test: boolean }): number;
export function poll(options: { token: number }): number | null;
export function stop(options: { token: number }): void;
export function release(options: { token: number }): void;
