(function () {
    'use strict';

    const STORAGE_KEY = 'w2b_cookie_consent';
    const CONSENT_VERSION = 1;
    const EXPIRATION_DAYS = 180;
    const DAY_IN_MS = 24 * 60 * 60 * 1000;
    const W2B_COOKIE_RELOAD_ON_CHANGE = false;
    const OPTIONAL_CATEGORIES = ['analytics', 'functionality', 'marketing'];
    const ALL_CATEGORIES = ['necessary'].concat(OPTIONAL_CATEGORIES);
    const SCRIPT_ATTRIBUTES_TO_COPY = ['id', 'async', 'defer', 'crossorigin', 'referrerpolicy', 'integrity', 'nonce'];
    const ANALYTICS_STORAGE_KEYS = ['lp_analytics_visitor_v1', 'lp_analytics_session_v1'];

    let banner = null;
    let modalElement = null;
    let modalInstance = null;
    let domReady = false;

    function storageAvailable() {
        try {
            const testKey = STORAGE_KEY + '_test';
            window.localStorage.setItem(testKey, '1');
            window.localStorage.removeItem(testKey);

            return true;
        } catch (error) {
            return false;
        }
    }

    function getStoredConsent() {
        if (!storageAvailable()) return null;

        try {
            const rawConsent = window.localStorage.getItem(STORAGE_KEY);
            return rawConsent ? JSON.parse(rawConsent) : null;
        } catch (error) {
            return null;
        }
    }

    function normalizeCategories(categories) {
        const normalized = { necessary: true };

        OPTIONAL_CATEGORIES.forEach(function (category) {
            normalized[category] = Boolean(categories && categories[category]);
        });

        return normalized;
    }

    function isValidConsent(consent) {
        if (!consent || consent.version !== CONSENT_VERSION || !consent.createdAt || !consent.categories) {
            return false;
        }

        const createdAt = Date.parse(consent.createdAt);

        if (Number.isNaN(createdAt)) {
            return false;
        }

        return Date.now() - createdAt <= EXPIRATION_DAYS * DAY_IN_MS;
    }

    function buildConsent(categories) {
        const createdAt = new Date();
        const expiresAt = new Date(createdAt.getTime() + EXPIRATION_DAYS * DAY_IN_MS);

        return {
            version: CONSENT_VERSION,
            createdAt: createdAt.toISOString(),
            expiresAt: expiresAt.toISOString(),
            categories: normalizeCategories(categories)
        };
    }

    function dispatchConsentUpdated(consent, decision) {
        document.dispatchEvent(new CustomEvent('w2bCookieConsentUpdated', {
            detail: Object.assign({}, consent, { decision: decision || null })
        }));
    }

    function showBanner() {
        if (banner) {
            banner.classList.add('is-visible');
            banner.removeAttribute('hidden');
        }
    }

    function hideBanner() {
        if (banner) {
            banner.classList.remove('is-visible');
            banner.setAttribute('hidden', 'hidden');
        }
    }

    function getConsent() {
        const consent = getStoredConsent();

        return isValidConsent(consent) ? consent : null;
    }

    function saveConsent(categories, decision) {
        const consent = buildConsent(categories);

        if (storageAvailable()) {
            try {
                window.localStorage.setItem(STORAGE_KEY, JSON.stringify(consent));
            } catch (error) {
                console.warn('W2BCookies: não foi possível salvar o consentimento no localStorage.');
            }
        } else {
            console.warn('W2BCookies: localStorage indisponível; consentimento não foi persistido.');
        }

        // Detailed identifiers belong exclusively to the opt-in layer.
        if (!consent.categories.analytics) {
            clearDetailedAnalyticsStorage();
        }

        hideBanner();
        dispatchConsentUpdated(consent, decision);

        return consent;
    }

    function clearDetailedAnalyticsStorage() {
        try { window.localStorage.removeItem(ANALYTICS_STORAGE_KEYS[0]); } catch (error) { /* storage unavailable */ }
        try { window.sessionStorage.removeItem(ANALYTICS_STORAGE_KEYS[1]); } catch (error) { /* storage unavailable */ }
    }

    function acceptAll() {
        return saveConsent({
            necessary: true,
            analytics: true,
            functionality: true,
            marketing: true
        }, 'CONSENT_ACCEPT_ALL');
    }

    function rejectNonNecessary() {
        return saveConsent({
            necessary: true,
            analytics: false,
            functionality: false,
            marketing: false
        }, 'CONSENT_REJECT_OPTIONAL');
    }

    function isCategoryAllowed(category, consent) {
        if (category === 'necessary') return true;

        if (ALL_CATEGORIES.indexOf(category) === -1) {
            return false;
        }

        return Boolean(consent && consent.categories && consent.categories[category]);
    }

    function copyScriptAttributes(blockedScript, script) {
        SCRIPT_ATTRIBUTES_TO_COPY.forEach(function (attribute) {
            if (!blockedScript.hasAttribute(attribute)) return;

            const value = blockedScript.getAttribute(attribute);

            if (value === '') {
                script.setAttribute(attribute, '');
            } else {
                script.setAttribute(attribute, value);
            }
        });
    }

    function loadAllowedScripts() {
        const consent = getConsent();
        const blockedScripts = document.querySelectorAll('script[type="text/plain"][data-w2b-cookie-script]');

        blockedScripts.forEach(function (blockedScript) {
            if (blockedScript.getAttribute('data-w2b-cookie-loaded') === 'true') return;

            const category = blockedScript.getAttribute('data-w2b-cookie-script');

            if (!isCategoryAllowed(category, consent)) return;

            const script = document.createElement('script');
            const src = blockedScript.getAttribute('data-src');

            copyScriptAttributes(blockedScript, script);

            if (src) {
                script.src = src;
                if (!blockedScript.hasAttribute('async') && !blockedScript.hasAttribute('defer')) {
                    script.async = false;
                }
            } else {
                script.text = blockedScript.textContent || '';
            }

            blockedScript.setAttribute('data-w2b-cookie-loaded', 'true');
            blockedScript.parentNode.insertBefore(script, blockedScript.nextSibling);
        });
    }

    function getSwitches() {
        if (!modalElement) return [];

        return Array.prototype.slice.call(modalElement.querySelectorAll('[data-w2b-cookie-category]'));
    }

    function updateSwitchesFromConsent() {
        const consent = getConsent();
        const categories = consent ? consent.categories : { necessary: true };

        getSwitches().forEach(function (input) {
            const category = input.getAttribute('data-w2b-cookie-category');
            input.checked = category === 'necessary' ? true : Boolean(categories[category]);
        });
    }

    function collectSwitchCategories() {
        const categories = { necessary: true };

        getSwitches().forEach(function (input) {
            const category = input.getAttribute('data-w2b-cookie-category');

            if (ALL_CATEGORIES.indexOf(category) === -1) return;

            categories[category] = category === 'necessary' ? true : Boolean(input.checked);
        });

        return normalizeCategories(categories);
    }

    function getModalInstance() {
        if (!modalElement) return null;

        if (
            window.bootstrap &&
            window.bootstrap.Modal &&
            typeof window.bootstrap.Modal.getOrCreateInstance === 'function' &&
            !modalInstance
        ) {
            modalInstance = window.bootstrap.Modal.getOrCreateInstance(modalElement);
        }
        return modalInstance;
    }

    function hasJQueryModal() {
        return Boolean(
            window.jQuery &&
            window.jQuery.fn &&
            typeof window.jQuery.fn.modal === 'function'
        );
    }

    function closePreferencesModal() {
        if (!modalElement || !modalElement.classList.contains('show')) return;

        const instance = getModalInstance();

        if (instance) {
            instance.hide();
        } else if (hasJQueryModal()) {
            window.jQuery(modalElement).modal('hide');
        }
    }

    function openPreferencesModal() {
        const instance = getModalInstance();

        if (instance) {
            instance.show();
            return true;
        }

        if (hasJQueryModal()) {
            window.jQuery(modalElement).modal('show');
            return true;
        }

        console.warn('W2BCookies: Bootstrap Modal não está disponível.');
        return false;
    }

    function openPreferences() {
        if (!domReady) return;

        updateSwitchesFromConsent();
        openPreferencesModal();
    }

    function resetConsent() {
        if (storageAvailable()) {
            try {
                window.localStorage.removeItem(STORAGE_KEY);
            } catch (error) {
                console.warn('W2BCookies: não foi possível remover o consentimento do localStorage.');
            }
        }

        clearDetailedAnalyticsStorage();

        showBanner();
    }

    function bindActions() {
        document.addEventListener('click', function (event) {
            const action = event.target.closest([
                '[data-w2b-cookie-accept-all]',
                '[data-w2b-cookie-reject]',
                '[data-w2b-cookie-manage]',
                '[data-w2b-cookie-save]',
                '[data-w2b-cookie-preferences]'
            ].join(','));

            if (!action) return;

            event.preventDefault();

            if (action.matches('[data-w2b-cookie-accept-all]')) {
                acceptAll();
                closePreferencesModal();
            } else if (action.matches('[data-w2b-cookie-reject]')) {
                rejectNonNecessary();
                closePreferencesModal();
            } else if (action.matches('[data-w2b-cookie-manage], [data-w2b-cookie-preferences]')) {
                openPreferences();
            } else if (action.matches('[data-w2b-cookie-save]')) {
                saveConsent(collectSwitchCategories(), 'CONSENT_SAVE_PREFERENCES');
                closePreferencesModal();
            }
        });
    }

    function init() {
        domReady = true;
        banner = document.getElementById('w2b-cookie-banner');
        modalElement = document.getElementById('w2b-cookie-modal');

        if (banner && modalElement) {
            bindActions();

            if (getConsent()) {
                hideBanner();
            } else {
                showBanner();
            }
        }

        loadAllowedScripts();
    }

    window.W2BCookies = {
        getConsent: getConsent,
        saveConsent: saveConsent,
        acceptAll: acceptAll,
        rejectNonNecessary: rejectNonNecessary,
        openPreferences: openPreferences,
        resetConsent: resetConsent,
        clearDetailedAnalyticsStorage: clearDetailedAnalyticsStorage,
        loadAllowedScripts: loadAllowedScripts
    };

    document.addEventListener('DOMContentLoaded', init);
    document.addEventListener('w2bCookieConsentUpdated', function () {
        if (W2B_COOKIE_RELOAD_ON_CHANGE) {
            window.location.reload();
            return;
        }

        loadAllowedScripts();
    });
})();
