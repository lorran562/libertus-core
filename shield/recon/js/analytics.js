(function () {
    'use strict';

    var config = document.getElementById('labpagesAnalytics');
    if (!config) return;

    var endpoint = config.getAttribute('data-endpoint') || '';
    var websiteId = Number(config.getAttribute('data-website-id'));
    var resultsPath = config.getAttribute('data-results-path') || '';
    var visitorKey = 'lp_analytics_visitor_v1';
    var sessionKey = 'lp_analytics_session_v1';
    var sessionTimeout = 30 * 60 * 1000;
    var pageviewSent = false;
    var analyticsWasConsented = consented();

    function consented() {
        var consent = window.W2BCookies && window.W2BCookies.getConsent ? window.W2BCookies.getConsent() : null;
        return Boolean(consent && consent.categories && consent.categories.analytics);
    }

    function uuid() {
        if (window.crypto && typeof window.crypto.randomUUID === 'function') return window.crypto.randomUUID();
        if (!window.crypto || typeof window.crypto.getRandomValues !== 'function') return null;
        var bytes = new Uint8Array(16);
        window.crypto.getRandomValues(bytes);
        bytes[6] = (bytes[6] & 15) | 64;
        bytes[8] = (bytes[8] & 63) | 128;
        return Array.prototype.map.call(bytes, function (byte, index) {
            return (index === 4 || index === 6 || index === 8 || index === 10 ? '-' : '') + byte.toString(16).padStart(2, '0');
        }).join('');
    }

    function visitorId() {
        try {
            var current = window.localStorage.getItem(visitorKey);
            if (current) return current;
            current = uuid();
            if (current) window.localStorage.setItem(visitorKey, current);
            return current;
        } catch (error) {
            return uuid();
        }
    }

    function sessionId() {
        var now = Date.now();
        try {
            var saved = JSON.parse(window.sessionStorage.getItem(sessionKey) || 'null');
            if (saved && typeof saved.id === 'string' && Number(saved.last) + sessionTimeout >= now) {
                saved.last = now;
                window.sessionStorage.setItem(sessionKey, JSON.stringify(saved));
                return saved.id;
            }
            var id = uuid();
            if (id) window.sessionStorage.setItem(sessionKey, JSON.stringify({ id: id, last: now }));
            return id;
        } catch (error) {
            return uuid();
        }
    }

    function removeDetailedIdentifiers() {
        try { window.localStorage.removeItem(visitorKey); } catch (error) { /* storage may be unavailable */ }
        try { window.sessionStorage.removeItem(sessionKey); } catch (error) { /* storage may be unavailable */ }
    }

    function referrerHost() {
        if (!document.referrer) return null;
        try { return new URL(document.referrer).hostname || null; } catch (error) { return null; }
    }

    function send(scope, type, metadata) {
        if (!endpoint || !Number.isInteger(websiteId) || websiteId < 1) return;
        var eventId = uuid();
        if (!eventId) return;
        var body = {
            website_id: websiteId,
            event_uuid: eventId,
            event_scope: scope,
            event_type: type,
            occurred_at: new Date().toISOString(),
            path: window.location.pathname || '/'
        };
        // This is only the coarse state, never the preference payload. It lets
        // the API classify the same short-lived basic session as decided or not.
        var state = consentState();
        if (state) body.consent_state = state;
        if (scope === 'DETAILED') {
            var visitor = visitorId();
            var session = sessionId();
            if (!visitor || !session) return;
            body.visitor_id = visitor;
            body.session_id = session;
            body.referrer = referrerHost();
            body.metadata = metadata || {};
        }
        var json = JSON.stringify(body);
        try {
            if (navigator.sendBeacon && navigator.sendBeacon(endpoint, new Blob([json], { type: 'text/plain;charset=UTF-8' }))) return;
        } catch (error) { /* fetch fallback remains intentionally best effort */ }
        try {
            window.fetch(endpoint, { method: 'POST', body: json, keepalive: true, credentials: 'omit' }).catch(function () {});
        } catch (error) { /* analytics must never affect site behavior */ }
    }

    function activeScope() {
        return consented() ? 'DETAILED' : 'BASIC';
    }

    function consentState() {
        var consent = window.W2BCookies && window.W2BCookies.getConsent ? window.W2BCookies.getConsent() : null;
        if (!consent || !consent.categories) return null;
        return consent.categories.analytics ? 'GRANTED' : 'DENIED';
    }

    function pageview() {
        if (pageviewSent || document.visibilityState === 'prerender') return;
        pageviewSent = true;
        // DETAILED enriches the total metric; it never sends a BASIC duplicate.
        send(activeScope(), 'PAGE_VIEW');
    }

    function clickType(anchor) {
        var explicit = anchor.getAttribute('data-analytics-event');
        if (explicit === 'WHATSAPP_CLICK' || explicit === 'PHONE_CLICK' || explicit === 'RESULTS_CLICK') return explicit;
        var href = (anchor.getAttribute('href') || '').toLowerCase();
        if (href.indexOf('tel:') === 0) return 'PHONE_CLICK';
        if (href.indexOf('https://wa.me/') === 0 || href.indexOf('https://api.whatsapp.com/') === 0 || href.indexOf('/whatsapp') === 0) return 'WHATSAPP_CLICK';
        if (resultsPath && href.split('?')[0] === resultsPath.toLowerCase().split('?')[0]) return 'RESULTS_CLICK';
        return null;
    }

    document.addEventListener('click', function (event) {
        var anchor = event.target.closest ? event.target.closest('a') : null;
        if (!anchor) return;
        var type = clickType(anchor);
        if (type) send(activeScope(), type, { link_type: type.toLowerCase().replace('_click', '') });
    }, true);

    document.addEventListener('w2bCookieConsentUpdated', function (event) {
        var nowConsented = consented();
        var decision = event.detail && event.detail.decision;
        if (decision) {
            // The decision itself is aggregate-only: no preference payload is sent.
            send(activeScope(), decision);
        } else if (nowConsented && !analyticsWasConsented) {
            // Current page was measured as BASIC; the grant must not add a second pageview.
            send('DETAILED', 'CONSENT_ANALYTICS_GRANTED');
        }
        if (!nowConsented) removeDetailedIdentifiers();
        analyticsWasConsented = nowConsented;
    });
    document.addEventListener('visibilitychange', function () { if (document.visibilityState === 'visible') pageview(); });
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', pageview); else pageview();
})();
