# 教学文档生成工作流

这个项目用来把课程回放、录屏演示视频整理成可交付的教学文档，并支持发布到飞书云文档。

## 当前可用产物

- 红框修正版飞书文档：
  [微信小程序课程前30分钟教学文档 红框修正版](https://www.feishu.cn/docx/KQi5d2EZgob39nxmpblcjnFBntf)
- 当前教学文档草稿：
  [前30分钟-教学文档草稿.md](/Users/shihui/Desktop/玩玩编程/生产教学文档/simple-demo/transcript-first-30min/前30分钟-教学文档草稿.md)
- 当前完整教学文档：
  [前30分钟-完整教学文档-v2.md](/Users/shihui/Desktop/玩玩编程/生产教学文档/simple-demo/transcript-first-30min/前30分钟-完整教学文档-v2.md)
- 转写整理稿：
  [前30分钟-转写整理稿.md](/Users/shihui/Desktop/玩玩编程/生产教学文档/simple-demo/transcript-first-30min/前30分钟-转写整理稿.md)

## 飞书发布结果

- 红框修正版发布结果：
  [lark_publish_redbox_fixed_result.json](/Users/shihui/Desktop/玩玩编程/生产教学文档/trial-run-v2/lark_publish_redbox_fixed_result.json)
- 红框修正版图片清单：
  [lark_publish_redbox_fixed_manifest.json](/Users/shihui/Desktop/玩玩编程/生产教学文档/trial-run-v2/lark_publish_redbox_fixed_manifest.json)

## 目录说明

- [scripts](/Users/shihui/Desktop/玩玩编程/生产教学文档/scripts)
  处理转写、抽帧、红框标注、时间点注入、飞书发布的脚本
- [video-teaching-doc-skill](/Users/shihui/Desktop/玩玩编程/生产教学文档/video-teaching-doc-skill)
  教学文档生成 skill
- [video-teaching-doc-prd.md](/Users/shihui/Desktop/玩玩编程/生产教学文档/video-teaching-doc-prd.md)
  产品方案与阶段规划
- [simple-demo/transcript-first-30min](/Users/shihui/Desktop/玩玩编程/生产教学文档/simple-demo/transcript-first-30min)
  当前这次“前 30 分钟”试跑的主要输出
- [trial-run-v2](/Users/shihui/Desktop/玩玩编程/生产教学文档/trial-run-v2)
  飞书发布结果与验证记录

## 当前流程

1. 从视频中抽取音频并生成转写
2. 按讲解顺序整理成学员可读的教学文案
3. 为每个步骤补 `【视频回放时点xx：xx：xx】`
4. 根据步骤语义和 OCR 结果标注真正要操作的控件
5. 生成 Markdown 教学文档
6. 发布到飞书云文档，并插入本地截图

## 关键脚本

- [publish_teaching_doc_to_lark.py](/Users/shihui/Desktop/玩玩编程/生产教学文档/scripts/publish_teaching_doc_to_lark.py)
  把 Markdown 和本地图片发布到飞书云文档
- [refine_doc_step_boxes.py](/Users/shihui/Desktop/玩玩编程/生产教学文档/scripts/refine_doc_step_boxes.py)
  依据步骤语义、OCR 和上下文重画红框
- [inject_step_timestamps.py](/Users/shihui/Desktop/玩玩编程/生产教学文档/scripts/inject_step_timestamps.py)
  为文档步骤注入视频回放时间点
- [vision_ocr.swift](/Users/shihui/Desktop/玩玩编程/生产教学文档/scripts/vision_ocr.swift)
  使用 macOS Vision 对截图做 OCR

## 说明

- 当前仓库保留了最终产物和部分中间结果，方便继续修文案、修红框、复发飞书
- 等版本确认稳定后，可以再清理原始音频、密集抽帧和调试中间文件
