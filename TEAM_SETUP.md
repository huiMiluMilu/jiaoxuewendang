# 教学文档 Skill 同事使用说明

这份说明是给团队同事看的，目标是让大家能独立使用 `video-teaching-doc-skill` 产出教学文档。

## 一、先说结论

如果同事只想做到“输入视频链接，产出一版 Markdown 教学文档”，最低只需要准备：

1. `Codex` 可用
2. `Chrome` 可用
3. `Python 3`
4. 安装好这个 skill

如果同事还想做到“自动发布到飞书”，再额外准备：

1. `lark-cli`
2. 飞书登录授权

如果同事还想做到“更精细的截图、OCR、红框标注”，再额外准备：

1. `macOS`
2. `Swift`
3. 允许 Chrome 被脚本控制

## 二、推荐的使用分层

为了降低同事上手难度，建议把使用方式分成 3 档。

### 档位 A：文档草稿版

适合先验证内容方向。

产出：

1. 转写整理稿
2. 教学文档 Markdown 草稿
3. 少量关键截图

需要准备：

1. `Codex`
2. `Chrome`
3. `Python 3`
4. Python 包：
   `Pillow`
   `numpy`
   `faster-whisper`
   `imageio-ffmpeg`

### 档位 B：飞书发布版

适合交给运营、教研、老师直接查看。

在档位 A 的基础上，再增加：

1. `lark-cli`
2. 飞书账号登录
3. 飞书文档创建权限

### 档位 C：精细截图/红框版

适合做更接近正式教程的版本。

在档位 B 的基础上，再增加：

1. `macOS`
2. `Swift`
3. Chrome 远程调试和 Apple 事件控制权限

## 三、同事必须安装什么

### 1. Codex

需要能正常使用 Codex，并且能在本机发现 skill。

推荐做法：

1. 把 skill 放在：
   `~/.codex/skills/video-teaching-doc-skill`
2. 最好用软链接指向项目目录，方便后续统一更新

当前 skill 源目录是：

- [/Users/shihui/Desktop/玩玩编程/生产教学文档/video-teaching-doc-skill](/Users/shihui/Desktop/玩玩编程/生产教学文档/video-teaching-doc-skill)

### 2. Python 3

当前环境验证过可用版本：

1. `Python 3.14.3`

建议同事至少准备：

1. `Python 3.11+`

### 3. Python 包

当前脚本实际依赖这些包：

1. `Pillow`
2. `numpy`
3. `faster-whisper`
4. `imageio-ffmpeg`

推荐安装命令：

```bash
python3 -m pip install pillow numpy faster-whisper imageio-ffmpeg
```

### 4. Chrome

需要本机安装 `Google Chrome`，因为现在这套流程里：

1. 有些课程回放必须依赖已登录浏览器会话
2. 有些视频链接需要真实播放器页面才能拿到媒体源
3. 精细截图版需要从浏览器里的 `video` 直接抓帧

### 5. lark-cli

如果要发布飞书文档，需要安装 `lark-cli`。

当前机器路径示例：

1. `/Users/shihui/.npm-global/bin/lark-cli`

同事不发飞书的话，这一项不是必须。

### 6. Swift

如果要做 OCR 和更细的控件识别，需要 `Swift`。

当前机器验证过：

1. `Swift 6.2.4`

这是因为当前 OCR 脚本依赖：

- [vision_ocr.swift](/Users/shihui/Desktop/玩玩编程/生产教学文档/scripts/vision_ocr.swift)

## 四、同事第一次使用前要完成什么登录

### 1. Chrome 登录课程平台

如果课程回放页是需要登录态的，同事必须先在 `Chrome` 里登录对应平台。

例如：

1. 打开课程回放链接
2. 确保能在浏览器里正常播放
3. 再让 Codex 开始跑流程

否则常见问题是：

1. 页面能打开，但拿不到真实视频流
2. 接口返回 `token 为 null`
3. 只能看到加载页，不能真正抽帧

### 2. 飞书登录

如果要发布飞书文档，同事需要先完成 `lark-cli` 登录授权。

至少要保证：

1. 能创建云文档
2. 能往云文档插入图片

### 3. GitHub / Vercel / 其他第三方账号

这类账号通常不是“跑 skill 必需”，而是课程视频本身内容的一部分。  
也就是说：

1. 如果视频里讲的是 `GitHub` 或 `Vercel`
2. skill 只需要能看视频，不一定要同事自己登录这些平台

除非要做“边看边真实复现”的高级版本，否则不要求同事本机也登录这些业务网站。

## 五、macOS 上要额外打开哪些权限

如果同事要跑“浏览器抓帧版”或“精细截图版”，需要额外开这几个能力。

### 1. Chrome 允许被 AppleScript 执行 JavaScript

需要在 Chrome 菜单中打开：

1. `查看 -> 开发者 -> 允许 Apple 事件中的 JavaScript`

没有这一项时，当前这些脚本就不能稳定读取浏览器中的 `video`：

- [browser_video_capture.py](/Users/shihui/Desktop/玩玩编程/生产教学文档/scripts/browser_video_capture.py)
- [browser_media_recorder.py](/Users/shihui/Desktop/玩玩编程/生产教学文档/scripts/browser_media_recorder.py)

### 2. Chrome 远程调试

如果课程平台特别依赖真实浏览器态，建议同事打开：

1. `chrome://inspect/#remote-debugging`
2. 允许当前浏览器实例远程调试

### 3. 系统自动化权限

macOS 可能会弹出权限请求：

1. 允许终端/应用控制 `Google Chrome`

这类权限需要点允许，否则抓帧脚本跑不起来。

## 六、同事需要知道的目录结构

建议同事统一使用这个结构：

1. `video-teaching-doc-skill/`
   skill 本体
2. `scripts/`
   处理脚本
3. `simple-demo/<视频代号>/`
   每个视频的一次产出目录
4. `simple-demo/<视频代号>/work/`
   中间文件目录

这样同事比较容易理解：

1. 哪些是脚本
2. 哪些是最终文档
3. 哪些只是中间产物

## 七、同事实际会用到哪些脚本

### 必用脚本

- [publish_teaching_doc_to_lark.py](/Users/shihui/Desktop/玩玩编程/生产教学文档/scripts/publish_teaching_doc_to_lark.py)
  用于把 Markdown 和本地图片发布到飞书

- [inject_step_timestamps.py](/Users/shihui/Desktop/玩玩编程/生产教学文档/scripts/inject_step_timestamps.py)
  用于给步骤加 `【视频回放时点xx：xx：xx】`

### 常用脚本

- [browser_video_capture.py](/Users/shihui/Desktop/玩玩编程/生产教学文档/scripts/browser_video_capture.py)
  从浏览器中的视频抓单帧

- [browser_media_recorder.py](/Users/shihui/Desktop/玩玩编程/生产教学文档/scripts/browser_media_recorder.py)
  从浏览器直接录音频

### 精细版才常用

- [refine_doc_step_boxes.py](/Users/shihui/Desktop/玩玩编程/生产教学文档/scripts/refine_doc_step_boxes.py)
  重画红框

- [vision_ocr.swift](/Users/shihui/Desktop/玩玩编程/生产教学文档/scripts/vision_ocr.swift)
  OCR 识别控件文字

- [video_action_candidates.py](/Users/shihui/Desktop/玩玩编程/生产教学文档/scripts/video_action_candidates.py)
  基于转写和动作词切步骤

- [video_dense_events.py](/Users/shihui/Desktop/玩玩编程/生产教学文档/scripts/video_dense_events.py)
  从连续帧中筛页面变化和操作事件

## 八、同事最小可用流程

如果一个同事第一次跑，建议只照这个最小流程走：

1. 在 Chrome 里打开课程回放链接，并确认能播放
2. 确认 skill 已安装到 `~/.codex/skills`
3. 确认 Python 依赖已装好
4. 让 Codex 先产出：
   转写整理稿
   教学文档 Markdown 草稿
5. 确认文案主线没问题后，再补截图
6. 最后再决定要不要发布飞书

这样能避免一上来就卡在：

1. 飞书权限
2. 红框精度
3. 浏览器抓帧
4. 页面登录态

## 九、常见问题

### 1. 为什么页面打开了，但还是拿不到视频

通常是因为：

1. 回放需要登录态
2. 只是打开了短链接，没有真正进入播放页
3. 浏览器没有权限给脚本读取 `video`

### 2. 为什么能发飞书文字，但图片上传失败

通常是因为：

1. 直接在 Markdown 里用了本地路径
2. 没有走 `docs +media-insert`
3. `lark-cli` 授权不完整

### 3. 为什么红框不准

因为红框不是简单找变化区域，而是要先确定“这一步真正操作的控件”。  
如果只做文档草稿版，可以先不做红框。

### 4. 为什么同事跑起来比你这里慢

常见原因是：

1. `faster-whisper` 首次加载模型较慢
2. 浏览器登录态不完整
3. 视频平台鉴权链路不同
4. 飞书图片上传本身有一定耗时

## 十、最推荐的团队落地方式

如果你希望同事长期用，最推荐的是这两步：

1. 先统一一份“团队标准环境”
   包括：
   Codex
   Chrome
   Python 包
   lark-cli
   skill 安装路径
2. 再统一一个“调用入口”
   例如：
   给 Codex 一个固定 prompt
   或者接飞书机器人命令

这样同事不需要理解全部脚本，只需要会发起任务即可。

## 十一、建议你给同事的标准 prompt

可以直接让同事这样说：

```text
用 $video-teaching-doc-skill 根据这个课程回放链接生成教学文档。
先转写，再按老师讲解顺序整理成详细操作步骤，
每一步前加【视频回放时点xx：xx：xx】，
再补关键截图。
如果可以，最后发布到飞书云文档。
```

## 十二、当前结论

如果只是让同事先能用起来，最小准备其实不复杂：

1. 装好 skill
2. 装好 Python 依赖
3. Chrome 里能打开课程回放
4. 要发飞书时再补 `lark-cli`

真正复杂的是“精细截图、红框、页面登录态”，这些完全可以放到第二阶段再统一。
