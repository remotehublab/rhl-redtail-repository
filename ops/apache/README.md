# REDTAIL response headers

Include `redtail-response-policies.conf` only inside the
`redtail.rhlab.ece.uw.edu` HTTPS virtual host. The existing HTTP virtual host
must continue redirecting to HTTPS; do not include this file there.

The frame policy allows same-origin parents and blocks cross-origin parents.
It does not restrict outgoing video iframes, ordinary links, or downloads.
Flask supplies the same framing policy for local development. Apache applies
it to direct files and errors too, and avoids duplicate upstream headers.

HSTS starts with `max-age=86400` (one day), without `includeSubDomains` or
`preload`. Increase its duration only in a separately reviewed change after
production verification. A broader CSP must be reconciled with both Flask and
Apache rather than added as a second conflicting policy.

## Deployment and verification

Use the normal deployment process and check host drift before updating. Run
`apachectl configtest` before reloading Apache: restarting only Gunicorn does
not reload this configuration. Check HTTPS responses for the homepage, login,
a public document, static assets, and a missing URL. Each must have one copy
of the three policy headers. Confirm HTTP still redirects to HTTPS.

Run browser frame-protection tests, authentication/download tests, and visual
regressions. The video test isolates the external provider to verify that our
policy permits its iframe; it does not establish third-party streaming uptime.

## Rollback

Revert the isolated policy commit through the normal source-controlled
deployment. To clear an already cached HSTS policy, explicitly serve
`Strict-Transport-Security: max-age=0` over valid HTTPS before removing it.
Removing the header alone does not immediately clear client caches; the
initial policy expires after one day. Do not disable HTTPS during rollback.
