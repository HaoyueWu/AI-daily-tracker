import streamlit as st
import pandas as pd
from data_fetcher import fetch_all
from llm_pipeline import run_pipeline

# 设置页面配置，极简宽屏风格
st.set_page_config(page_title="AI Daily Tracker", page_icon="🤖", layout="wide")

# 自定义 CSS 增加美观度
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Noto+Sans+SC:wght@400;500;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', 'Noto Sans SC', sans-serif !important;
    }
    
    /* 弱化 Streamlit 自带的 padding */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    .top-alpha-card {
        padding: 1.5rem;
        border-radius: 12px;
        background-color: var(--secondary-background-color);
        border-left: 5px solid #ff4b4b;
        margin-bottom: 1rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    }
    .tag-badge {
        display: inline-block;
        padding: 0.2rem 0.6rem;
        margin-right: 0.5rem;
        font-size: 0.8rem;
        font-weight: 600;
        color: #ffffff;
        background-color: #1f77b4;
        border-radius: 12px;
    }
    .source-badge {
        font-size: 0.8rem;
        color: var(--text-color);
        opacity: 0.6;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🤖 AI Daily Tracker")
st.markdown("极简、高信噪比的每日 AI 核心资讯聚合平台。经过四大过滤漏斗纯化呈现。")

# 侧边栏
with st.sidebar:
    st.header("操作面板")
    st.markdown("每日定时抓取，或手动点击下方按钮即刻获取：")
    
    if st.button("🚀 一键获取今日 AI 资讯", type="primary"):
        with st.spinner("正在从多源抓取数据..."):
            raw_data = fetch_all()
        
        if not raw_data:
            st.error("未获取到任何数据，请检查网络或 API 接口。")
            st.stop()
            
        with st.spinner("数据清洗中，正在调用 LLM 进行降噪过滤与分析..."):
            # 运行分析处理流
            df_result = run_pipeline(raw_data)
            
        # 将结果存在 session_state 中，避免重绘刷新掉
        st.session_state["df_result"] = df_result
        st.success("数据获取与处理完成！")

# 检查是否有数据已保存在 session_state 当中
if "df_result" in st.session_state:
    df = st.session_state["df_result"]
    
    st.markdown("---")
    
    # 渲染【总榜单】：全网最具影响力的 Top 5
    st.subheader("👑 AI要闻 Top5")
    # 不分源，直接取全局 score 最高的 5 条
    global_top_5 = df.sort_values(by="score", ascending=False).head(5)
    
    if global_top_5.empty:
        st.info("今日暂无内容。")
    else:
        for _, row in global_top_5.iterrows():
            score = row['score']
            tags_html = "".join([f'<span class="tag-badge" style="font-size: 0.9rem; padding: 0.3rem 0.8rem;">{t}</span>' for t in row['tags']])
            
            st.markdown(f"""
                <div class="top-alpha-card" style="border-left: 6px solid #FFD700; padding: 2rem;">
                    <h3 style="margin-bottom: 0.5rem;"><a href="{row['url']}" target="_blank" style="text-decoration:none; color: var(--text-color);">{row['title']}</a></h3>
                    <p style="margin-bottom: 1rem; font-size: 1.25rem; color: var(--text-color); opacity: 0.85; line-height: 1.6; font-weight: 500;">{row['summary']}</p>
                    <div style="margin-top: 1rem;">
                        {tags_html} 
                        <span class="source-badge" style="font-size: 0.95rem;">🎖️ 综合热度: <strong style="color: #e74c3c">{score}</strong>/10 | 🌍 {row['source']} | 🕒 {row['publish_time'].strftime('%m-%d')}</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    
    # 定义四个板块的展示配置项 (已去除英文前缀)
    sections = [
        {"source": "Hacker News", "title": "全球极客视野", "icon": "🌐"},
        {"source": "GitHub", "title": "热门开源动向", "icon": "🐙"},
        {"source": "Hugging Face", "title": "模型趋势先锋", "icon": "🤗"},
        {"source": "36Kr", "title": "国内商业落地跟踪", "icon": "💡"}
    ]
    
    # 将下方板块分组成每行 2 个的形式，实现左右并排布局
    for i in range(0, len(sections), 2):
        row_sections = sections[i:i+2]
        cols = st.columns(2, gap="large") # 建立左右两栏
        
        for j, col in enumerate(cols):
            if j < len(row_sections):
                sec = row_sections[j]
                with col:
                    st.subheader(f"{sec['icon']} {sec['title']}")
                    
                    # 筛选对应源的数据，并按 score 降序（获取最高10条）
                    source_df = df[df["source"] == sec["source"]].sort_values(by="score", ascending=False).head(10)
                    
                    if source_df.empty:
                        st.info(f"今日暂无 {sec['title']} 的高评分内容。")
                    else:
                        for _, row in source_df.iterrows():
                            score = row['score']
                            tags_html = "".join([f'<span class="tag-badge">{t}</span>' for t in row['tags']])
                            
                            st.markdown(f"""
                                <div class="top-alpha-card" style="box-shadow: 0 2px 4px rgba(0,0,0,0.03);">
                                    <h5 style="margin-bottom: 0.5rem; font-weight: 600;"><a href="{row['url']}" target="_blank" style="text-decoration:none; color: var(--text-color);">{row['title']}</a></h5>
                                    <p style="margin-bottom: 0.8rem; font-size: 1rem; color: var(--text-color); opacity: 0.8; line-height: 1.5;">{row['summary']}</p>
                                    <div>
                                        {tags_html} 
                                        <div class="source-badge" style="margin-top: 0.5rem;">🎖️ 综合热度: <strong>{score}</strong>/10 | 🕒 {row['publish_time'].strftime('%m-%d %H:%M') if isinstance(row['publish_time'], pd.Timestamp) else row['publish_time']}</div>
                                    </div>
                                </div>
                            """, unsafe_allow_html=True)
                            
                    st.markdown("<br>", unsafe_allow_html=True)

    # ======== 查看更多：展示未在主页中显示的剩余新闻 ========
    st.markdown("---")
    
    # 收集主页已展示的索引（Top5 + 各板块 Top10）
    shown_indices = set(global_top_5.index.tolist())
    for sec in sections:
        top10 = df[df["source"] == sec["source"]].sort_values(by="score", ascending=False).head(10)
        shown_indices.update(top10.index.tolist())
    
    # 剩余未展示的新闻
    remaining_df = df[~df.index.isin(shown_indices)]
    
    if not remaining_df.empty:
        with st.expander(f"📂 查看更多 )", expanded=False):
            for sec in sections:
                sec_remaining = remaining_df[remaining_df["source"] == sec["source"]].sort_values(by="score", ascending=False)
                
                if sec_remaining.empty:
                    continue
                    
                st.markdown(f"**{sec['icon']} {sec['title']}**")
                
                for _, row in sec_remaining.iterrows():
                    score = row['score']
                    try:
                        date_str = row['publish_time'].strftime('%m-%d %H:%M') if isinstance(row['publish_time'], pd.Timestamp) else str(row['publish_time'])[:16]
                    except:
                        date_str = str(row['publish_time'])[:16]
                    
                    summary_text = row.get('summary', '') or ''
                    st.markdown(f"""
                        <div style="padding: 0.6rem 0.8rem; margin-bottom: 0.5rem; border-radius: 8px; background-color: var(--secondary-background-color);">
                            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                                <a href="{row['url']}" target="_blank" style="text-decoration:none; color: var(--text-color); font-size: 0.85rem; font-weight: 500; flex: 1; min-width: 200px;">{row['title']}</a>
                                <span style="font-size: 0.75rem; color: var(--text-color); opacity: 0.5; white-space: nowrap; margin-left: 1rem;">🎖️ {score}/10 | 🕒 {date_str}</span>
                            </div>
                            <p style="margin: 0.3rem 0 0 0; font-size: 0.78rem; color: var(--text-color); opacity: 0.55; line-height: 1.4;">{summary_text}</p>
                        </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
                
else:
    st.info("👈 请点击左侧面板的「一键获取今日 AI 资讯」按钮启动引擎。")
