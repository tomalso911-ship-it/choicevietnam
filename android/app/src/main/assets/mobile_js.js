/* AGI-PM mobile runtime patch (injected by MainActivity at onPageFinished)
   Injected at runtime; index.html itself is not modified.
   __AGI_PM_VERSION__ is replaced at runtime with the APK versionName.

   作用：
   1) 把登录页脚的版本号改写为 APK 真实版本（覆盖网页写死的 V2026.09.08.03）。
   2) 包裹 _ovMakeChart：Chart.js 未就绪时的建图请求先排队，等库加载完成再自动重绘，
      彻底解决页面 _ovLoadChartLib 内 2.5s 超时回调在 Chart 未到位时把卡片写成
      永久「图表库加载中…」的问题。
   3) 旋转 / resize 时让 Chart.js 响应式图表重新适应宽度。 */
(function () {
  if (window.__agi_pm_done) return;
  window.__agi_pm_done = true;

  window.__agi_chart_queue = [];

  function flushQueue() {
    if (typeof Chart === 'undefined' || !window.__agi_chart_queue.length) return;
    var q = window.__agi_chart_queue;
    window.__agi_chart_queue = [];
    var fn = window.__agi_real_make_chart || window._ovMakeChart;
    for (var i = 0; i < q.length; i++) {
      try {
        var item = q[i];
        var c = document.getElementById(item.canvasId);
        if (c && c.tagName.toLowerCase() === 'canvas') {
          fn(item.canvasId, item.cfg);
        }
      } catch (e) {}
    }
  }

  function makeWrapper(fn) {
    return function (canvasId, cfg) {
      if (typeof Chart === 'undefined') {
        window.__agi_chart_queue.push({ canvasId: canvasId, cfg: cfg });
        return null;
      }
      try {
        return fn(canvasId, cfg);
      } catch (e) {
        // 布局未稳时重试一次（旋转 / 动态尺寸常见）
        setTimeout(function () {
          try {
            var c = document.getElementById(canvasId);
            if (c && c.tagName.toLowerCase() === 'canvas') fn(canvasId, cfg);
          } catch (e2) {}
        }, 300);
        return null;
      }
    };
  }

  // 1) 登录页脚版本号 → APK 版本
  try {
    var lv = document.getElementById('loginVer');
    if (lv) lv.textContent = '__AGI_PM_VERSION__';
  } catch (e) {}

  // 2) 包裹真实 _ovMakeChart（此时页面已完整解析，函数已定义）
  if (typeof window._ovMakeChart === 'function') {
    window.__agi_real_make_chart = window._ovMakeChart;
    window._ovMakeChart = makeWrapper(window.__agi_real_make_chart);
  }

  // 3) 轮询直到 Chart.js 就绪，再 flush 排队图表
  function pollChartReady() {
    if (typeof Chart !== 'undefined') {
      flushQueue();
    } else {
      setTimeout(pollChartReady, 300);
    }
  }
  pollChartReady();

  // 库加载完成回调里也 flush 一次（双保险）
  if (typeof window._ovLoadChartLib === 'function' && !window._ovLoadChartLib.__agiWrapped) {
    var origLoad = window._ovLoadChartLib;
    window._ovLoadChartLib = function (cb) {
      return origLoad.call(this, function () {
        try { if (typeof cb === 'function') cb(); } catch (e) {}
        setTimeout(flushQueue, 0);
      });
    };
    window._ovLoadChartLib.__agiWrapped = true;
  }

  // 4) 旋转 / resize 处理
  window.addEventListener('orientationchange', function () {
    setTimeout(function () {
      window.dispatchEvent(new Event('resize'));
      if (window._ovCharts && window._ovCharts.length) {
        for (var i = 0; i < window._ovCharts.length; i++) {
          try {
            var ch = window._ovCharts[i];
            if (ch && typeof ch.resize === 'function') ch.resize();
          } catch (e) {}
        }
      }
      flushQueue();
    }, 400);
  });
})();
