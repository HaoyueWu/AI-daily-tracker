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

def process_with_llm(item: Dict[str, Any]) -> Dict[str, Any]:
    """核心漏斗第二/三层：大模型聚类与打分"""
    # 构造 Prompt
    prompt = f"""
    请分析以下 AI 资讯内容，并输出 JSON 格式。
    标题: {item.get('title')}
    来源: {item.get('source')}
    内容: {item.get('raw_content')}
    
    输出要求：
    包含 score (1-10分之间的整数，评估其技术与商业重要性)，tags (1-2个核心标签列表)，summary (一句话中文总结)。
    """
    
    llm_response = call_llm(prompt)
    
    try:
        llm_data = json.loads(llm_response)
        # 强制转换为整数
        try:
            item["score"] = int(float(llm_data.get("score", 0)))
        except (ValueError, TypeError):
            item["score"] = 0
            
        # 兼容 tags 为 string 或 list 结构
        tags_raw = llm_data.get("tags", [])
        item["tags"] = tags_raw if isinstance(tags_raw, list) else [tags_raw]
        item["summary"] = llm_data.get("summary", "解析失败暂无总结")
    except json.JSONDecodeError:
        item["score"] = 0
        item["tags"] = []
        item["summary"] = "JSON 解析失败"
        
    return item

def run_pipeline(raw_data: List[Dict[str, Any]]) -> pd.DataFrame:
    """执行完整的数据清洗与加工流"""
    # 一：规则过滤
    step1_data = filter_by_rules(raw_data)
    
    # 二/三：LLM 分析打分与时间衰减算法 (Time Decay)
    processed_data = []
    now_dt = datetime.datetime.now()
    
    for item in step1_data:
        processed_item = process_with_llm(item)
        base_score = processed_item.get("score", 0)
        
        # 计算时间衰减
        pub_time = processed_item.get("publish_time")
        penalty = 0.0
        if isinstance(pub_time, datetime.datetime):
            delta = now_dt - pub_time
            # 将差距转化为‘天数’
            days_old = max(0, delta.total_seconds() / (24 * 3600))
            # 设定：每衰退 1 天扣 0.2 分 (可保留1位小数)
            penalty = round(days_old * 0.2, 1)
            
        # 计算最终综合分 (最低保底 1 分)
        final_score = max(1.0, round(float(base_score) - penalty, 1))
        
        # 将结构写入数据
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
