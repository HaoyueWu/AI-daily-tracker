import os
import json
import random
import datetime
import pandas as pd
import concurrent.futures
from typing import List, Dict, Any

def filter_by_rules(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """核心漏斗第一层：规则过滤
    过滤条件：
    1. 没有标题
    2. 发布时间超过 7 天 (168小时)
    """
    filtered_data = []
    now = datetime.datetime.utcnow()
    # 为兼容带时区或无时区的datetime，统一转换为 timestamp 比较
    now_ts = now.timestamp()
    
    for item in data:
        title = item.get("title")
        pub_time = item.get("publish_time")
        
        if not title or title.strip() == "":
            continue
            
        if isinstance(pub_time, datetime.datetime):
            pub_ts = pub_time.timestamp()
            # 大于 7 天 (604800 秒) 过滤掉 (Hugging Face 是持续霸榜的老模型，免除此过滤)
            if item.get("source") == "Hugging Face":
                pass
            elif now_ts - pub_ts > 604800:
                continue
                
        filtered_data.append(item)
        
    return filtered_data

def call_llm(prompt: str) -> str:
    """调用通义千问 API 接口"""
    import openai
    
    # 初始化 OpenAI Client，并配置通义千问的 base_url
    client = openai.OpenAI(
        api_key=os.environ.get("QWEN_API_KEY", ""),
        base_url=os.environ.get("QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
    )
    
    try:
        completion = client.chat.completions.create(
            model="qwen-plus", # 可根据需求调整为 qwen-turbo 或 qwen-max
            messages=[
                {"role": "system", "content": "你是一个资深的 AI 商业情报分析师。请严格按照用户输出要求，返回合法的 JSON 格式。返回时务必只输出 JSON 对象，不要含有任何 markdown 代码块前缀。"},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.3, # 稍微调低温度以保证 JSON 输出的稳定性
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"Error calling Qwen API: {e}")
        # 如果出错，为了保证流程不中断，返回格式化的兜底 JSON
        return json.dumps({
            "results": []
        }, ensure_ascii=False)

def process_batch_with_llm(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """核心漏斗第二/三层：批量大模型智能打分聚类与高维提炼"""
    
    # 构造批量 Prompt
    items_text = ""
    for i, item in enumerate(items):
        items_text += f"""
    [ID: {i}] 标题: {item.get('title')}
    来源: {item.get('source')}
    内容: {item.get('raw_content', '')[:150]}
    """
    
    prompt = f"""
    请作为一名顶级的金融科技商业分析师，批量分析以下 {len(items)} 条 AI 资讯。
    
    {items_text}
    
    输出要求：
    必须返回一个合法的 JSON 对象，包含一个名为 "results" 的 JSON 数组。
    数组中的每个元素对应上面的一条资讯（请严格按照 [ID] 顺序排列），包含以下字段：
    - id (必须是一个整数，对应你在处理的资讯的 ID：0, 1, 2...)
    - core_event (一句话精炼总结这到底是个什么核心客观事件或新产品)
    - business_impact (非常重要！分析其对金融科技落地、企业降本增效、资本流动、或行业竞争格局带来的具体商业影响，需要一针见血)
    - category (必须严格从以下四个赛道中选择其一，并参考以下定义：
        '底层基建': 硬件芯片、算力中心、开源大语言模型发布、主流框架库等技术底座。
        '金融与应用落地': AI在各行各业的具体产品化、SaaS应用发布、B端或C端落地场景。
        '资本创投流向': 定义要非常宽泛！包括但不限于：任何融资事件、收购并购(M&A)、科技巨头战略级商业扩张与结盟、核心高管/顶级大牛的人事跳槽变动、IPO动向、以及商业化盈利里程碑。
        '其他边界探索': 纯学术论文、实验室前沿研究、科幻/AGI哲学讨论等小众杂项。
      )
    - tags (1到2个核心标签，如 "大模型", "RAG", "芯片", "高管变动" 等)
    - business_score (1-10分之间的整数，极其严苛地评估其转化为实际商业收入或改变业务模式的商业潜力，满分为改变时代的级别)
    - heat_score (1-10分之间的整数，评估其在开发者社区或全网的纯技术热度和技术突破重要性)
    
    示例输出格式：
    {{
      "results": [
        {{
          "id": 0,
          "core_event": "OpenAI 推出新型金融分析套件内测",
          "business_impact": "直接威胁现有金融数据终端(如 Bloomberg)的市场份额，能大幅降低投研团队的财报分析人力成本。",
          "category": "金融与应用落地",
          "tags": ["AI 代理", "投研自动化"],
          "business_score": 9,
          "heat_score": 8
        }}
      ]
    }}
    """
    
    llm_response = call_llm(prompt)
    
    # 解析批量返回的 JSON 数组
    results_map = {}
    try:
        data = json.loads(llm_response)
        results = data.get("results", [])
        for r in results:
            if "id" in r:
                results_map[r["id"]] = r
    except json.JSONDecodeError:
        # 尝试从文本中提取 JSON 数组兜底
        try:
            start = llm_response.find("{")
            end = llm_response.rfind("}") + 1
            data = json.loads(llm_response[start:end])
            results = data.get("results", [])
            for r in results:
                if "id" in r:
                    results_map[r["id"]] = r
        except:
            pass
    
    # 将 LLM 结果回填到对应的 item 中
    for i, item in enumerate(items):
        if i in results_map:
            llm_data = results_map[i]
            
            try:
                item["business_score"] = int(float(llm_data.get("business_score", 5)))
                item["heat_score"] = int(float(llm_data.get("heat_score", 5)))
            except (ValueError, TypeError):
                item["business_score"] = 5
                item["heat_score"] = 5
                
            tags_raw = llm_data.get("tags", ["待归类"])
            item["tags"] = tags_raw if isinstance(tags_raw, list) else [tags_raw]
            
            item["core_event"] = llm_data.get("core_event", item.get("title", "暂无摘要"))
            item["business_impact"] = llm_data.get("business_impact", "暂无分析建议。")
            
            cat = llm_data.get("category", "其他边界探索")
            valid_cats = ["底层基建", "金融与应用落地", "资本创投流向", "其他边界探索"]
            item["category"] = cat if cat in valid_cats else "其他边界探索"
            
        else:
            # LLM 返回数量不足时或出错的兜底
            item["business_score"] = 3
            item["heat_score"] = 5
            item["tags"] = ["解析缺失"]
            item["core_event"] = str(item.get("title", ""))[:50]
            item["business_impact"] = "大模型未能成功解析此条目的商业价值。"
            item["category"] = "其他边界探索"
    
    return items

def run_pipeline(raw_data: List[Dict[str, Any]]) -> pd.DataFrame:
    """执行完整的数据清洗与加工流"""
    # 一：规则过滤
    step1_data = filter_by_rules(raw_data)
    
    # 二/三：LLM 批量分析打分与时间衰减算法 (Time Decay)
    # 每 10 条为一批送入大模型，大幅减少 API 调用次数
    BATCH_SIZE = 10
    processed_data = []
    now_dt = datetime.datetime.now()
    
    # 拆分大批次为小批次数组
    batches = [step1_data[i:i + BATCH_SIZE] for i in range(0, len(step1_data), BATCH_SIZE)]
    
    # 启用多线程并发调用大模型 API（设置 10 个以上工作线程以应对网络 I/O 等待）
    all_processed_batches = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        # map 能保证返回结果的顺序和输入的 batches 顺序一致
        all_processed_batches = list(executor.map(process_batch_with_llm, batches))
    
    for processed_batch in all_processed_batches:
        for processed_item in processed_batch:
            b_score = processed_item.get("business_score", 5)
            h_score = processed_item.get("heat_score", 5)
            
            pub_time = processed_item.get("publish_time")
            penalty = 0.0
            if isinstance(pub_time, datetime.datetime):
                delta = now_dt - pub_time
                days_old = max(0, delta.total_seconds() / (24 * 3600))
                penalty = round(days_old * 0.2, 1)
                
            # 综合分数计算 (60% 商用潜力 + 40% 原生极客热度 - 时间惩罚)
            comp_score = (float(b_score) * 0.6) + (float(h_score) * 0.4) - penalty
            comp_score = max(1.0, min(10.0, round(comp_score, 1)))
            
            processed_item["time_penalty"] = penalty
            processed_item["comprehensive_score"] = comp_score
            
            processed_data.append(processed_item)
        
    # 转换为 DataFrame 方便分析与展示
    df = pd.DataFrame(processed_data)
    
    # 确保所需列存在，即使数据为空
    required_cols = [
        "source", "title", "url", "publish_time", "fetch_time", "core_event", 
        "business_impact", "category", "tags", "business_score", "heat_score", "comprehensive_score"
    ]
    for col in required_cols:
        if col not in df.columns:
            df[col] = None
            
    # 按综合分数降序排列
    if not df.empty:
        df = df.sort_values(by="comprehensive_score", ascending=False).reset_index(drop=True)
        
    return df
