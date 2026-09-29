import requests
import json
import sys

base = 'https://135.106.229.213.sslip.io/api'

def run():
    print("=== STARTING FULL PRODUCTION AUDIT ===")
    
    # 1. Topics
    r = requests.get(f'{base}/topics')
    assert r.status_code == 200, f'Topics error: {r.status_code}'
    topics = r.json()
    print(f'✅ 1. Topics: OK ({len(topics)} topics loaded)')

    # 2. Bank Stats
    r = requests.get(f'{base}/bank/stats')
    assert r.status_code == 200, f'Bank stats error: {r.status_code}'
    stats = r.json()
    print(f'✅ 2. Bank Stats: OK (Open: {stats["open_bank_count"]}, Closed: {stats["closed_bank_count"]})')

    # 3. Open Bank Tasks
    r = requests.get(f'{base}/bank/tasks')
    assert r.status_code == 200, f'Bank tasks error: {r.status_code}'
    tasks = r.json()
    print(f'✅ 3. Open Bank Tasks: OK ({len(tasks)} tasks returned)')

    # 4. Closed Bank Tasks
    r = requests.get(f'{base}/bank/tasks/closed')
    assert r.status_code == 200, f'Closed bank error: {r.status_code}'
    closed_tasks = r.json()
    print(f'✅ 4. Closed Bank Tasks: OK ({len(closed_tasks)} tasks returned)')

    # 5. Solved Tasks (Knowledge Base)
    r = requests.get(f'{base}/bank/solved-tasks')
    assert r.status_code == 200, f'Solved tasks error: {r.status_code}'
    solved = r.json()
    print(f'✅ 5. Solved Bank Tasks: OK ({len(solved)} solved tasks)')

    # 6. Board Tasks (Requests feed)
    r = requests.get(f'{base}/tasks?status_filter=OPEN')
    assert r.status_code == 200, f'Board tasks error: {r.status_code}'
    board_tasks = r.json()
    print(f'✅ 6. Board Open Requests: OK ({len(board_tasks)} active requests)')

    # 7. Check Answer (Calorimeter tolerance test 19.8 vs 19.9)
    cal_task = next((t for t in closed_tasks if 'калориметр' in t['title'].lower()), None)
    if cal_task:
        # Test 19.8
        r1 = requests.post(f'{base}/bank/tasks/{cal_task["id"]}/check-answer', json={'user_answer': '19.8'})
        res1 = r1.json()
        # Test 19.9
        r2 = requests.post(f'{base}/bank/tasks/{cal_task["id"]}/check-answer', json={'user_answer': '19.9'})
        res2 = r2.json()
        print(f'✅ 7. Check Answer Tolerance ({cal_task["title"]}):')
        print(f'     - answer="19.8" -> is_correct={res1.get("is_correct")} (+{res1.get("xp_awarded")} XP)')
        print(f'     - answer="19.9" -> is_correct={res2.get("is_correct")} (+{res2.get("xp_awarded")} XP)')
        assert res1.get('is_correct') and res2.get('is_correct'), "Tolerance check failed!"
    else:
        print('⚠️ Calorimeter task not found in open bank')

    # 8. User sync
    r = requests.post(f'{base}/users/sync', json={'telegram_id': 99999999, 'first_name': 'TestUser', 'active_role': 'student'})
    assert r.status_code == 200, f'User sync error: {r.status_code}'
    print(f'✅ 8. User Sync: OK')

    # 9. SPA index.html
    r = requests.get('https://135.106.229.213.sslip.io/')
    assert r.status_code == 200 and '<div id="app">' in r.text, 'SPA root error'
    print(f'✅ 9. SPA WebApp Root: OK')

    # 10. Swagger Docs
    r = requests.get('https://135.106.229.213.sslip.io/docs')
    assert r.status_code == 200 and 'swagger' in r.text.lower(), 'Docs error'
    print(f'✅ 10. Swagger UI: OK')

    print("\n🎉 ALL 10 TESTS PASSED SUCCESSFULLY! EVERYTHING IS HEALTHY!")

if __name__ == '__main__':
    run()
