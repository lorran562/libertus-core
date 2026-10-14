# SAMPLE DELIVERABLE — Android APK Security Review

> Exemplo real de entrega, produzido a partir de análise que executei. Alvo
> anonimizado: descrevo a classe do problema e o método, sem nomear loja ou
> publicadora — o relatório de um cliente nomeia o alvo dele, o portfólio não
> nomeia terceiros.
>
> Use este arquivo como amostra na proposta. Ele responde a pergunta que o
> comprador técnico faz: *"esse cara entrega laudo com evidência ou só texto bonito?"*

---

## Scope and authorization

Static analysis of an Android application package (APK) obtained from a public
app store listing. Analysis is fully static: the artifact was inspected, never
installed, never executed, and no connection was made to any server belonging to
the publisher or the store.

The deliverable below is the same structure used in a paid engagement. In a
client engagement the scope line names the artifact, its SHA-256, and the written
authorization from the asset owner.

## Method and tooling

| Step | Tool | What it produces |
|---|---|---|
| Manifest and resource decode | apktool 3.0.3 | Decoded `AndroidManifest.xml`, resources |
| Code reconstruction | jadx 1.5.6 | Reconstructed Java/Kotlin sources |
| Structured inspection | REA 6.4.0 (jadx-headless-mcp 0.7.1) | Package inventory, class search, single-method decompilation with an evidence record |
| Security-specific review | purpose-built static analyzer | Exported components, deep links, dangerous permissions, insecure manifest flags, risky code patterns |

Every artifact in the chain is hashed. Version banner of each engine is recorded,
so the analysis can be reproduced later against the same input.

---

## Finding 1 — Repackaged application using a third party's package identifier

**Severity:** informational to the buyer / brand-impact for the impersonated
publisher
**Class:** impersonation, attribution abuse

**Observation.** The package declares the identifier of a well-known game
publisher's official client. The implementation does not belong to that
publisher:

| Fact | Evidence |
|---|---|
| Application package inventory contains **6 classes** | class search over the full APK |
| **No native libraries** present | archive inventory |
| **No functionality** of the named publisher | no matching class, string or asset |
| Only two external domains in the entire package | static string extraction |
| Build configuration self-identifies a webview-wrapper flavor | decompiled `BuildConfig` |

Decompiled runtime configuration:

```java
static {
    String strLastSegment = lastSegment(BuildConfig.APPLICATION_ID);
    SUB4 = strLastSegment;
    LOCKER_URL = "https://<monetization-domain>/mts/?month=<period>"
               + "&aff_sub4=" + strLastSegment + "&aff_sub5=dga";
}
```

`aff_sub4` / `aff_sub5` are affiliate tracking parameters. The only screen the
application loads is that URL.

**Impact.** A user looking for the publisher's client on a third-party store
receives an application bearing the publisher's identifier whose content is
controlled by a third party. It is attribution abuse and an affiliate
monetization channel built on someone else's brand.

**Boundary I did not cross.** I followed the redirect chain to its first hop only
and stopped. The next hop is an offer/installation page; retrieving further
artifacts from an unknown distribution chain is risk without analytic value.

---

## Finding 2 — WebView configured to accept insecure content

**Severity:** medium
**Class:** CWE-1188 (insecure default) / mixed content

Decompiled `MainActivity.onCreate` (single method, obtained via
`inspect-android-method`):

```java
WebSettings settings = this.webView.getSettings();
settings.setJavaScriptEnabled(true);
settings.setDomStorageEnabled(true);
settings.setDatabaseEnabled(true);
settings.setMixedContentMode(0);   // 0 = MIXED_CONTENT_ALWAYS_ALLOW
settings.setJavaScriptCanOpenWindowsAutomatically(false);
settings.setSupportMultipleWindows(false);
CookieManager cm = CookieManager.getInstance();
cm.setAcceptCookie(true);
cm.setAcceptThirdPartyCookies(this.webView, true);
```

`setMixedContentMode(0)` is `MIXED_CONTENT_ALWAYS_ALLOW`: the WebView loads
plaintext HTTP subresources inside an HTTPS page. The manifest additionally
declares `android:usesCleartextTraffic="true"` and no
`network_security_config` restriction.

**Impact.** The application renders third-party content — from a domain outside
the publisher's control — with transport downgrade permitted and third-party
cookies accepted, inside a shell the user believes belongs to the publisher.

**Note on rigor:** the numeric constant matters. `setMixedContentMode(0)` and
`setCacheMode(-1)` are not self-describing in decompiled output; the value was
resolved against the Android API constant rather than assumed from the number.

---

## What was checked and found clean

Reporting negatives is part of the deliverable, because it tells the buyer what
surface remains:

- `android:allowBackup = "false"` — correct.
- No `android:debuggable` flag in a release build.
- **No `addJavascriptInterface`** — the classic JavaScript-to-Java bridge is
  absent, which is the correct decision for this design.
- No exported component without a permission requirement other than the launcher
  activity and one support-library receiver.
- No credential-collecting form and no publisher branding on the first redirect
  hop — this is attribution and monetization abuse, **not** a phishing page. This
  distinction was verified rather than assumed, and it changes the severity
  assessment.

---

## Limitations of this review

Stated explicitly, as in every deliverable:

1. Static analysis only. Runtime behavior, server-side handling and anything
   behind authentication were not evaluated.
2. Artifact-level facts hold for the analyzed build; a different build of the
   same package may differ. Version and hash are recorded for this reason.
3. The redirect chain was characterized to its first hop only.
4. Findings describe this artifact. No claim is made about the publisher's own
   application, which was not examined in this review.

---

## Deliverable format (what a client receives)

1. `report.pdf` — executive summary, findings with severity, impact, evidence,
   remediation.
2. `report.md` — the same content in Markdown, for a developer's repo or ticket.
3. `evidence/` — per-finding evidence: decompiled snippets, engine version
   banners, artifact hashes, and the exact commands used to reproduce each step.
4. A short "what I did not evaluate" section, so the client knows the boundary of
   what they bought.
