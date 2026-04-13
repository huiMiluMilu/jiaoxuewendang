# 教学文档 Skill 通用使用说明

这份说明是给团队同事和外部协作者看的。  
目标不是“只在 Codex 里能用”，而是把这个项目作为一个 **可打包、可复用、可交给任意 AI 编程工具调用的教学文档工作流**。

仓库地址：

- [https://github.com/huiMiluMilu/jiaoxuewendang](https://github.com/huiMiluMilu/jiaoxuewendang)

## 一、它到底是什么

这个仓库本质上包含 3 层内容：

1. `规则层`
   也就是 skill 本体，定义“怎么从视频生成教学文档”
2. `脚本层`
   负责抽音频、抽帧、加时间点、发飞书、OCR、红框等
3. `产出层`
   每次跑一个视频后，生成 Markdown、截图、转写稿、飞书结果

所以它不依赖某一个特定 AI 工具。  
只要一个 AI 工具具备下面 3 个能力，就能使用它：

1. 能读取本地文件
2. 能执行 shell 命令
3. 能编辑 Markdown 或脚本

## 二、支持哪些 AI 工具

理论上，任何能读仓库和跑命令的 AI 编程工具都可以用，包括但不限于：

1. Codex
2. Claude Code
3. Cursor
4. Cline / Roo Code
5. Windsurf
6. 其他支持本地仓库和终端执行的 AI IDE

如果某个工具不支持“skill 发现机制”也没关系。  
你只需要让它：

1. 读取 [video-teaching-doc-skill/SKILL.md](video-teaching-doc-skill/SKILL.md)
2. 按照里面的流程调用 [scripts](scripts)

就能把它当成一个“打包好的工作流模板”来用。

## 三、最简单的一键安装

### 安装命令

如果同事只想先装好基础环境，直接运行：

```bash
git clone https://github.com/huiMiluMilu/jiaoxuewendang.git
cd jiaoxuewendang
bash install.sh
```

如果同事还要发布飞书文档：

```bash
git clone https://github.com/huiMiluMilu/jiaoxuewendang.git
cd jiaoxuewendang
bash install.sh --with-lark
```

如果同事本身就在用 Codex，也可以顺手把 skill 自动链接进去：

```bash
git clone https://github.com/huiMiluMilu/jiaoxuewendang.git
cd jiaoxuewendang
bash install.sh --with-lark --link-codex
```

### 安装脚本会做什么

[install.sh](install.sh) 当前会自动完成这些事：

1. 检查 `Python 3`
2. 创建本地虚拟环境 `.venv`
3. 安装 Python 依赖
4. 可选安装 `lark-cli`
5. 可选把 skill 链接到 `~/.codex/skills`

## 四、默认需要准备什么

### 必需

所有同事至少需要：

1. `Python 3.11+`
2. `Google Chrome`
3. 这个仓库本地副本

### Python 依赖

当前项目默认依赖写在：

- [requirements.txt](requirements.txt)

内容包括：

1. `Pillow`
2. `numpy`
3. `faster-whisper`
4. `imageio-ffmpeg`

### 可选依赖

如果同事要做更完整版本，还需要这些：

1. `lark-cli`
   用于发布飞书文档
2. `Swift`
   用于 macOS Vision OCR
3. `macOS`
   用于当前这套浏览器抓帧 + Vision OCR 的完整链路

## 五、不同能力需要的准备

### 1. 只产出 Markdown 教学文档

这是最简单的版本。

需要：

1. Python 依赖
2. Chrome
3. 能访问视频或回放页

不一定需要：

1. 飞书
2. OCR
3. 红框

### 2. 发布飞书文档

除了基础环境，还需要：

1. `lark-cli`
2. 飞书账号授权
3. 飞书文档创建权限

相关脚本：

- [publish_teaching_doc_to_lark.py](scripts/publish_teaching_doc_to_lark.py)

### 3. 精细截图和红框版

这是最强版本，但要求也更高。

除了基础环境，还需要：

1. macOS
2. Swift
3. Chrome 允许被脚本控制
4. 视频页面能在真实浏览器里播放

相关脚本：

1. [browser_video_capture.py](scripts/browser_video_capture.py)
2. [browser_media_recorder.py](scripts/browser_media_recorder.py)
3. [refine_doc_step_boxes.py](scripts/refine_doc_step_boxes.py)
4. [vision_ocr.swift](scripts/vision_ocr.swift)

## 六、Chrome 需要开什么权限

如果同事要用“浏览器抓帧版”，必须在 Chrome 里打开：

1. `查看 -> 开发者 -> 允许 Apple 事件中的 JavaScript`

建议同时打开：

1. `chrome://inspect/#remote-debugging`
2. 允许当前浏览器实例远程调试

如果回放页面需要登录态，也必须先在 Chrome 里登录对应平台。

## 七、同事实际怎么调用这个仓库

### 方式 A：支持 skill 的工具

如果 AI 工具本身支持 skill 或规则文件，可以直接让它读取：

- [video-teaching-doc-skill/SKILL.md](video-teaching-doc-skill/SKILL.md)

然后执行类似指令：

```text
用这个仓库里的 video-teaching-doc-skill，根据课程回放链接生成教学文档。
先转写，再按老师讲解顺序整理成详细操作步骤，
每一步前加【视频回放时点xx：xx：xx】，
再补关键截图。
如果可以，最后发布到飞书云文档。
```

### 方式 B：不支持 skill 的工具

如果 AI 工具没有 skill 机制，也完全没问题。  
直接让它做这两件事：

1. 先读 `video-teaching-doc-skill/SKILL.md`
2. 再按规则调用 `scripts/` 里的脚本

你可以直接给它这个 prompt：

```text
请把这个仓库当成一个教学文档生成工作流来使用。
先阅读 video-teaching-doc-skill/SKILL.md，
再根据里面的流程调用 scripts 目录中的脚本。
目标是根据课程回放链接生成教学文档：
先转写，再按讲解顺序整理成详细操作步骤，
每一步前加【视频回放时点xx：xx：xx】，
再补关键截图。
如果环境支持，再发布到飞书云文档。
```

### 方式 C：完全不用 AI 工具的 skill 机制

如果某些同事只想把这个仓库当“工具箱”用，也可以。

他们可以直接：

1. 手动抽音频
2. 手动抽帧
3. 手动写 Markdown
4. 用脚本补时间点
5. 用脚本发飞书

也就是说，这个项目本身不是“被某个 AI 绑死”的。

## 八、推荐给同事的标准工作流

建议你要求同事都按这个顺序来，最稳：

1. 在 Chrome 中打开课程回放链接，并确认能播放
2. 激活虚拟环境
3. 让 AI 工具先读取 `SKILL.md`
4. 先产出：
   转写整理稿
   教学文档 Markdown
5. 确认内容方向没问题后，再补截图
6. 最后再决定要不要发飞书

这样做的好处是：

1. 不会一开始就被红框和 OCR 卡住
2. 文案方向先对，再做精细化
3. 真正费时间的步骤放到后面

## 九、仓库里哪些文件最重要

### 1. 规则入口

- [video-teaching-doc-skill/SKILL.md](video-teaching-doc-skill/SKILL.md)

这是整个工作流的“说明书”。

### 2. 核心脚本

- [publish_teaching_doc_to_lark.py](scripts/publish_teaching_doc_to_lark.py)
- [inject_step_timestamps.py](scripts/inject_step_timestamps.py)
- [browser_video_capture.py](scripts/browser_video_capture.py)
- [browser_media_recorder.py](scripts/browser_media_recorder.py)
- [refine_doc_step_boxes.py](scripts/refine_doc_step_boxes.py)

### 3. 参考文档

- [TEAM_SETUP.md](TEAM_SETUP.md)
- [README.md](README.md)
- [video-teaching-doc-prd.md](video-teaching-doc-prd.md)

## 十、常见问题

### 1. 同事不用 Codex，还能不能用

可以。  
只要 AI 工具能读本地仓库、跑命令，就能用。

### 2. 一定要发布飞书吗

不一定。  
飞书只是输出渠道之一，Markdown 本地文档本身就可以交付。

### 3. 一定要做红框吗

不一定。  
红框属于增强项，不是首版必需项。

### 4. Windows 或 Linux 能不能用

可以先做“文字优先版”，也就是：

1. 转写
2. 整理文档
3. 少量截图

但当前最完整的“浏览器抓帧 + Vision OCR + 红框”链路，是偏 macOS 的。

## 十一、你最适合怎么对外发这个项目

如果你要把它发给同事，最推荐的方式是直接发这三个入口：

1. GitHub 仓库地址
2. 一键安装命令
3. 通用 prompt

可以直接发下面这段：

```text
仓库地址：
https://github.com/huiMiluMilu/jiaoxuewendang

安装：
git clone https://github.com/huiMiluMilu/jiaoxuewendang.git
cd jiaoxuewendang
bash install.sh

使用说明：
看 UNIVERSAL_SETUP.md
```

## 十二、当前建议

如果你的目标是“让同事先能用起来”，最推荐的落地方式是：

1. 先让大家都按这个仓库来安装
2. 先统一跑 Markdown 版
3. 飞书发布和精细红框放到第二阶段统一培训

这样成功率最高，也最不容易把同事劝退。
