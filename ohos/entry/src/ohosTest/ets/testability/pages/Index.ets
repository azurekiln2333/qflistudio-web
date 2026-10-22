import common from '@ohos.app.ability.common';
import { CatalogHarness, BOOTSTRAP_URL } from '../CatalogHarness';
import { webview } from '@kit.ArkWeb';

@Entry
@Component
struct Index {
  private controller: webview.WebviewController = new webview.WebviewController();
  private harness: CatalogHarness = new CatalogHarness();
  private alive: boolean = true;
  @State ready: boolean = false;
  @State error: string = '';

  aboutToAppear(): void {
    this.alive = true;
    this.prepare();
  }

  aboutToDisappear(): void {
    this.alive = false;
    if (this.ready) {
      try {
        this.controller.stop();
      } catch (failure) {
        // The component may already have detached. Ability teardown separately
        // disables the test-only debugger, and native Web destruction owns I/O.
        this.error = `Catalog view detached: ${failure}`;
      }
    }
  }

  private async prepare(): Promise<void> {
    try {
      await this.harness.prepare(getContext(this) as common.UIAbilityContext);
      if (this.alive) this.ready = true;
    } catch (failure) {
      if (this.alive) this.error = `${failure}`;
    }
  }

  build() {
    Column() {
      if (this.error.length > 0) {
        Text(`OHOS catalog preparation failed: ${this.error}`).padding(16)
      } else if (!this.ready) {
        Text('Reading and hashing packaged test catalogs…').padding(16)
      } else {
        Web({ src: BOOTSTRAP_URL, controller: this.controller, incognitoMode: true })
          .width('100%')
          .height('100%')
          .javaScriptAccess(true)
          .domStorageAccess(true)
          .mixedMode(MixedMode.None)
          .onInterceptRequest((event: OnInterceptRequestEvent) => {
            return this.harness.response(event.request.getRequestUrl(), event.request.getRequestMethod());
          })
      }
    }
    .width('100%')
    .height('100%')
  }
}
