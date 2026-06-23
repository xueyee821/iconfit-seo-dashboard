"""Generate static HTML dashboard from latest audit data."""
import json, os, datetime

with open('data/latest.json') as f:
    d = json.load(f)

scores   = d['scores']
gsc      = d['gsc']
ga4      = d['ga4']
tech     = d['technical']
gen_at   = d['generated_at'][:10]

def score_color(s):
    if s >= 70: return '#16a34a'
    if s >= 50: return '#f59e0b'
    return '#ef4444'

def pct_bar(pct, color='#4f46e5'):
    return f'<div style="background:#e5e7eb;border-radius:4px;height:8px;"><div style="background:{color};width:{min(pct,100)}%;height:8px;border-radius:4px;"></div></div>'

# Build keyword rows
kw_rows = ''
for q in gsc['top_queries'][:8]:
    opp = ''
    if q['impressions'] > 100 and q['clicks'] < 5:
        opp = '<span style="background:#fef2f2;color:#ef4444;padding:2px 8px;border-radius:4px;font-size:11px;">大机会</span>'
    elif q['position'] <= 5:
        opp = '<span style="background:#dcfce7;color:#16a34a;padding:2px 8px;border-radius:4px;font-size:11px;">保持</span>'
    else:
        opp = '<span style="background:#fef9c3;color:#ca8a04;padding:2px 8px;border-radius:4px;font-size:11px;">优化</span>'
    kw_rows += f'''<tr style="border-bottom:1px solid #f3f4f6;">
        <td style="padding:7px 8px;font-size:12px;">{q["query"]}</td>
        <td style="text-align:center;padding:7px 8px;font-size:12px;">{q["impressions"]}</td>
        <td style="text-align:center;padding:7px 8px;font-size:12px;font-weight:600;">{q["clicks"]}</td>
        <td style="text-align:center;padding:7px 8px;font-size:12px;">#{q["position"]}</td>
        <td style="text-align:center;padding:7px 8px;">{opp}</td>
    </tr>'''

# Build page rows
page_rows = ''
for p in ga4['top_pages'][:8]:
    bc = '#ef4444' if p['bounce'] > 70 else '#f59e0b' if p['bounce'] > 40 else '#16a34a'
    page_rows += f'''<tr style="border-bottom:1px solid #f3f4f6;">
        <td style="padding:7px 8px;font-size:12px;max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{p["page"]}</td>
        <td style="text-align:center;padding:7px 8px;font-size:12px;">{p["sessions"]}</td>
        <td style="text-align:center;padding:7px 8px;font-size:12px;color:{bc};font-weight:600;">{p["bounce"]}%</td>
        <td style="text-align:center;padding:7px 8px;font-size:12px;">{p["duration"]}s</td>
    </tr>'''

# Channel rows
channel_rows = ''
total_s = ga4['total_sessions'] or 1
for ch in ga4['channels']:
    pct = round(ch['sessions'] / total_s * 100)
    channel_rows += f'''<div style="margin-bottom:10px;">
        <div style="display:flex;justify-content:space-between;font-size:12px;margin-bottom:3px;">
            <span style="font-weight:600;">{ch["channel"]}</span>
            <span style="color:#888;">{ch["sessions"]} 次 · 停留 {ch["duration"]}s · 跳出 {ch["bounce"]}%</span>
        </div>
        {pct_bar(pct)}
    </div>'''

# Tech checks
def check(ok, label):
    icon = '✅' if ok else '❌'
    return f'<div style="display:flex;align-items:center;gap:8px;padding:6px 0;border-bottom:1px solid #f3f4f6;font-size:12px;"><span>{icon}</span><span>{label}</span></div>'

tech_checks = (
    check(not tech['rest_api_exposed'], 'REST API 用户保护（' + ('已保护' if not tech['rest_api_exposed'] else f'{tech["rest_api_users"]}个账号外露') + '）') +
    check(tech['security_headers'] >= 5, f'安全 Headers（{tech["security_headers"]}/5 已设置）') +
    check(not tech['wp_version_exposed'], 'WordPress 版本隐藏') +
    check(not tech['xmlrpc_advertised'], 'xmlrpc.php 已隐藏') +
    check(tech['has_llms_txt'], '/llms.txt 已创建') +
    check(tech['gptbot_allowed'], 'GPTBot 可访问（ChatGPT）') +
    check(tech['claudebot_allowed'], 'ClaudeBot 可访问（Claude AI）')
)

html = f'''<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Iconfit SEO Dashboard</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #f8fafc; color: #1a1a1a; }}
  .container {{ max-width: 900px; margin: 0 auto; padding: 24px 16px; }}
  .card {{ background: white; border-radius: 12px; padding: 20px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,.08); }}
  h1 {{ font-size: 20px; font-weight: 800; }}
  h2 {{ font-size: 14px; font-weight: 700; margin-bottom: 14px; }}
  .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }}
  .grid-4 {{ display: grid; grid-template-columns: repeat(4,1fr); gap: 10px; }}
  .score-big {{ font-size: 36px; font-weight: 800; }}
  .label {{ font-size: 11px; color: #888; }}
  table {{ width: 100%; border-collapse: collapse; }}
  th {{ font-size: 11px; color: #888; font-weight: 600; padding: 5px 8px; text-align: center; border-bottom: 2px solid #f3f4f6; }}
  th:first-child {{ text-align: left; }}
  @media(max-width:600px) {{ .grid-2,.grid-4 {{ grid-template-columns: 1fr; }} }}
</style>
</head>
<body>
<div class="container">

  <!-- Header -->
  <div class="card" style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;">
    <div>
      <h1>Iconfit SEO Dashboard</h1>
      <div class="label" style="margin-top:4px;">iconfit.asia · 数据更新：{gen_at} · 统计周期：过去90天</div>
    </div>
    <div style="text-align:center;">
      <div class="score-big" style="color:{score_color(scores['overall'])};">{scores['overall']}</div>
      <div class="label">/ 100 总评分</div>
    </div>
  </div>

  <!-- Score Cards -->
  <div class="grid-4" style="margin-bottom:16px;">
    {''.join(f"""<div class="card" style="text-align:center;padding:14px;">
      <div style="font-size:24px;font-weight:800;color:{score_color(scores[k])};">{scores[k]}</div>
      <div class="label">{label}</div>
    </div>""" for k,label in [('technical','技术 SEO'),('schema','Schema'),('content','内容质量'),('ai','AI 可见度')])}
  </div>

  <!-- GSC + GA4 Summary -->
  <div class="grid-2">
    <div class="card">
      <h2>搜索表现（GSC）</h2>
      <div class="grid-4" style="margin-bottom:0;">
        <div style="text-align:center;">
          <div style="font-size:22px;font-weight:800;color:#4f46e5;">{gsc["total_clicks"]}</div>
          <div class="label">点击</div>
        </div>
        <div style="text-align:center;">
          <div style="font-size:22px;font-weight:800;color:#4f46e5;">{gsc["total_impressions"]:,}</div>
          <div class="label">曝光</div>
        </div>
        <div style="text-align:center;">
          <div style="font-size:22px;font-weight:800;color:{'#ef4444' if gsc['avg_ctr']<1 else '#16a34a'};">{gsc["avg_ctr"]}%</div>
          <div class="label">CTR</div>
        </div>
        <div style="text-align:center;">
          <div style="font-size:22px;font-weight:800;color:#f59e0b;">#{gsc["avg_position"]}</div>
          <div class="label">平均排名</div>
        </div>
      </div>
    </div>
    <div class="card">
      <h2>网站流量（GA4）</h2>
      <div style="font-size:28px;font-weight:800;color:#4f46e5;margin-bottom:10px;">{ga4["total_sessions"]} <span style="font-size:14px;color:#888;font-weight:400;">次访问</span></div>
      {channel_rows}
    </div>
  </div>

  <!-- Keywords + Pages -->
  <div class="grid-2">
    <div class="card">
      <h2>关键词排名机会（GSC）</h2>
      <table>
        <tr><th style="text-align:left;">关键词</th><th>曝光</th><th>点击</th><th>排名</th><th>状态</th></tr>
        {kw_rows}
      </table>
    </div>
    <div class="card">
      <h2>页面表现（GA4）</h2>
      <table>
        <tr><th style="text-align:left;">页面</th><th>访问</th><th>跳出率</th><th>停留</th></tr>
        {page_rows}
      </table>
    </div>
  </div>

  <!-- Technical Checks -->
  <div class="card">
    <h2>技术健康检查</h2>
    {tech_checks}
  </div>

  <div style="text-align:center;padding:16px;font-size:11px;color:#aaa;">
    每周一自动更新 · 数据来源：Google Search Console + GA4 + 实时技术检测
  </div>

</div>
</body>
</html>'''

os.makedirs('docs', exist_ok=True)
with open('docs/index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("✅ Dashboard generated at docs/index.html")
