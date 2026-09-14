'use strict';
// 一次性删除 GS→AGI / AGI→GS 整个佣金模块的大块自包含代码（佣金支付管理子模态框、佣金报告）
// 用法: node remove_commission.cjs
const fs = require('fs');
const path = require('path');
const f = path.join(__dirname, 'index.html');
let s = fs.readFileSync(f, 'utf8');
const origLen = s.length;

// ---- 工具：跳过字符串/注释的括号匹配，返回匹配的右括号索引 ----
function matchBrace(text, openIdx) {
  // openIdx 指向 '{'
  let i = openIdx + 1;
  let depth = 1;
  const n = text.length;
  while (i < n) {
    const c = text[i];
    if (c === "'" || c === '"' || c === '`') {
      const q = c;
      i++;
      while (i < n) {
        if (text[i] === '\\') { i += 2; continue; }
        if (text[i] === q) { i++; break; }
        i++;
      }
      continue;
    }
    if (c === '/' && text[i+1] === '/') {
      while (i < n && text[i] !== '\n') i++;
      continue;
    }
    if (c === '/' && text[i+1] === '*') {
      i += 2;
      while (i < n && !(text[i] === '*' && text[i+1] === '/')) i++;
      i += 2;
      continue;
    }
    if (c === '{') depth++;
    else if (c === '}') { depth--; if (depth === 0) return i; }
    i++;
  }
  return -1;
}

function removeFunction(name) {
  const re = new RegExp('function\\s+' + name + '\\s*\\(', 'g');
  let m;
  while ((m = re.exec(s)) !== null) {
    const open = s.indexOf('{', m.index);
    const close = matchBrace(s, open);
    if (close < 0) { console.log('  !! 无法匹配函数 ' + name); break; }
    // 同时删除后续的 window.name=name; 行（若有）
    let end = close + 1;
    // 删除整行（含换行）
    let lineEnd = s.indexOf('\n', end);
    if (lineEnd < 0) lineEnd = s.length;
    // 检查 close 之后是否紧跟 window.name=name;
    const tail = s.slice(close + 1, lineEnd);
    s = s.slice(0, m.index) + '\n' + s.slice(lineEnd);
    re.lastIndex = 0;
  }
}

function removeBetween(startMarker, endMarker, opts) {
  const si = s.indexOf(startMarker);
  if (si < 0) { console.log('  -- 未找到起始标记: ' + startMarker); return; }
  const ei = s.indexOf(endMarker, si + startMarker.length);
  if (ei < 0) { console.log('  -- 未找到结束标记: ' + endMarker); return; }
  const removeEnd = ei + endMarker.length;
  s = s.slice(0, si) + '\n' + s.slice(removeEnd);
}

console.log('=== 删除佣金模块大块代码 ===');

// 1) CommissionModal HTML（id="commissionModal" 的整个 div）
{
  const idIdx = s.indexOf('id="cmMask"');
  if (idIdx >= 0) {
    // 回退找到该 div 的开头 '<div'
    let divStart = s.lastIndexOf('<div', idIdx);
    // 从该 div 开头做 div 深度匹配
    let i = divStart + 4, depth = 1;
    while (i < s.length) {
      if (s[i] === '<' && s[i+1] === 'd' && s[i+2] === 'i' && s[i+3] === 'v' && s[i+4] !== ' ') {
        // 仅统计 <div 与 </div>
      }
      if (s[i] === '<' && s[i+1] === '/' && s[i+2] === 'd' && s[i+3] === 'i' && s[i+4] === 'v') {
        depth--; i += 5; if (depth === 0) { const closeEnd = i; s = s.slice(0, divStart) + '\n' + s.slice(closeEnd); console.log('  ✓ CommissionModal HTML 已删除'); break; }
        continue;
      }
      if (s[i] === '<' && s[i+1] === 'd' && s[i+2] === 'i' && s[i+3] === 'v' && s[i+4] === ' ') { depth++; i += 5; continue; }
      i++;
    }
  } else { console.log('  -- 未找到 CommissionModal HTML'); }
}

// 2) CommissionModal JS IIFE（注释头 → window.CommissionModal= 之后的 })();）
{
  const cmHead = s.indexOf('佣金支付管理 · 子模态框 JS');
  if (cmHead >= 0) {
    const wm = s.indexOf('window.CommissionModal=', cmHead);
    if (wm >= 0) {
      const p = matchBrace(s, wm); // 找到 window.CommissionModal={...} 的 }
      // 再找紧跟的 })();
      let j = s.indexOf('})();', p);
      let end = (j >= 0 ? j + 5 : p + 1);
      s = s.slice(0, cmHead) + '\n' + s.slice(end);
      console.log('  ✓ CommissionModal JS 已删除');
    } else { console.log('  -- 未找到 window.CommissionModal='); }
  } else { console.log('  -- 未找到佣金支付管理 JS 注释头'); }
}

// 3) GS→AGI 佣金报告
removeFunction('openGsCommissionReport');
// 4) AGI→GS 佣金相关函数
removeFunction('openAgiPayModalFromModal');
removeFunction('openAgiPayReportFromModal');
removeFunction('openAgiPayReport');
removeFunction('openAgiPayReportFromMain');

// 5) I18N 键（主 I18N 三语包内的 p3_*/p4_*/gs_rpt_* 及具体键；按"键值对"移除，保留同行的其他键如 p2_note1）
{
  // 匹配形如 , key:"value"  或  key:"value",  的佣金键值对
  const keyPat = '(?:p3_[^:]*|p4_[^:]*|gs_rpt_[^:]*|lbl_gs_view_detail|lbl_agi_view_detail|detail_gs_payment|detail_agi_payment)';
  const reTrail = new RegExp('\\s*,\\s*' + keyPat + ':"[^"]*"', 'g');   // 非首个：连同前导逗号
  const reLead  = new RegExp(keyPat + ':"[^"]*"\\s*,\\s*', 'g');        // 首个：连同尾部逗号
  let removed = 0;
  const lines = s.split('\n');
  const out = [];
  for (let ln of lines) {
    const before = ln;
    ln = ln.replace(reTrail, '').replace(reLead, '');
    if (ln !== before) removed++;
    out.push(ln);
  }
  s = out.join('\n');
  console.log('  ✓ I18N 佣金键值对已清除（影响 ' + removed + ' 行）');
}

fs.writeFileSync(f, s, 'utf8');
console.log('=== 完成 ===');
console.log('文件大小变化: ' + origLen + ' -> ' + s.length + ' (' + (origLen - s.length) + ' 字节已删除)');
