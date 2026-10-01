# Design

Shared `qfli_studio_core` owns catalog/detail UI, code-file writes, project
registration, saved example edits and initial editor-file selection. WebForge
owns preview entry selection and carries safe project metadata through both
WebForge and native Nginx middleware.

Catalogs use MD3 list rows. Details pass the displayed code and real stores to
the import dialog. New imports create a persistent registered project; existing
project imports preserve identity and entry. Success passes the actual path to
`EditorPage.initialOpenPath`, taking precedence over session restoration.

The safe HTML entry found by RunnerService chooses the default preview root.
An explicit Web root still wins. The selected root-relative index is passed to
both server engines; missing assets continue returning 404.
