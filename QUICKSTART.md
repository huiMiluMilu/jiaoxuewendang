# 30 秒上手

## 1. 克隆仓库

```bash
git clone https://github.com/huiMiluMilu/jiaoxuewendang.git
cd jiaoxuewendang
```

## 2. 一键安装

只装基础环境：

```bash
bash install.sh
```

如果要发飞书文档：

```bash
bash install.sh --with-lark
```

如果你本身就在用 Codex：

```bash
bash install.sh --with-lark --link-codex
```

## 3. 让 AI 用这个仓库

如果你的 AI 工具支持读取仓库规则文件，就让它先读：

```text
video-teaching-doc-skill/SKILL.md
```

然后给它这段话：

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

## 4. 看完整说明

- 可直接复制给 AI 的对话模板：
  [AI_CHAT_GUIDE.md](AI_CHAT_GUIDE.md)
- 通用说明：[UNIVERSAL_SETUP.md](UNIVERSAL_SETUP.md)
- 团队说明：[TEAM_SETUP.md](TEAM_SETUP.md)
- 项目入口：[README.md](README.md)
