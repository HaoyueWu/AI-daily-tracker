import sys
import pprint
import pandas as pd
from data_fetcher import fetch_all
from llm_pipeline import run_pipeline

def test_pipeline():
    print("=" * 50)
    print("🚀 [1/3] 开始测试数据抓取 (Data Fetching)...")
    print("=" * 50)
    try:
        raw_data = fetch_all()
        print(f"✅ 成功抓取总计 {len(raw_data)} 条原始数据！")
        
        # 统计各平台抓取量
        source_counts = {}
        for item in raw_data:
            source = item.get("source")
            source_counts[source] = source_counts.get(source, 0) + 1
            
        for k, v in source_counts.items():
            print(f"   - {k}: {v} 条")
            
        print("\n查看第一条抓取的数据样本:")
        pprint.pprint(raw_data[0] if raw_data else "No data")
    except Exception as e:
        print(f"❌ 数据抓取阶段发生严重错误: {e}")
        sys.exit(1)

    print("\n" + "=" * 50)
    print("🧠 [2/3] 开始测试大模型漏斗 (LLM Pipeline)...")
    print("=" * 50)
    print("这可能需要 30-60 秒左右的时间，请耐心等待通义 API 返回...\n")
    try:
        # 为了测试速度，我们只取前 5 条数据去跑 LLM，验证链路是否跑通
        test_batch = raw_data[:5]
        print(f"-> 截取其中 {len(test_batch)} 条送入打分漏斗...")
        
        df_result = run_pipeline(test_batch)
        print(f"✅ LLM 处理完成！成功返回 {len(df_result)} 条带标签/评分的数据")
        
    except Exception as e:
        print(f"❌ LLM 处理阶段发生严重错误: {e}")
        sys.exit(1)

    print("\n" + "=" * 50)
    print("📊 [3/3] 验证最终数据结构 (Data Validation)...")
    print("=" * 50)
    
    if df_result.empty:
        print("⚠️ 警告：处理后的 DataFrame 为空，所有数据都被规则或 LLM 过滤掉了！")
    else:
        print("成功转化为 Pandas DataFrame！以下为前 3 条结果：\n")
        # 打印特定的列以检查数据完整性
        print(df_result[['source', 'title', 'business_score', 'heat_score', 'category']].head(3).to_markdown())
        
        print("\n查看第一条解析后的完整结构体:")
        first_result = df_result.iloc[0].to_dict()
        pprint.pprint({k: first_result[k] for k in ["title", "core_event", "business_impact", "category", "tags", "comprehensive_score"]})
        
        print("\n\n🎉 MVP 核心链路全量跑通！Streamlit 前端可安全渲染。")

if __name__ == "__main__":
    test_pipeline()
