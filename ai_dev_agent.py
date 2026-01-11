import os
import subprocess
import datetime
import google.generativeai as genai

# ==========================================
# 1. 설정 및 초기화
# ==========================================
# Gemini API 설정 (환경 변수에서 가져옴)
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
gemini_model = genai.GenerativeModel('gemini-1.5-pro')

REPORT_FILE = "dev_report.md"

def log_to_report(title, content):
    """진행 상황을 마크다운 파일에 기록합니다."""
    with open(REPORT_FILE, "a", encoding="utf-8") as f:
        f.write(f"## {title}\n\n")
        f.write(f"**시간:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"```\n{content}\n```\n\n---\n\n")

# ==========================================
# 2. 에이전트 인터페이스
# ==========================================
def ask_claude(prompt):
    """Claude Code CLI를 호출하여 작업을 수행합니다."""
    print(f"[*] Claude 작업 중: {prompt[:50]}...")
    # --yes 플래그는 Claude CLI가 자동으로 작업을 승인하게 함 (버전에 따라 확인 필요)
    cmd = f'claude -p "{prompt}"'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8')
    return result.stdout

def ask_gemini(role, context):
    """Gemini에게 분석 또는 리뷰를 요청합니다."""
    print(f"[*] Gemini {role} 중...")
    prompt = f"당신은 {role}입니다. 다음 맥락을 분석하고 해결책이나 리뷰를 제안하세요.\n\n{context}"
    response = gemini_model.generate_content(prompt)
    return response.text

def run_tests(test_command):
    """작성된 코드에 대해 테스트를 실행합니다."""
    print(f"[*] 테스트 실행 중: {test_command}")
    result = subprocess.run(test_command, shell=True, capture_output=True, text=True, encoding='utf-8')
    return result.returncode == 0, result.stdout + result.stderr

# ==========================================
# 3. 메인 개발 워크플로우
# ==========================================
def main():
    # 리포트 초기화
    if os.path.exists(REPORT_FILE): os.remove(REPORT_FILE)
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write("# AI 에이전트 협업 개발 리포트\n\n")

    # [Step 1] 요구사항 전달
    user_task = "FastAPI를 사용하여 간단한 메모 API를 만들고, pytest로 유닛 테스트 코드까지 작성해줘."
    log_to_report("초기 요구사항", user_task)
    
    claude_code = ask_claude(user_task)
    log_to_report("Claude의 초기 코드 생성", claude_code)

    # [Step 2] Gemini의 코드 리뷰
    review = ask_gemini("시니어 코드 리뷰어", claude_code)
    log_to_report("Gemini의 코드 리뷰 피드백", review)

    # [Step 3] 테스트 자동 실행
    test_cmd = "pytest" # 프로젝트에 맞는 테스트 명령어
    success, test_log = run_tests(test_cmd)
    log_to_report("1차 테스트 결과", test_log)

    # [Step 4] (조건부) 에러 발생 시 자가 치유 루프
    if not success:
        print("[!] 테스트 실패. 디버깅 루프 진입.")
        debug_info = f"테스트 에러 로그:\n{test_log}\n\n관련 코드:\n{claude_code}"
        fix_suggestion = ask_gemini("디버깅 전문가", debug_info)
        log_to_report("Gemini의 에러 분석", fix_suggestion)

        final_fix = ask_claude(f"다음 분석을 바탕으로 코드를 수정하고 테스트를 통과시켜줘: {fix_suggestion}")
        log_to_report("Claude의 최종 수정본", final_fix)
        
        # 재검증
        success, test_log = run_tests(test_cmd)
        log_to_report("최종 테스트 결과", "성공" if success else "실패:\n" + test_log)

    print(f"\n[완료] 모든 과정이 종료되었습니다. '{REPORT_FILE}'을 확인하세요.")

if __name__ == "__main__":
    main()