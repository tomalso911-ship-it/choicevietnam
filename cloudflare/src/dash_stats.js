// 看板聚合统计接口（2026-09-06）
// 合并 CRM / WON / LOST 的计数与三币汇总，单次返回，
// 避免前端为渲染看板卡片而全量拉取三张表（大幅降低 D1 行读）。
import { getCrmStats } from "./crm.js";
import { getWonStats, getLostStats } from "./wonlost.js";

export async function handleDashStats(request, env, url, pathname) {
  if (pathname !== "/api/dashboard-stats" || request.method !== "GET") return null;
  const username = (
    request.headers.get("X-User-Name") ||
    url.searchParams.get("me") ||
    ""
  ).trim();
  try {
    const [crm, won, lost] = await Promise.all([
      getCrmStats(env, username),
      getWonStats(env, username),
      getLostStats(env, username),
    ]);
    return { body: { ok: true, crm, won, lost }, status: 200 };
  } catch (e) {
    return { body: { ok: false, error: String((e && e.message) || e) }, status: 500 };
  }
}
