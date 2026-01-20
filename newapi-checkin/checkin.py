#!/usr/bin/env python3
"""NewAPI 单账号签到 CLI"""

import argparse
import json
import sys
import requests


def main():
    parser = argparse.ArgumentParser(description='NewAPI 签到')
    parser.add_argument('--url', required=True, help='站点 URL')
    parser.add_argument('--auth', required=True, help='认证信息 (userId:session)')
    args = parser.parse_args()

    user_id, session = args.auth.split(':', 1)
    url = args.url.rstrip('/')
    headers = {
        'Cookie': f'session={session}',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Cache-Control': 'no-store',
        'new-api-user': user_id,
    }
    result = {'url': url, 'success': False}

    try:
        resp = requests.post(f'{url}/api/user/checkin', headers=headers, timeout=30).json()
        if resp.get('success'):
            result['success'] = True
            result['quota'] = resp.get('data', 0)
        else:
            msg = resp.get('message', '')
            if '已签到' in msg or 'already' in msg.lower():
                result['success'] = True
                result['message'] = '今日已签到'
            else:
                result['error'] = msg
    except Exception as e:
        result['error'] = str(e)

    print(json.dumps(result, ensure_ascii=False))
    sys.exit(0 if result['success'] else 1)


if __name__ == '__main__':
    main()
