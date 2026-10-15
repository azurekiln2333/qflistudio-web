import { FlutterEngine, MethodChannel, MethodCall, MethodResult } from '@ohos/flutter_ohos';
import { BusinessError } from '@kit.BasicServicesKit';
import { version, start, poll, stop, release } from 'libqfli_nginx_napi.so';

// Mirrors ios/Runner/EmbeddedNginxBridge.swift: the Dart host
// (lib/services/nginx_host.dart EmbeddedNginxHost) owns the lifecycle ordering
// and this bridge only forwards the four lifecycle calls plus the version.
//
// Failure mapping follows the shared contract: malformed payloads are
// INVALID_ARGUMENT, a negative start is NGINX_START, and any other negative
// lifecycle status is NGINX_SESSION.
function tokenArgument(call: MethodCall): number {
  const token = call.argument('token') as number;
  if (typeof token !== 'number' || !Number.isInteger(token) || token <= 0) {
    throw new Error('INVALID_ARGUMENT');
  }
  return token;
}

let activeToken: number = 0;

// Mirrors EmbeddedNginxBridge.swift deinit: stop the worker, then poll until it
// reaches completion and release it. Without the release the native
// qfli_active token stays busy, so a later start() in the same process would
// return -EBUSY. ArkTS has no blocking sleep, so a bounded setTimeout loop is
// used; the 5 s budget matches the Dart-side stop timeout.
function stopAndRelease(token: number, remaining: number): void {
  if (token <= 0) return;
  try {
    stop({ token: token });
  } catch (_) {
    // The engine is going away; nothing to report.
  }
  const tick = (attempts: number): void => {
    if (attempts <= 0) return;
    try {
      const status = poll({ token: token });
      if (status === null) {
        setTimeout(() => tick(attempts - 1), 50);
        return;
      }
      release({ token: token });
    } catch (_) {
      // An invalid or already-collected token needs no further work.
    }
  };
  tick(remaining);
}

// Called from EntryAbility.onDestroy: replacing/destroying the ability disposes
// the channel before Dart necessarily releases its token.
export function stopActiveNginx(): void {
  const token = activeToken;
  activeToken = 0;
  stopAndRelease(token, 100);
}

export function configureNginxChannel(engine: FlutterEngine): void {
  const channel = new MethodChannel(
    engine.dartExecutor.getBinaryMessenger(),
    'qflistudio/nginx',
  );
  channel.setMethodCallHandler({
    onMethodCall(call: MethodCall, result: MethodResult): void {
      if (call.method === 'version') {
        result.success(version());
        return;
      }
      if (call.method === 'start') {
        const prefix = call.argument('prefix') as string;
        const test = call.argument('test') as boolean;
        if (typeof prefix !== 'string' || prefix.length === 0 || prefix.includes('\u0000')) {
          result.error('INVALID_ARGUMENT', 'Invalid Nginx start arguments', null);
          return;
        }
        try {
          const token = start({ prefix: prefix, test: test === true });
          if (token < 0) {
            result.error('NGINX_START', 'Native Nginx start failed', token);
            return;
          }
          activeToken = token;
          result.success(token);
        } catch (error) {
          result.error('NGINX_START', (error as BusinessError).message, null);
        }
        return;
      }
      if (call.method === 'poll' || call.method === 'stop' || call.method === 'release') {
        let token: number;
        try {
          token = tokenArgument(call);
        } catch (_) {
          result.error('INVALID_ARGUMENT', 'Invalid Nginx token', null);
          return;
        }
        try {
          if (call.method === 'poll') {
            result.success(poll({ token: token }));
          } else if (call.method === 'stop') {
            stop({ token: token });
            result.success(null);
          } else {
            release({ token: token });
            if (activeToken === token) activeToken = 0;
            result.success(null);
          }
        } catch (error) {
          result.error('NGINX_SESSION', (error as BusinessError).message, null);
        }
        return;
      }
      result.notImplemented();
    },
  });
}
