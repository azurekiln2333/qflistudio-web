# Focused host continuation, October 24

This records host-runner evidence and product test boundaries. It does not
close the eleven-product parent or any native/device gate.

## Executed windows

- [Repair6 owned-job report](web-runtime-repair6-job.json): Note425/Web430 grant,
  root71588 exit1, Job active0,1.115s. Formatting ten files succeeded and
  normalized one existing Dart file. Windows PowerShell could not resolve
  `Get-FileHash`; tests and analysis did not start. [Release431](web-runtime-repair6-channel.log)
  delivered the terminal handoff to JSON. Old evidence was preserved.
- [Repair7 owned-job report](web-runtime-repair7-job.json): Note441/Web451 grant,
  root70588 exit124 at the96-second execution deadline; empty Job confirmed
  after96.127s. [Release453](web-runtime-repair7-channel.log) delivered to Java;
  publisher69816 exited0 with active0. No Web heavy process was retained.
- [Repair7 test log](web-runtime-repair7-tests.log): first34 cases passed,
  including both production bridge engines,18 policy cases and both browser
  CSP/report-sentinel cases. The first Tools layout then failed on a test cast
  from `RawTooltip` to `IconButton` at Clear. All preceding200/404/warn/POST204
  visible-log checks had been reached and passed. Teardown subsequently waited
  for HTTP completion while disposal needed fake-zone progress; repeated
  two-second timeouts caused the deadline. The narrow layout, analyzer suite
  and scoped analysis did not run. There is no combined-suite pass/footer.
- The worker was killed before its final snapshot. An explicitly independent
  [post-timeout raw-hash check](web-runtime-repair7-post-check.json) compared all
 192 captured inputs and found no drift. The separately named
  [post snapshot](web-runtime-repair7-source-after-independent.json) does not
  pretend to be a completed worker-finally result.

## Runner repair and control

Repair8 consumed Note478 through Web479 and [released to Java480](web-runtime-repair8-channel.log).
Its [Job report](web-runtime-repair8-job.json) records root82596 terminal exit1,
active0 at29.691s; publisher56080 terminal exit0/active0 delivered the release.
Formatting succeeded, the five-file suite reached a footer at54PASS/2FAIL,
and scoped analysis returned exit1 with only two `avoid_print` infos in browser
evidence logging. All230 before/after raw hashes matched.

The [test log](web-runtime-repair8-tests.log) proves34 bridge/policy/browser
cases and20 analyzer cases, including the explicit JSX guard. Both Tools
layouts reached all HTTP200/404, warning and POST204 visible-log assertions,
then missed Clear because nested `tester.ensureVisible(target)` scrolled the
outer Tools overview. Their strict TCP teardown probes timed out at200ms with
Windows10060; neither timeout is counted as refused. The initial framework
exception checks passed, but stop/restart/disposal completion remains unproven.

The follow-up source-only fixture aligns the outer server panel once, reveals
targets through the inner public `ScrollPosition.ensureVisible`, and returns
only for a hit-testable target. TCP timeout is2s while accepted refusal codes
stay strict. Browser evidence logging now uses `debugPrintSynchronously`.
Those corrections require a new named window; source review is not a rerun.

Repair9 consumed Note501 through Web504 and [released to Java505](web-runtime-repair9-channel.log).
Its [Job report](web-runtime-repair9-job.json) records root82044 terminal exit1,
active0 at32.303s; publisher36700 terminal exit0/active0 delivered the release.
The [test log](web-runtime-repair9-tests.log) ends54PASS/2FAIL; the same34 runtime
and20 analyzer cases passed. Both Tools cases now pass Clear and the subsequent
diagnostic, perform Stop and observe idle controls, then fail on the2s TCP
probe. [Scoped analysis](web-runtime-repair9-analysis.log) passes with no issues;
all230 raw input hashes remain identical.

The SDK source constructs10060 when that caller deadline expires. A separate
[own-listener Python control](web-loopback-refusal-control-20261024.json) timed
out at2.007s under2s, but received actual Windows10061 at2.032s under5s. This is
host timing evidence, not a Dart/product pass. The fixture now allows5s while
retaining the strict refusal set; that change is unrun. The next six-file gate
also includes the prepared actual-profile named-workspace regression before
Tools. Its input snapshot additionally binds that test, `analysis_options.yaml`
and both runner files; lightweight preflight passed with234 inputs.

Repair10 consumed Go545's explicit deferral of C537 through Web548 and
[released to Note549](web-runtime-repair10-channel.log). Its
[test log](web-runtime-repair10-tests.log) ends **57/57 passed**: the prior54
runtime/analyzer cases, actual Web named-workspace reconstruction and both Tools
layouts. Strict native refusal, restart and final disposal pass with the5s
deadline. Clear, new diagnostics, unchanged configuration/source/history bytes,
owners, cursors and nested expansion assertions remain intact.
[Eleven-file analysis](web-runtime-repair10-analysis.log) has no issues and
formatting changes0 files. All234 raw input hashes match. The
[Job report](web-runtime-repair10-job.json) records root91884 terminal exit0,
active0 at48.57s, no deadline/errors and publisher91528 terminal exit0/active0
with delivered release. Shared Home has other live WIP beyond core HEAD2f9039a3,
so this is a frozen live-tree checkpoint, not isolated published-tree or full
product/native acceptance.

The [Python entry](run-web-owned-window.py) now contains its own Windows Job
primitive, copied from the exact Note425 helper identified in its provenance
comment; it has no runtime dependency on the sibling Note file. The worker is
created suspended and assigned before resume, preventing escaped descendants.
Normal and deadline paths require both the root handle terminal and active0.
The publisher is separately contained; its terminal exit0 is required for a
successful wrapper result. Malformed worker JSON is recorded without skipping
cleanup/publication. Fresh run names preserve previous reports.

The [actual self-control](web-owned-job-self-control-20261024.json) proved the
important negative case: root81344 exited0 while its Job was still nonempty;
only explicit own-Job cleanup reduced active processes to0. This started only
lightweight Python processes and touched no sibling process.

The [PowerShell worker](run-web-focused-window.ps1) uses .NET SHA256 streams
instead of an unavailable cmdlet and explicitly selects UTF8. Its lightweight
`-SnapshotOnly` preflight succeeded under the actual Windows PowerShell
`-NoProfile` launch:192 initial inputs, then230 after adding vendored editor,
core manifest and available native analyzer DLL inputs. No Flutter/Dart test,
analyzer, compiler, browser or device command runs during this preflight.
The unsafe old PID-only parent path has been removed. Analyzer tests precede
the Tools lifecycle file in the next run so a teardown failure cannot hide
the analyzer regression's execution state.

Every later run still requires a new named grant and fresh evidence name.
Full app tests/analysis, current full481 desktop/mobile catalog and native/HAP/
device checks remain separate pending gates. Repair10 establishes the six-file
focused scope above. No new commit or push is established here.
