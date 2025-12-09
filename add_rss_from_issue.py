import os
import yaml
import requests
import re

# 获取环境变量
github_token = os.environ.get('GITHUB_TOKEN')
issue_number = os.environ.get('ISSUE_NUMBER')
repository = os.environ.get('GITHUB_REPOSITORY')

if not all([github_token, issue_number, repository]):
    print("缺少必要的环境变量")
    exit(1)

# GitHub API 基础URL
base_url = f"https://api.github.com/repos/{repository}"
headers = {
    "Authorization": f"token {github_token}",
    "Accept": "application/vnd.github.v3+json"
}

# 1. 获取Issue内容
issue_url = f"{base_url}/issues/{issue_number}"
response = requests.get(issue_url, headers=headers)
if response.status_code != 200:
    print(f"获取Issue内容失败: {response.status_code}")
    exit(1)

issue_data = response.json()
issue_title = issue_data['title']
issue_body = issue_data['body']

# 2. 解析Issue内容，提取网站名称和RSS URL
# 支持两种格式：
# 格式1：网站名称: 示例网站
# RSS URL: https://example.com/feed.xml
# 格式2：直接在标题或正文中包含网站名称和URL

website_name = ""
rss_url = ""

# 尝试解析格式1
website_match = re.search(r'网站名称:\s*(.+)', issue_body, re.IGNORECASE)
rss_match = re.search(r'RSS URL:\s*(.+)', issue_body, re.IGNORECASE)

if website_match and rss_match:
    website_name = website_match.group(1).strip()
    rss_url = rss_match.group(1).strip()
else:
    # 尝试解析格式2，从正文中提取URL
    url_match = re.search(r'(https?://[^\s]+)', issue_body)
    if url_match:
        rss_url = url_match.group(1).strip()
        # 使用Issue标题作为网站名称
        website_name = issue_title.strip()

if not website_name or not rss_url:
    # 如果解析失败，回复并关闭Issue
    comment_url = f"{base_url}/issues/{issue_number}/comments"
    comment_body = "抱歉，无法从您的Issue中提取有效的网站名称和RSS URL。请按照以下格式提交：\n\n网站名称: 示例网站\nRSS URL: https://example.com/feed.xml"
    requests.post(comment_url, json={"body": comment_body}, headers=headers)
    
    # 关闭Issue
    update_url = f"{base_url}/issues/{issue_number}"
    requests.patch(update_url, json={"state": "closed"}, headers=headers)
    
    print("解析Issue内容失败")
    exit(1)

# 3. 读取现有的rss.yaml文件
try:
    with open('rss.yaml', 'r', encoding='utf-8') as f:
        rss_config = yaml.safe_load(f) or {}
except Exception as e:
    print(f"读取rss.yaml失败: {str(e)}")
    exit(1)

# 4. 添加新的RSS源
rss_config[website_name] = {
    "rss_url": rss_url,
    "website_name": website_name
}

# 5. 保存更新后的rss.yaml文件
try:
    with open('rss.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(rss_config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
except Exception as e:
    print(f"保存rss.yaml失败: {str(e)}")
    exit(1)

# 6. 回复Issue，告知用户操作结果
comment_url = f"{base_url}/issues/{issue_number}/comments"
comment_body = f"✅ 已成功添加RSS源！\n\n网站名称: {website_name}\nRSS URL: {rss_url}\n\n该RSS源将从下一次监控开始生效。"
response = requests.post(comment_url, json={"body": comment_body}, headers=headers)
if response.status_code != 201:
    print(f"回复Issue失败: {response.status_code}")
    exit(1)

# 7. 关闭Issue
update_url = f"{base_url}/issues/{issue_number}"
response = requests.patch(update_url, json={"state": "closed"}, headers=headers)
if response.status_code != 200:
    print(f"关闭Issue失败: {response.status_code}")
    exit(1)

print(f"成功添加RSS源: {website_name} - {rss_url}")
print("成功回复并关闭Issue")
