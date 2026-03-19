import streamlit as st
import pandas as pd
from data_fetcher import fetch_all
from llm_pipeline import run_pipeline

st.set_page_config(page_title="AI Daily Tracker", page_icon="⚡️", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', system-ui, -apple-system, sans-serif !important;
        background-color: #F8FAFC !important;
    }
    
    /* 彻底重设 Streamlit */
    .block-container {
        padding-top: 2rem !important; 
        padding-bottom: 4rem !important;
        max-width: 1440px !important;
    }
    header {display: none !important;}
    
    /* 侧边栏美化 */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #E2E8F0;
        box-shadow: 10px 0 30px -10px rgba(0,0,0,0.03);
    }
    
    /* 全局组件样式 */
    .dashboard-header {
        font-size: 2.2rem;
        font-weight: 800;
        letter-spacing: -0.03em;
        background: linear-gradient(135deg, #0F172A 0%, #3B82F6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
        line-height: 1.2;
    }
    .dashboard-subtitle {
        color: #64748B;
        font-size: 0.95rem;
        font-weight: 500;
        margin-bottom: 2.5rem;
    }
    
    .section-title {
        font-size: 1.15rem;
        font-weight: 800;
        color: #0F172A;
        margin-top: 2rem;
        margin-bottom: 1.2rem;
        display: flex;
        align-items: center;
        gap: 0.6rem;
    }
    .section-title::before {
        content: "";
        display: block;
        width: 5px;
        height: 18px;
        background: linear-gradient(180deg, #3B82F6, #8B5CF6);
        border-radius: 4px;
    }
    
    /* Figma 卡片主体 */
    .figma-card {
        background: #ffffff;
        border-radius: 14px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -2px rgba(0, 0, 0, 0.05);
        border: 1px solid #F1F5F9;
        margin-bottom: 1.25rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    .figma-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 15px 20px -5px rgba(0, 0, 0, 0.08), 0 6px 8px -4px rgba(0, 0, 0, 0.04);
        border-color: #E2E8F0;
    }
    
    /* 卡片顶部流光强调条 */
    .card-top-accent {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 5px;
        background: linear-gradient(90deg, #3B82F6, #8B5CF6);
        opacity: 0.9;
    }
    .is-top-card .card-top-accent {
        background: linear-gradient(90deg, #F59E0B, #EF4444);
    }
    
    /* 标题与事件 */
    .card-title {
        font-size: 1.05rem;
        font-weight: 700;
        color: #0F172A;
        text-decoration: none;
        line-height: 1.4;
        margin-bottom: 0.6rem;
        display: block;
    }
    .card-title:hover {
        color: #3B82F6;
    }
    
    .card-event {
        font-size: 0.85rem;
        color: #475569;
        line-height: 1.6;
        margin-bottom: 1.15rem;
        font-weight: 500;
    }
    
    /* 商业影响 Callout 框 */
    .impact-callout {
        background: #F8FAFC;
        border-radius: 10px;
        padding: 0.8rem 1rem;
        border: 1px solid #E2E8F0;
        margin-bottom: 1.15rem;
        position: relative;
    }
    .impact-title {
        font-size: 0.75rem;
        font-weight: 800;
        color: #3B82F6;
        margin-bottom: 0.4rem;
        display: flex;
        align-items: center;
        gap: 0.4rem;
    }
    .impact-content {
        font-size: 0.85rem;
        color: #0F172A;
        line-height: 1.5;
        font-weight: 600;
    }
    
    /* 干净去碍眼的评分展示 */
    .metrics-simple-container {
        display: flex;
        align-items: center;
        gap: 0.8rem;
        margin-bottom: 1.15rem;
    }
    .metric-simple-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        background: #F1F5F9;
        border: 1px solid #E2E8F0;
        padding: 0.35rem 0.6rem;
        border-radius: 6px;
    }
    .metric-lbl-cn {
        font-size: 0.75rem;
        font-weight: 600;
        color: #64748B;
    }
    .metric-val {
        font-family: monospace;
        font-weight: 800;
        font-size: 0.95rem;
    }
    
    /* 分数颜色 */
    .score-biz { color: #10B981; }
    .score-tech { color: #8B5CF6; }
    
    /* 底部 Metadata */
    .card-footer {
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-top: 1px dashed #E2E8F0;
        padding-top: 0.8rem;
    }
    .footer-source {
        font-size: 0.75rem;
        font-weight: 600;
        color: #64748B;
        display: flex;
        align-items: center;
        gap: 0.4rem;
        text-transform: uppercase;
        letter-spacing: 0.02em;
    }
    .source-dot {
        width: 6px;
        height: 6px;
        background: linear-gradient(135deg, #3B82F6, #2563EB);
        border-radius: 50%;
    }
    .footer-date {
        font-size: 0.75rem;
        color: #94A3B8;
        font-weight: 500;
    }
    
    .tags-container {
        display: flex;
        flex-wrap: wrap;
        gap: 0.3rem;
    }
    .figma-tag {
        font-size: 0.65rem;
        font-weight: 600;
        color: #3B82F6;
        background: #EFF6FF;
        padding: 0.2rem 0.6rem;
        border-radius: 99px;
    }
    
    /* 归档列表样式 (查看更多) */
    .archive-item {
        background: #ffffff;
        border-radius: 10px;
        padding: 1rem 1.25rem;
        border: 1px solid #E2E8F0;
        margin-bottom: 0.6rem;
        display: flex;
        gap: 1.25rem;
        align-items: center;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .archive-item:hover {
        transform: translateX(4px);
        box-shadow: 0 6px 10px -3px rgba(0, 0, 0, 0.05);
        border-color: #CBD5E1;
    }
    .archive-scores {
        display: flex;
        flex-direction: column;
        gap: 0.3rem;
        flex-shrink: 0;
        width: 65px;
    }
    .archive-score-box {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 6px;
        padding: 0.25rem 0;
        text-align: center;
    }
    .archive-score-val {
        font-size: 0.9rem;
        font-weight: 800;
        font-family: monospace;
        line-height: 1.1;
    }
    .archive-score-lbl {
        font-size: 0.55rem;
        font-weight: 700;
        color: #64748B;
    }
    .archive-content {
        flex: 1;
    }
    .archive-title {
        font-size: 0.95rem;
        font-weight: 700;
        color: #0F172A;
        text-decoration: none;
        margin-bottom: 0.3rem;
        display: block;
        line-height: 1.4;
    }
    .archive-title:hover {
        color: #3B82F6;
    }
    .archive-desc {
        font-size: 0.8rem;
        color: #475569;
        line-height: 1.4;
        margin-bottom: 0.5rem;
    }
    

    /* =========================================
       🔥🔥 无缝适配深色模式 (Dark Mode) 🔥🔥
       ========================================= */
    @media (prefers-color-scheme: dark) {
        html, body, [class*="css"] {
            background-color: #0B1120 !important;
            color: #F8FAFC !important;
        }
        .dashboard-header {
            background: linear-gradient(135deg, #F8FAFC 0%, #93C5FD 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .section-title { color: #F1F5F9 !important; }
        .figma-card, .archive-item {
            background: #1E293B !important;
            border-color: #334155 !important;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
        }
        .card-title, .archive-title { color: #F8FAFC !important; }
        .card-event, .impact-content, .archive-desc { color: #CBD5E1 !important; }
        .card-event strong { color: #E2E8F0 !important; }
        
        .impact-callout {
            background: #0F172A !important;
            border-color: #334155 !important;
        }
        .impact-title { color: #60A5FA !important; }
        
        .metric-simple-badge, .archive-score-box {
            background: #0F172A !important;
            border-color: #334155 !important;
        }
        .metric-lbl-cn, .archive-score-lbl, .footer-source { color: #94A3B8 !important; }
        .metric-val, .archive-score-val { color: #F1F5F9 !important; }
        
        .score-biz { color: #34D399 !important; } /* 绿色变亮 */
        .score-tech { color: #A78BFA !important; } /* 紫色变亮 */
        
        .card-footer { border-top-color: #334155 !important; }
        .figma-tag {
            background: #0F172A !important;
            color: #93C5FD !important;
            border: 1px solid #1E3A8A !important;
        }
        .empty-placeholder {
            background: #1E293B !important;
            border-color: #334155 !important;
        }
        .empty-placeholder h3 { color: #F8FAFC !important; }
        .empty-placeholder p { color: #94A3B8 !important; }
        
        [data-testid="stSidebar"] {
            background-color: #0F172A !important;
            border-right: 1px solid #1E293B !important;
        }
        /* 归档分隔线 */
        .archive-separator {
            color: #F1F5F9 !important;
            border-bottom-color: #334155 !important;
        }
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="dashboard-header">AI Daily Tracker</div>', unsafe_allow_html=True)
st.markdown('<div class="dashboard-subtitle">全网实时追踪与商业价值分析看板</div>', unsafe_allow_html=True)

with st.sidebar:
    st.header("情报控制台")
    st.markdown("启动数据引擎，全网抓取并使用大模型进行商业分析：")
    
    if st.button("同步最新市场情报", type="primary", use_container_width=True):
        with st.spinner("正在抓取全球数据源..."):
            raw_data = fetch_all()
        
        if not raw_data:
            st.error("网络请求失败，未获取到任何数据。")
            st.stop()
            
        with st.spinner("正在执行大模型商业价值评估..."):
            df_result = run_pipeline(raw_data)
            
        st.session_state["df_result"] = df_result
        st.success("情报更新成功。")
        st.rerun()

def build_card_html(row, is_top=False):
    """构建单张新闻卡片的 HTML，彻底避免 Markdown 缩进 Bug"""
    accent_class = "is-top-card" if is_top else ""
    
    try:
        date_str = pd.to_datetime(row['publish_time']).strftime('%m-%d %H:%M')
    except:
        date_str = str(row['publish_time'])[:16]
    
    tags_html = "".join([f'<span class="figma-tag">{str(t).strip()}</span>' for t in row.get('tags', [])])
    
    biz_score = row.get('business_score', 0)
    tech_score = row.get('heat_score', 0)
    
    core_event = row.get('core_event', '')
    business_impact = row.get('business_impact', '')
    source = row.get('source', '')
    title = row.get('title', '')
    url = row.get('url', '#')
    
    html = f"""
    <div class="figma-card {accent_class}">
        <div class="card-top-accent"></div>
        <a href="{url}" target="_blank" class="card-title">{title}</a>
        <div class="card-event"><strong style="color: #0F172A;">核心事件：</strong>{core_event}</div>
        
        <div class="impact-callout">
            <div class="impact-title">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg>
                商业影响预判
            </div>
            <div class="impact-content">{business_impact}</div>
        </div>
        
        <div class="metrics-simple-container">
            <div class="metric-simple-badge">
                <span class="metric-lbl-cn">💼 商业潜力</span>
                <span class="metric-val score-biz">{biz_score}/10</span>
            </div>
            <div class="metric-simple-badge">
                <span class="metric-lbl-cn">🔥 技术热度</span>
                <span class="metric-val score-tech">{tech_score}/10</span>
            </div>
        </div>
        
        <div class="card-footer">
            <div class="tags-container">{tags_html}</div>
            <div style="display:flex; align-items:center; gap: 1rem;">
                <div class="footer-source"><div class="source-dot"></div>{source}</div>
                <div class="footer-date">{date_str}</div>
            </div>
        </div>
    </div>
    """
    # 彻底去除换行以防 Streamlit Markdown parser 的 bug 拦截
    return html.replace('\n', ' ')

def build_empty_card_html():
    """构建用于对齐的空白占位卡片 HTML"""
    html = """
    <div class="figma-card empty-placeholder" style="display:flex; align-items:center; justify-content:center; min-height: 250px; background:#F8FAFC; border: 1px dashed #CBD5E1; box-shadow:none; border-radius:14px;">
        <div style="text-align:center; color:#94A3B8;">
            <div style="font-size:1.5rem; margin-bottom:0.5rem;">✨</div>
            <div style="font-size:0.85rem; font-weight:600;">情报正在赶来</div>
        </div>
    </div>
    """
    return html.replace('\n', ' ')

def build_archive_html(row):
    """构建归档列表项的 HTML"""
    biz_score = row.get('business_score', 0)
    tech_score = row.get('heat_score', 0)
    
    try:
        date_str = pd.to_datetime(row['publish_time']).strftime('%m-%d')
    except:
        date_str = ""
        
    html = f"""
    <div class="archive-item">
        <div class="archive-scores">
            <div class="archive-score-box">
                <div class="archive-score-val score-biz">{biz_score}</div>
                <div class="archive-score-lbl">商业潜力</div>
            </div>
            <div class="archive-score-box">
                <div class="archive-score-val score-tech">{tech_score}</div>
                <div class="archive-score-lbl">技术热度</div>
            </div>
        </div>
        <div class="archive-content">
            <a href="{row['url']}" target="_blank" class="archive-title">{row['title']}</a>
            <div class="archive-desc">{row.get('core_event', '')}</div>
            <div style="display: flex; align-items: center; justify-content: space-between;">
                <div class="footer-source" style="font-size:0.75rem;"><div class="source-dot" style="background:#94A3B8;"></div>{row['source']}</div>
                <div class="footer-date" style="font-size: 0.75rem;">{date_str}</div>
            </div>
        </div>
    </div>
    """
    return html.replace('\n', ' ')

if "df_result" in st.session_state:
    df = st.session_state["df_result"]
    
    # 防御性检测：如果 Streamlit Cloud 网页持久化缓存了旧版的数据格式（缺少 comprehensive_score)
    # 则自动清空脏缓存，要求用户重新抓取
    if "comprehensive_score" not in df.columns:
        del st.session_state["df_result"]
        st.warning("⚠️ 检测到旧版浏览器缓存与新系统不兼容。脏数据已自动清理，请点击左侧重新同步最新情报！")
        st.stop()
        
    # ---------------- 整体概览 TOP 5 ----------------
    st.markdown('<div class="section-title">市场风向标 (Top 5)</div>', unsafe_allow_html=True)
    global_top_5 = df.sort_values(by="comprehensive_score", ascending=False).head(5)
    
    if global_top_5.empty:
        st.info("今日暂无高优情报介入。")
    else:
        # 直接输出拼接好的安全 HTML
        rendered_html = "".join([build_card_html(row, is_top=True) for _, row in global_top_5.iterrows()])
        st.markdown(rendered_html, unsafe_allow_html=True)

    # ---------------- 四大核心赛道 ----------------
    sections = [
        {"category": "金融与应用落地", "title": "金融与商业落地"},
        {"category": "底层基建", "title": "核心底层基建"},
        {"category": "资本创投流向", "title": "资本与创投风向"},
        {"category": "其他边界探索", "title": "前沿与边界探索"}
    ]
    
    for i in range(0, len(sections), 2):
        row_sections = sections[i:i+2]
        cols = st.columns(2, gap="large")
        
        for j, col in enumerate(cols):
            if j < len(row_sections):
                sec = row_sections[j]
                with col:
                    st.markdown(f'<div class="section-title" style="font-size: 1.15rem; margin-top: 1.5rem;">{sec["title"]}</div>', unsafe_allow_html=True)
                    
                    source_df = df[df["category"] == sec["category"]].sort_values(by="comprehensive_score", ascending=False)
                    # 剔除已经在全局 Top 5 里展示过的数据，避免主页内容过多重复
                    source_df = source_df[~source_df.index.isin(global_top_5.index)]
                    top5_in_sec = source_df.head(5) # 主页强制展示每个赛道前 5
                    
                    rendered_html = ""
                    if not top5_in_sec.empty:
                        rendered_html = "".join([build_card_html(row, is_top=False) for _, row in top5_in_sec.iterrows()])
                    
                    # 补充空白补齐 5 个以保证对齐
                    padding_count = 5 - len(top5_in_sec)
                    if padding_count > 0:
                        rendered_html += "".join([build_empty_card_html() for _ in range(padding_count)])
                    
                    st.markdown(rendered_html, unsafe_allow_html=True)

    # ---------------- 深度追踪 / 查看更多 ----------------
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown('<div class="section-title">深度追踪与历史归档</div>', unsafe_allow_html=True)
    
    # 排重，确保主页显示过的不重复出现
    shown_indices = set(global_top_5.index.tolist())
    for sec in sections:
        source_df = df[df["category"] == sec["category"]].sort_values(by="comprehensive_score", ascending=False)
        source_df = source_df[~source_df.index.isin(global_top_5.index)]
        shown_indices.update(source_df.head(5).index.tolist())
    
    remaining_df = df[~df.index.isin(shown_indices)]
    
    if not remaining_df.empty:
        archive_html = ""
        for sec in sections:
            sec_remaining = remaining_df[remaining_df["category"] == sec["category"]].sort_values(by="comprehensive_score", ascending=False)
            if not sec_remaining.empty:
                archive_html += f"<div class='archive-separator' style='font-size:1rem; font-weight:800; color:#0F172A; margin: 2rem 0 1rem 0; padding-bottom: 0.5rem; border-bottom: 2px solid #F1F5F9;'>{sec['title']}</div>"
                archive_html += "".join([build_archive_html(row) for _, row in sec_remaining.iterrows()])
                
        st.markdown(archive_html, unsafe_allow_html=True)
else:
    st.markdown("""
        <div class="empty-placeholder" style="text-align: center; padding: 4rem 2rem; background: white; border-radius: 20px; border: 1px dashed #CBD5E1; margin-top: 2rem;">
            <div style="font-size: 3rem; margin-bottom: 1rem;">🛰️</div>
            <h3 style="color: #0F172A; font-family: 'Plus Jakarta Sans', sans-serif;">等待同步全网情报</h3>
            <p style="color: #64748B; margin-bottom: 2rem;">请点击左侧控制台的「同步最新市场情报」按钮，启动数据抓取与大模型评估任务。</p>
        </div>
    """, unsafe_allow_html=True)
