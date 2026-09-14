package com.choicevietnam.app

import android.annotation.SuppressLint
import android.content.Context
import android.net.ConnectivityManager
import android.net.NetworkCapabilities
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.util.Log
import android.view.View
import android.view.WindowInsets
import android.view.WindowInsetsController
import android.webkit.JavascriptInterface
import android.webkit.ValueCallback
import android.webkit.WebChromeClient
import android.webkit.WebResourceRequest
import android.webkit.WebResourceResponse
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.Button
import android.widget.LinearLayout
import android.widget.ProgressBar
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.swiperefreshlayout.widget.SwipeRefreshLayout

/**
 * Choice Viet Nam - 单机版 WebView 主界面
 *
 * 当前版本为纯单机离线壳：
 *   - 启动后直接加载 APK 内置的 assets/index.html（含 CHOICE SLATS VIET NAM Logo）
 *   - 不依赖远程服务器，无网络也能显示 Logo 与三语标题
 *   - 保留 WebView 完整能力（JS、文件选择、下载、返回键等），
 *     后续把 choice-project 前端产物放进 assets 即可直接运行
 */
class MainActivity : AppCompatActivity() {

    companion object {
        private const val TAG = "ChoiceVN"
        private const val HOME_URL = "file:///android_asset/index.html"
        private const val EXIT_INTERVAL = 2000L
    }

    private lateinit var webView: WebView
    private lateinit var swipeRefresh: SwipeRefreshLayout
    private lateinit var progressBar: ProgressBar
    private lateinit var errorLayout: LinearLayout
    private lateinit var errorText: TextView
    private lateinit var retryButton: Button

    private var lastBackPressed = 0L

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        initViews()
        setupWebView()
        applyFullScreen()
        loadHome()
    }

    private fun initViews() {
        webView = findViewById(R.id.webView)
        swipeRefresh = findViewById(R.id.swipeRefresh)
        progressBar = findViewById(R.id.progressBar)
        errorLayout = findViewById(R.id.errorLayout)
        errorText = findViewById(R.id.errorText)
        retryButton = findViewById(R.id.retryButton)

        swipeRefresh.setColorSchemeResources(R.color.primary)
        swipeRefresh.setOnRefreshListener {
            webView.reload()
            swipeRefresh.isRefreshing = false
        }

        retryButton.setOnClickListener { loadHome() }
    }

    @SuppressLint("SetJavaScriptEnabled")
    private fun setupWebView() {
        webView.settings.apply {
            javaScriptEnabled = true
            domStorageEnabled = true
            databaseEnabled = true
            allowFileAccess = true
            allowContentAccess = true
            mixedContentMode = android.webkit.WebSettings.MIXED_CONTENT_ALWAYS_ALLOW
            setSupportMultipleWindows(false)
            builtInZoomControls = true
            displayZoomControls = false
            useWideViewPort = true
            loadWithOverviewMode = true
        }

        webView.webViewClient = object : WebViewClient() {
            override fun onPageStarted(view: WebView?, url: String?, favicon: android.graphics.Bitmap?) {
                progressBar.visibility = View.VISIBLE
                progressBar.progress = 0
            }

            override fun onPageFinished(view: WebView?, url: String?) {
                progressBar.visibility = View.GONE
                errorLayout.visibility = View.GONE
                injectLocaleBridge()
            }

            override fun onReceivedError(
                view: WebView?,
                errorCode: Int,
                description: String?,
                failingUrl: String?
            ) {
                Log.e(TAG, "WebView error $errorCode: $description @ $failingUrl")
                showError(getString(R.string.load_failed))
            }

            override fun shouldInterceptRequest(view: WebView?, request: WebResourceRequest?): WebResourceResponse? {
                // 单机版：所有资源来自本地 assets，无需远程代理
                return super.shouldInterceptRequest(view, request)
            }
        }

        webView.webChromeClient = object : WebChromeClient() {
            override fun onProgressChanged(view: WebView?, newProgress: Int) {
                progressBar.progress = newProgress
                if (newProgress >= 100) {
                    progressBar.visibility = View.GONE
                }
            }

            override fun onShowFileChooser(
                webView: WebView?,
                filePathCallback: ValueCallback<Array<android.net.Uri>>?,
                fileChooserParams: FileChooserParams?
            ): Boolean {
                // 预留：后续 choice-project 需要上传文件时，可在这里启动系统文件选择器
                Toast.makeText(this@MainActivity, "File upload not yet enabled", Toast.LENGTH_SHORT).show()
                filePathCallback?.onReceiveValue(null)
                return true
            }
        }

        webView.addJavascriptInterface(ChoiceBridge(this), "AndroidBridge")
    }

    private fun injectLocaleBridge() {
        // 把当前 Android 系统语言告知网页，让 index.html 内的 JS 显示对应语言标题
        val lang = when (resources.configuration.locales.get(0).language) {
            "zh" -> "zh"
            "vi" -> "vi"
            else -> "en"
        }
        webView.evaluateJavascript("if(typeof window.setAppLang==='function') window.setAppLang('$lang');", null)
    }

    private fun loadHome() {
        if (!isNetworkAvailable()) {
            // 单机版本地 index.html 不依赖网络，仍然加载；只有真正访问远程 URL 时才需要网络
            Log.i(TAG, "Network unavailable, loading local assets anyway")
        }
        errorLayout.visibility = View.GONE
        webView.loadUrl(HOME_URL)
    }

    private fun showError(msg: String) {
        progressBar.visibility = View.GONE
        errorText.text = msg
        errorLayout.visibility = View.VISIBLE
    }

    private fun applyFullScreen() {
        window.decorView.setOnApplyWindowInsetsListener { _, insets ->
            if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.R) {
                window.insetsController?.let { controller ->
                    controller.hide(WindowInsets.Type.statusBars() or WindowInsets.Type.navigationBars())
                    controller.systemBarsBehavior = WindowInsetsController.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE
                }
            } else {
                @Suppress("DEPRECATION")
                window.decorView.systemUiVisibility = (
                    View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
                        or View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
                        or View.SYSTEM_UI_FLAG_FULLSCREEN
                        or View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
                        or View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
                )
            }
            insets
        }
    }

    private fun isNetworkAvailable(): Boolean {
        val cm = getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
        return if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.M) {
            val network = cm.activeNetwork ?: return false
            val capabilities = cm.getNetworkCapabilities(network) ?: return false
            capabilities.hasTransport(NetworkCapabilities.TRANSPORT_WIFI) ||
                capabilities.hasTransport(NetworkCapabilities.TRANSPORT_CELLULAR) ||
                capabilities.hasTransport(NetworkCapabilities.TRANSPORT_ETHERNET)
        } else {
            @Suppress("DEPRECATION")
            cm.activeNetworkInfo?.isConnected == true
        }
    }

    override fun onBackPressed() {
        if (webView.canGoBack()) {
            webView.goBack()
            return
        }
        val now = System.currentTimeMillis()
        if (now - lastBackPressed > EXIT_INTERVAL) {
            lastBackPressed = now
            Toast.makeText(this, R.string.exit_confirm, Toast.LENGTH_SHORT).show()
            return
        }
        super.onBackPressed()
    }

    override fun onConfigurationChanged(newConfig: android.content.res.Configuration) {
        super.onConfigurationChanged(newConfig)
        applyFullScreen()
    }

    /**
     * JS 桥：供网页调用原生能力。
     * 当前仅暴露系统版本与返回键状态，后续可按需扩展。
     */
    class ChoiceBridge(private val context: Context) {
        @JavascriptInterface
        fun getVersion(): String {
            return BuildConfig.VERSION_NAME
        }

        @JavascriptInterface
        fun finish() {
            Handler(Looper.getMainLooper()).post {
                (context as? AppCompatActivity)?.finish()
            }
        }
    }
}
