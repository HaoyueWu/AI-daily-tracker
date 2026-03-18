import os
import json
import random
import datetime
import pandas as pd
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
                {"role": "system", "content": "你是一个 AI 领域的新闻分析师。请严格按照用户输出要求，返回合法的 JSON 格式。返回时除了 JSON 文本不要带有额外的说明字符或 markdown 的 ```json 前缀。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3, # 稍微调低温度以保证 JSON 输出的稳定性
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"Error calling Qwen API: {e}")
        # 如果出错，为了保证流程不中断，返回格式化的兜底 JSON
        return json.dumps({
            "score": 0,
            "tags": ["错误"],
            "summary": "API 调用失败，请检查网络或剩余额度。"
        }, ensure_ascii=False)

def process_batch_with_llm(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """核心漏斗第二/三层：批量大模型聚类与打分（每批最多 10 条）"""
    
    # 构造批量 Prompt
    items_text = ""
    for i, item in enumerate(items):
        items_text += f"""
    [{i+1}] 标题: {item.get('title')}
    来源: {item.get('source')}
    内容: {item.get('raw_content', '')[:150]}
    """
    
    prompt = f"""
    请批量分析以下 {len(items)} 条 AI 资讯，并统一输出一个 JSON 数组。
    
    {items_text}
    
    输出要求：
    返回一个 JSON 数组，每个元素对应上面的一条资讯（按顺序），包含：
    - score (1-10分之间的整数，评估其技术与商业重要性)
    - tags (1-2个核心标签列表)
    - summary (一句话中文总结)
    
    示例输出格式：
    [{{"score": 8, "tags": ["大模型", "开源"], "summary": "xxx"}}, {{"score": 6, "tags": ["工具"], "summary": "yyy"}}]
    """
    
    llm_response = call_llm(prompt)
    
    # 解析批量返回的 JSON 数组
    try:
        results = json.loads(llm_response)
        if not isinstance(results, list):
            results = [results]
    except json.JSONDecodeError:
        # 尝试从文本中提取 JSON 数组
        try:
            start = llm_response.index("[")
            end = llm_response.rindex("]") + 1
            results = json.loads(llm_response[start:end])
        except:
            results = []
    
    # 将 LLM 结果回填到对应的 item 中
    for i, item in enumerate(items):
        if i < len(results):
            llm_data = results[i]
            try:
                item["score"] = int(float(llm_data.get("score", 0)))
            except (ValueError, TypeError):
                item["score"] = 0
            tags_raw = llm_data.get("tags", [])
            item["tags"] = tags_raw if isinstance(tags_raw, list) else [tags_raw]
            item["summary"] = llm_data.get("summary", "暂无总结")
        else:
            # LLM 返回数量不足时的兜底
            item["score"] = 5
            item["tags"] = ["待分析"]
            item["summary"] = item.get("title", "暂无总结")
    
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
    
    for batch_start in range(0, len(step1_data), BATCH_SIZE):
        batch = step1_data[batch_start:batch_start + BATCH_SIZE]
        processed_batch = process_batch_with_llm(batch)
        
        for processed_item in processed_batch:
            base_score = processed_item.get("score", 0)
            
            pub_time = processed_item.get("publish_time")
            penalty = 0.0
            if isinstance(pub_time, datetime.datetime):
                delta = now_dt - pub_time
                days_old = max(0, delta.total_seconds() / (24 * 3600))
                penalty = round(days_old * 0.2, 1)
                
            final_score = max(1.0, round(float(base_score) - penalty, 1))
            
            processed_item["base_score"] = base_score
            processed_item["time_penalty"] = penalty
            processed_item["score"] = final_score
            
            processed_data.append(processed_item)
        
    # 转换为 DataFrame 方便分析与展示
    df = pd.DataFrame(processed_data)
    
    # 确保所需列存在，即使数据为空
    required_cols = ["source", "title", "url", "publish_time", "score", "tags", "summary"]
    for col in required_cols:
        if col not in df.columns:
            df[col] = None
            
    # 按分数降序排列
    if not df.empty:
        df = df.sort_values(by="score", ascending=False).reset_index(drop=True)
        
    return df
