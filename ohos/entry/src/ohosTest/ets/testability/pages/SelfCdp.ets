import { webview } from '@kit.ArkWeb';
import hilog from '@ohos.hilog';
import { SelfCdpProof, SelfCdpReport } from '../SelfCdpProof';

// Opt-in test route only. TestAbility owns the application-wide one-argument
// debugging enable/disable lease. This page never changes that switch.
@Entry
@Component
struct SelfCdp {
  private controller: webview.WebviewController = new webview.WebviewController();
  private proof: SelfCdpProof | undefined = undefined;
  private alive: boolean = false;
  private started: boolean = false;
  private attached: boolean = false;
  private loadTimer: number = -1;
  @State bootstrapUrl: string = '';
  @State transcript: string = 'Test-owned self CDP proof: preparing static bootstrap';
  @State ready: boolean = false;

  aboutToAppear(): void {
    this.alive = true;
    this.started = false;
    try {
      this.proof = new SelfCdpProof();
      this.bootstrapUrl = this.proof.bootstrapUrl;
      this.ready = true;
      this.loadTimer = setTimeout(() => {
        this.loadTimer = -1;
        if (!this.alive || this.started) return;
        this.record({ stage: 'bootstrap', state: 'fail', detail: 'Static bootstrap did not finish within 10 seconds' });
        this.proof?.cancel();
        this.ready = false;
      }, 10000);
    } catch (failure) {
      this.record({ stage: 'prepare', state: 'fail', detail: `${failure}` });
    }
  }

  aboutToDisappear(): void {
    this.alive = false;
    if (this.loadTimer >= 0) clearTimeout(this.loadTimer);
    this.loadTimer = -1;
    this.proof?.cancel();
    this.proof = undefined;
    if (this.attached) {
      try {
        this.controller.stop();
      } catch (failure) {
        hilog.error(0x0000, 'QfliSelfCdp', 'Web stop after detach: %{public}s', `${failure}`.slice(0, 512));
      }
    }
    this.attached = false;
  }

  private record(report: SelfCdpReport): void {
    const line = `${report.stage}: ${report.state}: ${report.detail}`.slice(0, 640);
    if (report.state === 'fail') hilog.error(0x0000, 'QfliSelfCdp', '%{public}s', line);
    else hilog.info(0x0000, 'QfliSelfCdp', '%{public}s', line);
    if (this.alive) this.transcript = `${this.transcript}\n${line}`.slice(-8192);
  }

  private async begin(): Promise<void> {
    if (!this.alive || this.started || this.proof === undefined) return;
    if (this.loadTimer >= 0) clearTimeout(this.loadTimer);
    this.loadTimer = -1;
    this.started = true;
    const proof = this.proof;
    try {
      await proof.run((report: SelfCdpReport) => this.record(report));
    } catch (failure) {
      // run already emits the exact bounded failure stage, including native
      // errno/EOF/timeouts. The route never substitutes a host connection.
      hilog.error(0x0000, 'QfliSelfCdp', 'Proof ended: %{public}s', `${failure}`.slice(0, 512));
    }
  }

  build() {
    Column() {
      Text('QFLI test-owned same-app CDP proof').fontSize(18).padding(12)
      Scroll() {
        Text(this.transcript).fontSize(12).fontFamily('monospace').width('100%').padding(12)
      }.layoutWeight(1).width('100%')
      if (this.ready) {
        Web({ src: this.bootstrapUrl, controller: this.controller, incognitoMode: true })
          .width('100%')
          .height(100)
          .javaScriptAccess(true)
          .domStorageAccess(false)
          .fileAccess(false)
          .multiWindowAccess(false)
          .mixedMode(MixedMode.None)
          .onControllerAttached(() => {
            this.attached = true;
          })
          .onInterceptRequest((event: OnInterceptRequestEvent) => {
            const proof = this.proof;
            if (this.alive && proof !== undefined) {
              return proof.response(event.request.getRequestUrl(), event.request.getRequestMethod());
            }
            // null permits a real load. Keep a closed page fail-closed even
            // after its protocol owner and cancellation state are released.
            const denied = new WebResourceResponse();
            denied.setResponseCode(403);
            denied.setReasonMessage('Forbidden');
            denied.setResponseMimeType('text/plain');
            denied.setResponseEncoding('utf-8');
            denied.setResponseData('Test-owned page is closed');
            return denied;
          })
          .onLoadIntercept((event: OnLoadInterceptEvent) => {
            return !this.alive || event.data.getRequestUrl() !== this.bootstrapUrl;
          })
          .onOverrideUrlLoading((request: WebResourceRequest) => {
            return !this.alive || request.getRequestUrl() !== this.bootstrapUrl;
          })
          .onPageEnd((event: OnPageEndEvent) => {
            if (event.url === this.bootstrapUrl) this.begin();
          })
      }
    }.width('100%').height('100%')
  }
}
