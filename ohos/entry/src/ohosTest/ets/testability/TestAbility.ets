import UIAbility from '@ohos.app.ability.UIAbility';
import Want from '@ohos.app.ability.Want';
import window from '@ohos.window';
import deviceInfo from '@ohos.deviceInfo';
import { webview } from '@kit.ArkWeb';
import hilog from '@ohos.hilog';
import { BusinessError } from '@ohos.base';

// Compiled only into the ohosTest feature HAP. Production EntryAbility and
// ArkUI pages never import this ability or enable Web debugging.
export default class TestAbility extends UIAbility {
  private debugging: boolean = false;
  private tcpPort: number = 0;
  private stopping: boolean = false;

  onCreate(want: Want): void {
    if (this.stopRequested(want)) return;
    try {
      const mode = want.parameters?.['qfliCatalogCdp'];
      if (mode !== 'tcp' && mode !== 'unix') {
        hilog.info(0x0000, 'QfliCatalog', 'CDP disabled; opt in with qfliCatalogCdp=tcp or unix');
        return;
      }
      if (mode === 'tcp') {
        const requestedPort = want.parameters?.['qfliCatalogPort'];
        const port = typeof requestedPort === 'number' ? requestedPort : 9222;
        if (deviceInfo.sdkApiVersion < 20 || !Number.isInteger(port) || port <= 1024 || port > 65535) {
          throw new Error('TCP ArkWeb debugging requires API20+ and port1025..65535; use unix mode on API9..19');
        }
        webview.WebviewController.setWebDebuggingAccess(true, port);
        this.tcpPort = port;
      } else {
        webview.WebviewController.setWebDebuggingAccess(true);
      }
      this.debugging = true;
      hilog.info(0x0000, 'QfliCatalog', 'Test-only CDP enabled (%{public}s)', mode);
    } catch (failure) {
      this.disableDebugging();
      throw new Error(`Test-only CDP initialization failed: ${failure}`);
    }
  }

  onNewWant(want: Want): void {
    this.stopRequested(want);
  }

  onWindowStageCreate(windowStage: window.WindowStage): void {
    if (this.stopping) return;
    try {
      windowStage.loadContent('testability/pages/Index', (failure: BusinessError) => {
        if (failure.code) {
          this.disableDebugging();
          hilog.error(0x0000, 'QfliCatalog', 'Catalog page failed: %{public}s', `${failure.message}`);
        }
      });
    } catch (failure) {
      this.disableDebugging();
      throw new Error(`Test-only catalog window failed: ${failure}`);
    }
  }

  onWindowStageDestroy(): void {
    this.disableDebugging();
  }

  onDestroy(): void {
    this.disableDebugging();
  }

  private stopRequested(want: Want): boolean {
    if (want.parameters?.['qfliCatalogStop'] !== true) return false;
    this.stopping = true;
    this.disableDebugging();
    this.context.terminateSelf().catch((failure: BusinessError) => {
      hilog.error(0x0000, 'QfliCatalog', 'Test ability termination failed: %{public}s', failure.message);
    });
    return true;
  }

  private disableDebugging(): void {
    try {
      if (!this.debugging) return;
      if (this.tcpPort > 0) {
        webview.WebviewController.setWebDebuggingAccess(false, this.tcpPort);
      } else {
        webview.WebviewController.setWebDebuggingAccess(false);
      }
      this.debugging = false;
      this.tcpPort = 0;
    } catch (failure) {
      hilog.error(0x0000, 'QfliCatalog', 'CDP teardown failed: %{public}s', `${failure}`);
    }
  }
}
