import os
import requests
import datetime
import xml.etree.ElementTree as ET
from typing import List, Dict, Any

# 配置系统级代理绕过，防止代理软件阻断国内数据源 (AkShare 使用东方财富网接口)
os.environ["NO_PROXY"] = "eastmoney.com,push2.eastmoney.com,quote.eastmoney.com,127.0.0.1,localhost," + os.environ.get("NO_PROXY", "")

def get_hacker_news() -> List[Dict[str, Any]]:
    """抓取 Hacker News Top 30 的帖子"""
    results = []
    try:
        top_stories_url = "https://hacker-news.firebaseio.com/v0/topstories.json"
        response = requests.get(top_stories_url, timeout=25)
        response.raise_for_status()
        story_ids = response.json()[:30]

        for story_id in story_ids:
            story_url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
            res = requests.get(story_url, timeout=15)
            if res.status_code == 200:
                data = res.json()
                if data and data.get("type") == "story" and data.get("title") and data.get("url"):
                    publish_time = datetime.datetime.fromtimestamp(data.get("time", 0))
                    results.append({
                        "source": "Hacker News",
                        "title": data.get("title"),
                        "url": data.get("url"),
                        "raw_content": f"Score: {data.get('score', 0)}, By: {data.get('by', 'unknown')}",
                        "publish_time": publish_time
                    })
    except Exception as e:
        print(f"Error fetching Hacker News: {e}")
    return results

def get_github_trending() -> List[Dict[str, Any]]:
    """搜索过去24小时内创建的、带 AI/LLM 标签、Star 增长最快的5个项目"""
    results = []
    try:
        # 过去24小时的日期
        yesterday = (datetime.datetime.utcnow() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        # 构造搜索查询
        query = f"created:>{yesterday} topic:ai" # 简化 query 避免 422 错误
        url = "https://api.github.com/search/repositories"
        params = {
            "q": query,
            "sort": "stars",
            "order": "desc",
            "per_page": 20
        }
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"Bearer {os.environ.get('GITHUB_TOKEN', '')}"
        }
        response = requests.get(url, headers=headers, params=params, timeout=25)
        response.raise_for_status()
        data = response.json()

        for item in data.get("items", [])[:20]:
            publish_time = datetime.datetime.strptime(item.get("created_at"), "%Y-%m-%dT%H:%M:%SZ")
            results.append({
                "source": "GitHub",
                "title": item.get("full_name"),
                "url": item.get("html_url"),
                "raw_content": item.get("description") or "No description",
                "publish_time": publish_time
            })
    except Exception as e:
        print(f"Error fetching GitHub repositories: {e}")
    return results

def get_huggingface_trending() -> List[Dict[str, Any]]:
    """抓取每日 Trending 的 Top 10 模型名称和简介"""
    results = []
    try:
        url = "https://huggingface.co/api/models?sort=trendingScore&direction=-1&limit=20"
        response = requests.get(url, timeout=25)
        response.raise_for_status()
        data = response.json()

        now = datetime.datetime.utcnow()
        for item in data:
            try:
                # 尝试抓取模型建档时间 "2026-03-09T05:48:58.000Z"
                created_at_str = item.get("createdAt", "")
                dt = datetime.datetime.strptime(created_at_str[:19].replace("T", " "), "%Y-%m-%d %H:%M:%S")
            except Exception:
                dt = now
                
            results.append({
                "source": "Hugging Face",
                "title": item.get("id"),
                "url": f"https://huggingface.co/{item.get('id')}",
                "raw_content": f"Downloads: {item.get('downloads', 0)}, Pipeline: {item.get('pipeline_tag', 'N/A')}",
                "publish_time": dt
            })
    except Exception as e:
        print(f"Error fetching Hugging Face models: {e}")
    return results

def get_36kr_ai_news() -> List[Dict[str, Any]]:
    """抓取 36氪 官方 RSS 源，过滤出 AI 相关前沿商业跟踪资讯"""
    results = []
    try:
        url = "https://36kr.com/feed"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        response = requests.get(url, headers=headers, timeout=25)
        response.raise_for_status()
        
        # 使用 Python 内置的增量解析 XML (兼容能力强且无需第三方库)
        root = ET.fromstring(response.content)
        
        # 设定的 AI 关键词字典
        keywords = ["AI", "人工智能", "大模型", "算力", "芯片", "机器人", "自动驾驶", "深度学习"]
        now = datetime.datetime.now()
        
        # 在 RSS Channel 内遍历所有文章 item
        for item in root.findall('./channel/item'):
            if len(results) >= 20:
                break
                
            title = item.find('title')
            desc = item.find('description')
            link = item.find('link')
            pubDate = item.find('pubDate')
            
            title_text = title.text if title is not None and title.text else ""
            desc_text = desc.text if desc is not None and desc.text else ""
            
            # 使用简单的关键词双向匹配来筛选相关新闻
            if any(kw in title_text or kw in desc_text for kw in keywords):
                try:
                    date_str = pubDate.text.strip()
                    if date_str[0].isdigit(): # 处理 36Kr 极其特殊的格式: "2026-03-18 14:06:36 +0800"
                        dt = datetime.datetime.strptime(date_str[:19], "%Y-%m-%d %H:%M:%S")
                    else: # 处理标准 RSS 格式如: "Mon, 18 Mar 2026 15:30:00 +0800"
                        dt = datetime.datetime.strptime(date_str[5:25], "%d %b %Y %H:%M:%S")
                except:
                    dt = now
                    
                results.append({
                    "source": "36Kr",
                    "title": title_text[:80] + "..." if len(title_text) > 80 else title_text,
                    "url": link.text if link is not None else "https://36kr.com",
                    "raw_content": desc_text[:250] + "...", # 为防止塞爆 LLM 上下文，截断超长摘要
                    "publish_time": dt
                })
                
    except Exception as e:
        print(f"Error fetching 36Kr RSS: {e}")
        
    return results

def fetch_all() -> List[Dict[str, Any]]:
    """聚合所有数据源"""
    all_data = []
    all_data.extend(get_hacker_news())
    all_data.extend(get_github_trending())
    all_data.extend(get_huggingface_trending())
    all_data.extend(get_36kr_ai_news())
    return all_data

if __name__ == "__main__":
    from pprint import pprint
    data = fetch_all()
    print(f"Total items fetched: {len(data)}")
    pprint(data[:2])
