#!/usr/bin/env python3
"""
국민연금 가입 사업장 API 문서 변경 감지 및 Slack 알림 스크립트
"""

import hashlib
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# 설정
API_DOC_URL = "https://infuser.odcloud.kr/oas/docs?namespace=15083277/v1"
STATE_FILE = Path(__file__).parent / "last_state.json"
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")


def fetch_api_doc():
    """API 문서를 가져옵니다."""
    try:
        response = requests.get(API_DOC_URL, timeout=30)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"[ERROR] API 문서 가져오기 실패: {e}")
        return None


def load_last_state():
    """이전 상태를 로드합니다."""
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {"hash": None, "content": None, "last_check": None}


def save_state(content_hash, content):
    """현재 상태를 저장합니다."""
    state = {
        "hash": content_hash,
        "content": content,
        "last_check": datetime.now().isoformat()
    }
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def get_content_hash(content):
    """콘텐츠의 해시값을 계산합니다."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def find_changes(old_content, new_content):
    """변경 사항을 찾습니다."""
    if old_content is None:
        return "초기 실행 - 모니터링을 시작합니다."

    try:
        old_json = json.loads(old_content)
        new_json = json.loads(new_content)
    except json.JSONDecodeError:
        return "콘텐츠 변경이 감지되었습니다. (JSON 파싱 실패)"

    changes = []

    # paths 변경 확인 (API 엔드포인트)
    old_paths = set(old_json.get("paths", {}).keys())
    new_paths = set(new_json.get("paths", {}).keys())

    added_paths = new_paths - old_paths
    removed_paths = old_paths - new_paths

    if added_paths:
        changes.append(f"추가된 엔드포인트: {len(added_paths)}개")
        for path in sorted(added_paths)[-5:]:  # 마지막 5개만 표시
            changes.append(f"  + {path}")

    if removed_paths:
        changes.append(f"삭제된 엔드포인트: {len(removed_paths)}개")
        for path in sorted(removed_paths)[-5:]:
            changes.append(f"  - {path}")

    # definitions 변경 확인 (데이터 스키마)
    old_defs = set(old_json.get("definitions", {}).keys())
    new_defs = set(new_json.get("definitions", {}).keys())

    added_defs = new_defs - old_defs
    removed_defs = old_defs - new_defs

    if added_defs:
        changes.append(f"추가된 스키마: {len(added_defs)}개")
        for def_name in sorted(added_defs)[-3:]:
            changes.append(f"  + {def_name}")

    if removed_defs:
        changes.append(f"삭제된 스키마: {len(removed_defs)}개")
        for def_name in sorted(removed_defs)[-3:]:
            changes.append(f"  - {def_name}")

    # info 섹션 변경 확인
    old_info = old_json.get("info", {})
    new_info = new_json.get("info", {})

    if old_info.get("version") != new_info.get("version"):
        changes.append(f"버전 변경: {old_info.get('version')} -> {new_info.get('version')}")

    if not changes:
        changes.append("세부 내용 변경이 감지되었습니다.")

    return "\n".join(changes)


def send_slack_notification(message):
    """Slack으로 알림을 전송합니다."""
    if not SLACK_WEBHOOK_URL:
        print("[ERROR] SLACK_WEBHOOK_URL이 설정되지 않았습니다.")
        return False

    payload = {
        "text": f":bell: *국민연금 가입 사업장 API 문서 변경 감지*\n\n```\n{message}\n```\n\n:link: <{API_DOC_URL}|API 문서 확인하기>",
        "username": "API Monitor Bot",
        "icon_emoji": ":robot_face:"
    }

    try:
        response = requests.post(
            SLACK_WEBHOOK_URL,
            json=payload,
            timeout=10
        )
        response.raise_for_status()
        print("[INFO] Slack 알림 전송 완료")
        return True
    except requests.RequestException as e:
        print(f"[ERROR] Slack 알림 전송 실패: {e}")
        return False


def main():
    print(f"[INFO] API 문서 변경 체크 시작: {datetime.now().isoformat()}")

    # API 문서 가져오기
    content = fetch_api_doc()
    if content is None:
        sys.exit(1)

    # 이전 상태 로드
    last_state = load_last_state()

    # 해시 비교
    current_hash = get_content_hash(content)

    if last_state["hash"] == current_hash:
        print("[INFO] 변경 사항이 없습니다.")
        # 체크 시간만 업데이트
        save_state(current_hash, content)
        return

    print("[INFO] 변경 사항이 감지되었습니다!")

    # 변경 사항 분석
    changes = find_changes(last_state["content"], content)
    print(f"[INFO] 변경 내용:\n{changes}")

    # Slack 알림 전송
    send_slack_notification(changes)

    # 상태 저장
    save_state(current_hash, content)

    print("[INFO] 완료")


if __name__ == "__main__":
    main()
