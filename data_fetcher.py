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
        story_ids = response.json()[:50]

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

def get_reddit_ai() -> List[Dict[str, Any]]:
    """抓取 Reddit AI 核心社区 (r/singularity, r/MachineLearning) 的 Top 帖子"""
    results = []
    # Reddit JSON needs a custom User-Agent to avoid 429 Too Many Requests
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Safari/537.36)"}
    subreddits = ["singularity", "MachineLearning"]
    
    for sub in subreddits:
        try:
            url = f"https://www.reddit.com/r/{sub}/top.json?t=day&limit=20"
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            for post in data.get("data", {}).get("children", []):
                post_data = post.get("data", {})
                if post_data.get("title") and post_data.get("url"):
                    publish_time = datetime.datetime.fromtimestamp(post_data.get("created_utc", 0))
                    results.append({
                        "source": "Reddit AI",
                        "title": post_data.get("title"),
                        "url": post_data.get("url") if not post_data.get("url").startswith("/r/") else f"https://www.reddit.com{post_data.get('permalink')}",
                        "raw_content": f"[{sub}] Upvotes: {post_data.get('ups', 0)} | Comments: {post_data.get('num_comments', 0)}\n" + (post_data.get("selftext", "")[:200] + "..." if post_data.get("selftext") else ""),
                        "publish_time": publish_time
                    })
        except Exception as e:
            print(f"Error fetching Reddit r/{sub}: {e}")
            
    return results

def get_product_hunt_ai() -> List[Dict[str, Any]]:
    """抓取 Product Hunt 官方的人工智能专区 RSS"""
    results = []
    try:
        url = "https://www.producthunt.com/feed?category=artificial-intelligence"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Safari/537.36)"}
        response = requests.get(url, headers=headers, timeout=25)
        response.raise_for_status()
        
        root = ET.fromstring(response.content)
        
        for item in root.findall('./channel/item')[:25]:
            title = item.find('title')
            desc = item.find('description')
            link = item.find('link')
            pubDate = item.find('pubDate')
            
            title_text = title.text if title is not None and title.text else ""
            desc_text = desc.text if desc is not None and desc.text else ""
            
            try:
                date_str = pubDate.text.strip()
                dt = datetime.datetime.strptime(date_str[5:25], "%d %b %Y %H:%M:%S")
            except:
                dt = datetime.datetime.utcnow()
                
            results.append({
                "source": "Product Hunt",
                "title": title_text,
                "url": link.text if link is not None else "https://www.producthunt.com",
                "raw_content": desc_text[:250] + "...",
                "publish_time": dt
            })
            
    except Exception as e:
        print(f"Error fetching Product Hunt RSS: {e}")
        
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
            if len(results) >= 40:
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

def get_techcrunch_ai() -> List[Dict[str, Any]]:
    """抓取 TechCrunch 官方的人工智能专区 RSS (含大量创投融资事件)"""
    results = []
    try:
        url = "https://techcrunch.com/category/artificial-intelligence/feed/"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Safari/537.36)"}
        response = requests.get(url, headers=headers, timeout=25)
        response.raise_for_status()
        
        root = ET.fromstring(response.content)
        
        import re
        for item in root.findall('./channel/item')[:30]:
            title = item.find('title')
            desc = item.find('description')
            link = item.find('link')
            pubDate = item.find('pubDate')
            
            title_text = title.text if title is not None and title.text else ""
            desc_text = desc.text if desc is not None and desc.text else ""
            desc_clean = re.sub('<[^<]+>', '', desc_text)
            
            try:
                date_str = pubDate.text.strip()
                dt = datetime.datetime.strptime(date_str[5:25], "%d %b %Y %H:%M:%S")
            except:
                dt = datetime.datetime.utcnow()
                
            results.append({
                "source": "TechCrunch",
                "title": title_text,
                "url": link.text if link is not None else "https://techcrunch.com",
                "raw_content": desc_clean[:250] + "...",
                "publish_time": dt
            })
            
    except Exception as e:
        print(f"Error fetching TechCrunch RSS: {e}")
        
    return results

def fetch_all() -> List[Dict[str, Any]]:
    """聚合所有数据源"""
    all_data = []
    all_data.extend(get_hacker_news())
    all_data.extend(get_reddit_ai())
    all_data.extend(get_product_hunt_ai())
    all_data.extend(get_techcrunch_ai())
    all_data.extend(get_36kr_ai_news())
    
    # 记录统一的获取时间 (精确到分)
    fetch_time = datetime.datetime.now()
    for item in all_data:
        item["fetch_time"] = fetch_time
        
    return all_data

if __name__ == "__main__":
    from pprint import pprint
    data = fetch_all()
    print(f"Total items fetched: {len(data)}")
    pprint(data[:2])
