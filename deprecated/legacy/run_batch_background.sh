#!/bin/bash

# 배치 처리 백그라운드 실행 및 로그 확인 스크립트 (서버용)

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 서버 환경 감지
detect_environment() {
    if [ -f /.dockerenv ]; then
        echo "docker_container"
    elif command -v docker-compose &> /dev/null; then
        echo "docker_host"
    elif command -v docker &> /dev/null; then
        echo "docker_available"
    else
        echo "no_docker"
    fi
}

ENV_TYPE=$(detect_environment)

# 함수: 사용법 출력
print_usage() {
    echo -e "${CYAN}🚀 배치 처리 백그라운드 실행 스크립트${NC}"
    echo -e "${CYAN}========================================${NC}"
    echo ""
    echo -e "${GREEN}사용법:${NC}"
    echo -e "  $0 <날짜>                    # 단일 날짜 처리"
    echo -e "  $0 <시작날짜> <종료날짜>        # 기간별 처리 (날짜별 병렬처리)"
    echo ""
    echo -e "${GREEN}예시:${NC}"
    echo -e "  $0 2025-06-15                # 2025-06-15만 처리"
    echo -e "  $0 2025-06-11 2025-06-19     # 2025-06-11~19 병렬 처리"
    echo ""
    echo -e "${YELLOW}⚡ 성능 향상:${NC}"
    echo -e "  • 기간별 처리 시 각 날짜를 병렬로 동시 처리"
    echo -e "  • 9일 기간 처리 시 약 3-5배 빠른 속도"
    echo -e "  • 개별 날짜 내에서도 청크별 병렬처리 적용"
    echo ""
    echo -e "${GREEN}기능:${NC}"
    echo -e "  ✅ 백그라운드 실행 (터미널 종료해도 계속 실행)"
    echo -e "  ✅ 실시간 로그 확인 가능"
    echo -e "  ✅ 진행률 추적"
    echo -e "  ✅ 완료 시 이메일 알림 (설정 시)"
    echo -e "  ✅ 날짜별 병렬처리로 고속 처리"
    echo ""
    echo -e "${BLUE}로그 확인:${NC}"
    echo -e "  실행 후 표시되는 로그 파일 경로를 사용하여 진행상황 확인"
    echo -e "  예: tail -f logs/batch_range_2025-06-11_to_2025-06-19_20250116_143052.log"
    echo ""
}

# 함수: Docker 명령어 생성
get_docker_cmd() {
    local cmd_args="$1"
    
    case $ENV_TYPE in
        "docker_container")
            # 컨테이너 내부에서 실행 중인 경우
            echo "python /app/chat_keyword_batch.py $cmd_args"
            ;;
        "docker_host"|"docker_available")
            # Docker 호스트에서 실행하는 경우
            if command -v docker-compose &> /dev/null; then
                echo "docker-compose exec -T keyword-batch python chat_keyword_batch.py $cmd_args"
            else
                # docker-compose가 없으면 직접 docker 명령 사용
                echo "docker exec -i keyword-batch python chat_keyword_batch.py $cmd_args"
            fi
            ;;
        *)
            echo -e "${RED}❌ Docker 환경을 찾을 수 없습니다.${NC}"
            exit 1
            ;;
    esac
}

# 함수: 백그라운드 배치 실행
run_batch() {
    local start_date=$1
    local end_date=$2
    
    if [ -z "$start_date" ]; then
        echo -e "${RED}❌ 오류: 날짜를 입력해주세요${NC}"
        print_usage
        exit 1
    fi
    
    # 로그 파일명 생성
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local log_file=""
    local cmd_args=""
    
    if [ -n "$end_date" ]; then
        # 기간별 처리
        log_file="logs/batch_range_${start_date}_to_${end_date}_${timestamp}.log"
        cmd_args="--start-date $start_date --end-date $end_date"
        echo -e "${GREEN}🚀 기간별 배치 시작: $start_date ~ $end_date${NC}"
    else
        # 단일 날짜 처리
        log_file="logs/batch_single_${start_date}_${timestamp}.log"
        cmd_args="--target-date $start_date"
        echo -e "${GREEN}🚀 단일 날짜 배치 시작: $start_date${NC}"
    fi
    
    # 로그 디렉토리 확인/생성
    mkdir -p logs
    
    # Docker 컨테이너 상태 확인 (컨테이너 내부가 아닌 경우만)
    if [ "$ENV_TYPE" != "docker_container" ]; then
        echo -e "${BLUE}🔍 Docker 컨테이너 상태 확인...${NC}"
        
        if command -v docker-compose &> /dev/null; then
            if ! docker-compose ps keyword-batch 2>/dev/null | grep -q "Up"; then
                echo -e "${YELLOW}⚠️ keyword-batch 컨테이너가 실행되지 않았습니다. 시작합니다...${NC}"
                docker-compose up -d keyword-batch
                sleep 5
            fi
        else
            # docker-compose가 없는 경우 직접 docker 명령 사용
            if ! docker ps | grep -q keyword-batch; then
                echo -e "${RED}❌ keyword-batch 컨테이너를 찾을 수 없습니다.${NC}"
                echo "수동으로 컨테이너를 시작하거나 docker-compose를 사용해주세요."
                exit 1
            fi
        fi
    fi
    
    # 실행 명령어 생성
    local docker_cmd=$(get_docker_cmd "$cmd_args")
    
    # 백그라운드에서 배치 실행
    echo -e "${BLUE}📝 로그 파일: $log_file${NC}"
    echo -e "${BLUE}🔧 실행 명령: $docker_cmd${NC}"
    
    # 환경에 따라 다른 방식으로 백그라운드 실행
    if [ "$ENV_TYPE" == "docker_container" ]; then
        # 컨테이너 내부에서 직접 실행
        nohup $docker_cmd > "$log_file" 2>&1 &
    else
        # 호스트에서 Docker 명령 실행
        nohup $docker_cmd > "$log_file" 2>&1 &
    fi
    
    local pid=$!
    
    echo -e "${GREEN}✅ 배치가 백그라운드에서 시작되었습니다 (PID: $pid)${NC}"
    echo -e "${BLUE}📊 프로세스 ID를 기록합니다...${NC}"
    echo "$pid" > "logs/batch_${timestamp}.pid"
    
    # 잠시 대기 후 초기 로그 출력
    sleep 3
    echo -e "${YELLOW}📋 초기 로그:${NC}"
    if [ -f "$log_file" ]; then
        tail -15 "$log_file"
    else
        echo "로그 파일이 아직 생성되지 않았습니다. 잠시 후 다시 확인해주세요."
    fi
    
    echo ""
    echo -e "${GREEN}💡 유용한 명령어:${NC}"
    echo "  실시간 로그 확인: $0 logs"
    echo "  또는: tail -f $log_file"
    echo "  배치 중지: $0 stop"
    echo "  상태 확인: $0 status"
}

# 함수: 실시간 로그 확인
show_logs() {
    echo -e "${BLUE}📋 사용 가능한 로그 파일들:${NC}"
    
    if [ ! -d "logs" ]; then
        echo -e "${RED}❌ logs 디렉토리가 없습니다.${NC}"
        exit 1
    fi
    
    # 최근 로그 파일들 목록 출력 (서버 호환성 개선)
    log_files=($(find logs -name "batch_*.log" -type f 2>/dev/null | head -10 | sort -r))
    
    if [ ${#log_files[@]} -eq 0 ]; then
        echo -e "${YELLOW}⚠️ 로그 파일이 없습니다.${NC}"
        echo "먼저 배치를 실행해주세요: $0 run <날짜>"
        exit 1
    fi
    
    echo -e "${YELLOW}최근 로그 파일들:${NC}"
    for i in "${!log_files[@]}"; do
        local file="${log_files[$i]}"
        local size
        local modified
        
        # 서버 호환성을 위한 크기/시간 정보
        if command -v du &> /dev/null; then
            size=$(du -h "$file" 2>/dev/null | cut -f1)
        else
            size="unknown"
        fi
        
        if command -v stat &> /dev/null; then
            # Linux와 macOS 호환성
            if stat -c %y "$file" &>/dev/null; then
                modified=$(stat -c %y "$file" 2>/dev/null | cut -d' ' -f1-2)
            else
                modified=$(stat -f "%Sm" "$file" 2>/dev/null)
            fi
        else
            modified="unknown"
        fi
        
        echo "  $((i+1)). $(basename "$file") (크기: $size, 수정: $modified)"
    done
    
    # 가장 최근 로그 파일 자동 선택
    local latest_log="${log_files[0]}"
    echo ""
    echo -e "${GREEN}📖 가장 최근 로그 파일을 실시간으로 보여줍니다: $(basename "$latest_log")${NC}"
    echo -e "${BLUE}🔄 실시간 로그 (Ctrl+C로 중지):${NC}"
    echo "----------------------------------------"
    
    # 실시간 로그 출력
    tail -f "$latest_log"
}

# 함수: 상태 확인
check_status() {
    echo -e "${BLUE}📊 환경 정보: $ENV_TYPE${NC}"
    
    if [ "$ENV_TYPE" != "docker_container" ]; then
        echo -e "${BLUE}🐳 Docker 컨테이너 상태:${NC}"
        if command -v docker-compose &> /dev/null; then
            docker-compose ps keyword-batch 2>/dev/null || echo "docker-compose 상태 확인 실패"
        else
            docker ps --filter name=keyword-batch 2>/dev/null || echo "Docker 컨테이너 상태 확인 실패"
        fi
    fi
    
    echo ""
    echo -e "${BLUE}🔍 실행 중인 배치 프로세스:${NC}"
    
    # 실행 중인 PID 파일들 확인
    if [ -d "logs" ]; then
        pid_files=($(find logs -name "batch_*.pid" -type f 2>/dev/null))
        
        if [ ${#pid_files[@]} -eq 0 ]; then
            echo -e "${YELLOW}⚠️ 실행 중인 배치가 없습니다.${NC}"
        else
            for pid_file in "${pid_files[@]}"; do
                if [ -f "$pid_file" ]; then
                    local pid=$(cat "$pid_file" 2>/dev/null)
                    if [ -n "$pid" ] && ps -p "$pid" > /dev/null 2>&1; then
                        echo -e "${GREEN}✅ 실행 중: PID $pid ($(basename "$pid_file"))${NC}"
                    else
                        echo -e "${RED}❌ 종료됨: PID $pid ($(basename "$pid_file"))${NC}"
                        # 오래된 PID 파일 정리
                        rm -f "$pid_file"
                    fi
                fi
            done
        fi
    fi
    
    echo ""
    echo -e "${BLUE}📈 최근 로그 파일들:${NC}"
    if [ -d "logs" ]; then
        find logs -name "batch_*.log" -type f 2>/dev/null | head -5 | while read file; do
            if [ -f "$file" ]; then
                local size
                if command -v du &> /dev/null; then
                    size=$(du -h "$file" 2>/dev/null | cut -f1)
                else
                    size="unknown"
                fi
                echo "  $(basename "$file") (크기: $size)"
            fi
        done
    else
        echo -e "${YELLOW}⚠️ logs 디렉토리가 없습니다.${NC}"
    fi
}

# 함수: 배치 중지
stop_batch() {
    echo -e "${YELLOW}🛑 실행 중인 배치 프로세스를 중지합니다...${NC}"
    
    local stopped_count=0
    
    if [ -d "logs" ]; then
        pid_files=($(find logs -name "batch_*.pid" -type f 2>/dev/null))
        
        if [ ${#pid_files[@]} -eq 0 ]; then
            echo -e "${YELLOW}⚠️ 실행 중인 배치가 없습니다.${NC}"
        else
            for pid_file in "${pid_files[@]}"; do
                if [ -f "$pid_file" ]; then
                    local pid=$(cat "$pid_file" 2>/dev/null)
                    if [ -n "$pid" ] && ps -p "$pid" > /dev/null 2>&1; then
                        echo -e "${RED}🛑 프로세스 종료: PID $pid${NC}"
                        kill "$pid" 2>/dev/null
                        sleep 2
                        
                        # 강제 종료가 필요한 경우
                        if ps -p "$pid" > /dev/null 2>&1; then
                            echo -e "${RED}💀 강제 종료: PID $pid${NC}"
                            kill -9 "$pid" 2>/dev/null
                        fi
                        stopped_count=$((stopped_count + 1))
                    fi
                    # PID 파일 제거
                    rm -f "$pid_file"
                fi
            done
            
            if [ $stopped_count -gt 0 ]; then
                echo -e "${GREEN}✅ $stopped_count개 배치 프로세스가 중지되었습니다.${NC}"
            fi
        fi
    fi
    
    # Docker 컨테이너 내부의 Python 프로세스도 확인 (호스트에서만)
    if [ "$ENV_TYPE" != "docker_container" ]; then
        echo -e "${BLUE}🔍 Docker 컨테이너 내부 프로세스 확인...${NC}"
        if command -v docker-compose &> /dev/null; then
            docker-compose exec -T keyword-batch pkill -f "chat_keyword_batch.py" 2>/dev/null || true
        else
            docker exec keyword-batch pkill -f "chat_keyword_batch.py" 2>/dev/null || true
        fi
    fi
}

# 함수: 오래된 로그 파일 정리
cleanup_logs() {
    echo -e "${YELLOW}🧹 로그 파일 정리 시작...${NC}"
    
    if [ ! -d "logs" ]; then
        echo -e "${YELLOW}⚠️ logs 디렉토리가 없습니다.${NC}"
        return
    fi
    
    # 7일 이전 로그 파일 삭제
    local deleted_count=0
    find logs -name "batch_*.log" -type f -mtime +7 2>/dev/null | while read file; do
        echo "  🗑️ 삭제: $(basename "$file")"
        rm -f "$file"
        deleted_count=$((deleted_count + 1))
    done
    
    # 오래된 PID 파일 정리
    find logs -name "batch_*.pid" -type f -mtime +1 2>/dev/null | while read file; do
        rm -f "$file"
    done
    
    echo -e "${GREEN}✅ 로그 정리 완료${NC}"
}

# 메인 로직
case "$1" in
    "run")
        if [ -n "$3" ]; then
            # 기간별 처리: run <start-date> <end-date>
            run_batch "$2" "$3"
        else
            # 단일 날짜 처리: run <target-date>
            run_batch "$2"
        fi
        ;;
    "logs")
        show_logs
        ;;
    "status")
        check_status
        ;;
    "stop")
        stop_batch
        ;;
    "cleanup")
        cleanup_logs
        ;;
    *)
        echo -e "${RED}❌ 알 수 없는 명령어: $1${NC}"
        echo ""
        print_usage
        exit 1
        ;;
esac 