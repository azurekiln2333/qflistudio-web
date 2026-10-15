## Shared core assets (baseline audit)

- root: `D:\MyNewProjects\qfli_studio_core\assets\content`
- web tutorials: 300
- web examples: 300
- distinct concepts: 27
- linked examples: 300
- normalised unique example bodies: 3/300
- normalised unique lesson code: 3
- normalised unique tutorial titles: 72/300
- normalised unique example titles: 72/300

| metric | unique/total |
| --- | --- |
| tutorial_titles | 300/300 |
| explain | 1/300 |
| lesson_output | 200/300 |
| example_titles | 300/300 |
| example_bodies | 300/300 |

| type | tutorials | examples |
| --- | --- | --- |
| html | 100 | 100 |
| css | 100 | 100 |
| javascript | 100 | 100 |

Top concepts: 可测试实现(300), 边界条件(300), 发布检查(300), 数据建模与不变量(15), 输入校验与错误边界(15), 文件格式与编码(15), 日志与可观测性(15), 缓存与失效策略(12)

Issues: 5
- placeholder: normalised tutorial titles only 72/300 unique after number normalisation
- placeholder: normalised example titles only 72/300 unique after number normalisation
- placeholder: explain only 1/300 unique
- placeholder: lesson_output only 200/300 unique
- placeholder: example bodies duplicate after number normalisation (3/300)
