
import {
  FlutterAbility,
  FlutterEngine,
  MethodChannel,
  MethodCall,
  MethodResult,
} from '@ohos/flutter_ohos';
import { systemShare } from '@kit.ShareKit';
import { common, Want, ConfigurationConstant } from '@kit.AbilityKit';
import { window } from '@kit.ArkUI';
import { BusinessError } from '@kit.BasicServicesKit';
import { GeneratedPluginRegistrant } from '../plugins/GeneratedPluginRegistrant';
import { handlePickerCall, isPickerMethod } from './PickerBridge';
import { configureNginxChannel, stopActiveNginx } from './NginxBridge';

const CHANNEL_PLATFORM = 'qflistudio/platform';

export default class EntryAbility extends FlutterAbility {
  onWindowStageCreate(windowStage: window.WindowStage): void {
    // 启动遮罩消失后、Flutter 首帧渲染前，引擎初始化期间窗口会露出
    // 默认白底。窗口底色与 Flutter 的 MD3 surface 保持一致。
    try {
      const isDark = this.context.config?.colorMode ===
        ConfigurationConstant.ColorMode.COLOR_MODE_DARK;
      windowStage.getMainWindowSync().setWindowBackgroundColor(
        isDark ? '#FF111418' : '#FFF8F9FF',
      );
    } catch (e) {
      // 设置失败不影响启动（仅深色模式可能出现短暂白闪）。
    }
    super.onWindowStageCreate(windowStage);
  }

  configureFlutterEngine(flutterEngine: FlutterEngine) {
    super.configureFlutterEngine(flutterEngine)
    GeneratedPluginRegistrant.registerWith(flutterEngine)
    // Native Nginx runs in-process through the embedded lifecycle ABI on
    // HarmonyOS; the standalone executableBinaryPaths form is rejected by
    // bm install on HarmonyOS 7.0.
    configureNginxChannel(flutterEngine)

    const abilityContext = this.context as common.UIAbilityContext;

    // 通用平台能力：打开系统浏览器（HTML 预览用）。
    const platformChannel = new MethodChannel(
      flutterEngine.dartExecutor.getBinaryMessenger(),
      CHANNEL_PLATFORM,
    );
    platformChannel.setMethodCallHandler({
      onMethodCall(call: MethodCall, result: MethodResult): void {
        if (call.method === 'openUrl') {
          const url = call.argument('url') as string;
          const want: Want = {
            action: 'ohos.want.action.viewData',
            uri: url,
          };
          abilityContext.startAbility(want)
            .then(() => {
              result.success(null);
            })
            .catch((err: BusinessError) => {
              result.error(`${err.code}`, `${err.message}`, null);
            });
        } else if (call.method === 'shareText') {
          // 系统分享面板（Share Kit）：纯文本分享。
          const title = call.argument('title') as string;
          const text = call.argument('text') as string;
          const record: systemShare.SharedRecord = {
            utd: 'general.plain-text',
            content: text,
            title: title,
          };
          const data = new systemShare.SharedData(record);
          const controller = new systemShare.ShareController(data);
          const options: systemShare.ShareControllerOptions = {};
          controller.show(abilityContext, options)
            .then(() => {
              result.success(null);
            })
            .catch((err: BusinessError) => {
              result.error('SHARE_FAILED', `${err.code}: ${err.message}`, null);
            });
        } else if (isPickerMethod(call.method)) {
          handlePickerCall(abilityContext, call, result);
        } else {
          result.notImplemented();
        }
      },
    });

  }

  onDestroy(): void {
    // The embedded Nginx worker owns a pthread; stop the active session before
    // the ability (and its engine) is torn down. Dart's own stop/release path
    // still handles the normal case.
    stopActiveNginx();
    super.onDestroy();
  }
}
