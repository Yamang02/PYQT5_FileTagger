#!/usr/bin/env python3
"""
테스트용 태그 데이터를 생성하는 스크립트입니다.
현재 디렉토리의 파일들에 샘플 태그를 추가하여 TagInputWidget 기능을 테스트할 수 있도록 합니다.
"""

import os
import sys
from core.tag_manager import TagManager


def generate_test_tags():
    """현재 디렉토리의 파일들에 테스트용 태그를 추가합니다."""

    # 샘플 태그들
    sample_tags = [
        "중요",
        "업무",
        "개인",
        "프로젝트",
        "문서",
        "이미지",
        "비디오",
        "음악",
        "보고서",
        "계획서",
        "회의록",
        "참고자료",
        "템플릿",
        "백업",
        "임시",
        "완료",
        "진행중",
        "검토필요",
        "승인대기",
        "최종",
        "초안",
    ]

    # TagManager 초기화
    tag_manager = TagManager()
    if not tag_manager.connect():
        print("❌ MongoDB 연결 실패")
        return False

    print("✅ MongoDB 연결 성공")

    # 현재 디렉토리의 파일들에 태그 추가
    current_dir = os.path.dirname(os.path.abspath(__file__))
    files_processed = 0

    for filename in os.listdir(current_dir):
        file_path = os.path.join(current_dir, filename)

        # 파일만 처리 (디렉토리 제외)
        if os.path.isfile(file_path):
            # 파일 확장자에 따른 태그 선택
            ext = os.path.splitext(filename)[1].lower()

            if ext in [".py", ".pyc"]:
                tags = ["Python", "코드", "개발"]
            elif ext in [".md", ".txt"]:
                tags = ["문서", "마크다운"]
            elif ext in [".json", ".yaml", ".yml"]:
                tags = ["설정", "JSON", "YAML"]
            elif ext in [".gitignore"]:
                tags = ["Git", "설정"]
            else:
                # 기본 태그
                tags = ["파일", "기타"]

            # 랜덤하게 추가 태그 선택 (1-3개)
            import random

            additional_tags = random.sample(sample_tags, random.randint(1, 3))
            tags.extend(additional_tags)

            # 태그 추가
            if tag_manager.update_tags(file_path, tags):
                print(f"✅ {filename}: {', '.join(tags)}")
                files_processed += 1
            else:
                print(f"❌ {filename}: 태그 추가 실패")

    print(f"\n📊 총 {files_processed}개 파일에 태그 추가 완료")

    # 전체 태그 목록 출력
    all_tags = tag_manager.get_all_unique_tags()
    print(f"📋 전체 태그 목록 ({len(all_tags)}개):")
    for tag in sorted(all_tags):
        print(f"  - {tag}")

    tag_manager.disconnect()
    return True


def clear_test_tags():
    """테스트용 태그를 모두 제거합니다."""
    tag_manager = TagManager()
    if not tag_manager.connect():
        print("❌ MongoDB 연결 실패")
        return False

    print("✅ MongoDB 연결 성공")

    # 모든 태그 데이터 삭제
    try:
        tag_manager.collection.delete_many({})
        print("🗑️ 모든 태그 데이터 삭제 완료")
    except Exception as e:
        print(f"❌ 태그 데이터 삭제 실패: {e}")
        return False

    tag_manager.disconnect()
    return True


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "clear":
        print("🧹 테스트 태그 데이터 삭제 중...")
        clear_test_tags()
    else:
        print("🎯 테스트 태그 데이터 생성 중...")
        generate_test_tags()
