    @Override // androidx.fragment.app.FragmentActivity, androidx.activity.ComponentActivity, androidx.core.app.ComponentActivity, android.app.Activity
    protected void onCreate(Bundle bundle) {
        super.onCreate(bundle);
        setContentView(R.layout.activity_main);
        this.webView = (WebView) findViewById(R.id.webView);
        this.progressBar = (ProgressBar) findViewById(R.id.progressBar);
        this.errorView = findViewById(R.id.errorView);
        findViewById(R.id.retryButton).setOnClickListener(new View.OnClickListener() { // from class: com.roblox.client.MainActivity$$ExternalSyntheticLambda0
            @Override // android.view.View.OnClickListener
            public final void onClick(View view) {
                this.f$0.m181lambda$onCreate$0$comrobloxclientMainActivity(view);
            }
        });
        WebSettings settings = this.webView.getSettings();
        boolean z = true;
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setDatabaseEnabled(true);
        settings.setLoadsImagesAutomatically(true);
        settings.setMediaPlaybackRequiresUserGesture(false);
        settings.setUseWideViewPort(true);
        settings.setLoadWithOverviewMode(true);
        settings.setMixedContentMode(0);
        settings.setCacheMode(-1);
        settings.setJavaScriptCanOpenWindowsAutomatically(false);
        settings.setSupportMultipleWindows(false);
        CookieManager cookieManager = CookieManager.getInstance();
        cookieManager.setAcceptCookie(true);
        cookieManager.setAcceptThirdPartyCookies(this.webView, true);
        this.webView.setWebChromeClient(new AppWebChromeClient());
        this.webView.setWebViewClient(new AppWebViewClient());
        this.webView.setDownloadListener(new DownloadListener() { // from class: com.roblox.client.MainActivity$$ExternalSyntheticLambda1
            @Override // android.webkit.DownloadListener
            public final void onDownloadStart(String str, String str2, String str3, String str4, long j) {
                this.f$0.m182lambda$onCreate$1$comrobloxclientMainActivity(str, str2, str3, str4, j);
            }
        });
        if (bundle == null) {
            loadStartUrl();
        } else {
            this.webView.restoreState(bundle);
        }
        getOnBackPressedDispatcher().addCallback(this, new OnBackPressedCallback(z) { // from class: com.roblox.client.MainActivity.1
            @Override // androidx.activity.OnBackPressedCallback
            public void handleOnBackPressed() {
                boolean zCanGoBack = MainActivity.this.webView.canGoBack();
                MainActivity mainActivity = MainActivity.this;
                if (zCanGoBack) {
                    mainActivity.webView.goBack();
                } else {
                    mainActivity.finish();
                }
            }
        });
    }