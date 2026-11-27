# Web branch disposition, 2026-11-27

Source: D:/MyNewProjects/qfli_web. Target: E:/MyNewProjects/QFLIProjects/qflistudio-web.

| Ref or endpoint | Observed full SHA | Disposition |
| --- | --- | --- |
| local main | 1fed59c2a5137560b393ffaea2c9363ead83bbd9 | Fast-forward to reviewed migration commits after source preservation. |
| local ci/app-packages | 1a05b08117dc69cc8aa160d88f5dc18f0b8d7231 | Four reviewed migration commits above baseline; include by fast-forward, retain branch. |
| GitHub main | 1fed59c2a5137560b393ffaea2c9363ead83bbd9 | Publication destination through orchestration gate only. |
| GitHub ci/app-packages | 1a05b08117dc69cc8aa160d88f5dc18f0b8d7231 | Same four commits; no unique remote work beyond local branch. Retain remote branch. |
| Gitee main | 1fed59c2a5137560b393ffaea2c9363ead83bbd9 | Already ancestor of migration branch; no merge needed, no push. Only advertised branch. |
| CNB main | 1fed59c2a5137560b393ffaea2c9363ead83bbd9 | Already ancestor; no merge needed, no push. Only advertised branch. |
| GitCode main | 1fed59c2a5137560b393ffaea2c9363ead83bbd9 | Already ancestor; no merge needed, no push. Only advertised branch. |
| GitLab HTTPS main | 1fed59c2a5137560b393ffaea2c9363ead83bbd9 | Already ancestor; no merge needed, no push. Only advertised branch. |
| GitLab SSH push endpoint main | 1fed59c2a5137560b393ffaea2c9363ead83bbd9 | Prior 2026-11-26 audit matched HTTPS. No push. |
| target local main | 1fed59c2a5137560b393ffaea2c9363ead83bbd9 | Clean independent clone; frozen until final main handoff. |

Live GitHub and four HTTPS mirror heads re-read on 2026-11-27. No branch is
deleted.

Source origin history: the 2026-11-26 audit found five push URLs on the source
`origin`. That is now historical. The current source configuration keeps the
mirror remotes locally, and only the `origin` push URL is narrowed to GitHub.
The mirror remote-tracking refs stay in the source `.git`; they are not copied
outside the workspace. The external backup holds the former Git config only.
Source `origin` must never be used for publishing beyond the narrowed GitHub
push URL. Target origin has one GitHub fetch URL and one GitHub push URL.

The source has one registered worktree and no live stashes. Dropped stash 71c569c and its index parent c42b691 are recovery objects, not branch integration candidates. Preserve old .git. Do not merge the old stash blindly or rewrite history.

Current integration is pending source review, durable Trellis publication, clean local main and push gate. This record does not claim final synchronization or passing app CI.

## Local integration checkpoint, 2026-11-27

The source Codex fast-forwarded local main through c57833d024b43733a8f96ae3e7b610f32f6e44a4 after reviewing the migration chain. Local ci/app-packages is retained at that commit and has no unique work outside main. GitHub ci/app-packages at 1a05b08117dc69cc8aa160d88f5dc18f0b8d7231 and all audited mirror main tips are ancestors of this integrated main. No branch was deleted or history rewritten. Subsequent evidence-only or repair commits stay on main and go through the same push gate.

The source working tree was clean at this checkpoint. Publication, final cloud acceptance and the frozen target pull remain pending. The final published SHA and target parity are recorded in the orchestration progress/status files and formal Herdr handoff.
