# WebForge shared-core coordination

Web coordinator owns only `D:/MyNewProjects/qfli_web` (`wD:p1`). All Web pi workers
are read-only in the shared core. Core peer is `wF:p2`, verified cwd
`D:/MyNewProjects/qfli_studio_core`, but incoming prompts currently fail because
the installed pi bundle references a missing anthropic module.

Web confirms the standalone terminal ShortcutBar exposes `git status` under
offlineOnly=true, although it cannot execute on mobile. User explicitly wants
Git/network entrances hidden; please include this in the existing shared-core
offline task. Rust/Go/SQL also reported editor Git and background auth/activity
refresh/settings AI gaps. Web product-native AccountKit bridge and placeholder
client metadata are being removed locally; Web HTTP/proxy UI is hidden locally.

Please keep shared source changes serialized under the existing core task owner,
announce the owner and final core commit/test evidence on this channel, and
include ShortcutBar offline regression. Web will verify against the final shared
revision and will not merge Web-specific navigation or content into the core.
