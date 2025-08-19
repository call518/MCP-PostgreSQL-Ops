"""
MCP Server Template

이 템플릿은 Model Context Protocol (MCP) 서버를 빠르게 개발하기 위한 기본 구조를 제공합니다.

사용법:
1. SERVER_NAME을 원하는 서버 이름으로 변경
2. 필요한 상수들을 Constants 섹션에 추가
3. 유틸리티 함수들을 Helper Functions 섹션에 구현
4. @mcp.tool() 데코레이터를 사용해서 도구들을 추가

예시:
- 외부 데이터가 필요한 경우: fetch_external_data 함수 참고
- 데이터 포맷팅이 필요한 경우: format_data 함수 참고
"""

import argparse
import logging
import os
import sys
from typing import Any, Optional
from mcp.server.fastmcp import FastMCP
from .functions import fetch_external_data, format_data

# TODO: 필요한 라이브러리들을 여기에 추가하세요
# 예시:
# import httpx          # HTTP 요청
# import sqlite3        # SQLite 데이터베이스
# import json           # JSON 처리

# =============================================================================
# 로깅 설정
# =============================================================================
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# =============================================================================
# 서버 초기화
# =============================================================================
# TODO: "your-server-name"을 실제 서버 이름으로 변경하세요
mcp = FastMCP("your-server-name")

# =============================================================================
# 상수 (Constants)
# =============================================================================
# TODO: 필요한 상수들을 여기에 추가하세요
# 예시:
# API_BASE_URL = "https://api.example.com"
# USER_AGENT = "your-app/1.0"
# DEFAULT_TIMEOUT = 30.0

# 헬퍼 함수들은 src/MCP_NAME/functions.py로 이동했습니다.

# =============================================================================
# MCP 도구들 (Tools)
# =============================================================================
# 
# MCP 도구 작성 가이드라인:
# 1. 도구명은 동사_명사 형태로 명확하게 (예: get_weather, search_files, create_report)
# 2. docstring 필수 구조 (LLM 판단을 위한 핵심 정보):
#    [도구 역할]: 이 도구가 담당하는 핵심 역할을 한 문장으로 명시
#    [정확한 기능]: 구체적으로 수행하는 기능들을 나열
#    [필수 사용 상황]: LLM이 이 도구를 선택해야 하는 명확한 트리거 조건들
#    [절대 사용 금지 상황]: 이 도구를 사용하면 안 되는 상황들
#    [입력 제약 조건]: 매개변수의 형식, 범위, 제약사항
#    Args/Returns: 구체적인 형식과 예시
# 3. 실제 사용자 문구나 키워드를 포함하여 LLM이 정확히 매칭할 수 있도록 작성
# 4. 다른 도구와의 구분을 위해 고유한 역할 영역을 명확히 정의

@mcp.tool()
async def example_tool(parameter: str) -> str:
    """
    [도구 역할]: 사용자의 특정 요청을 처리하여 실시간 데이터를 제공하는 전용 도구
    
    [정확한 기능]: 
    - [구체적인 기능 1]: 예) 외부 API에서 최신 데이터 조회
    - [구체적인 기능 2]: 예) 특정 조건에 따른 데이터 필터링  
    - [구체적인 기능 3]: 예) 결과를 사용자 친화적 형태로 변환
    
    [필수 사용 상황]:
    - 사용자가 "[구체적인 키워드/문구]"를 언급할 때
    - "[특정 데이터 유형]"에 대한 정보 요청 시
    - "[특정 작업]"을 수행해야 할 때
    - 실시간/최신 정보가 반드시 필요한 경우
    
    [절대 사용 금지 상황]:
    - 일반적인 지식 질문 (위키백과 수준의 정보)
    - 단순 계산이나 변환 작업
    - 이미 알려진 정적 정보에 대한 질문
    - 다른 도구의 영역에 속하는 요청
    
    [입력 제약 조건]:
    - parameter는 반드시 [특정 형식]이어야 함
    - 빈 문자열이나 None 값 불허
    - 최대 길이: [구체적 숫자] 문자
    
    Args:
        parameter: [역할 설명] - 처리할 대상을 명시하는 문자열
                  형식: "[구체적 형식 설명]"
                  예시: "파일명.확장자", "YYYY-MM-DD", "사용자ID:12345"
    
    Returns:
        [반환값 역할]: 처리 결과를 구조화된 형태로 제공
        성공 시: "[구체적 성공 형식]"
        실패 시: "오류: [구체적 오류 메시지]"
        데이터 없음: "결과 없음: [구체적 상황 설명]"
    
    TODO: 
    1. [도구 역할] 섹션을 실제 도구의 핵심 역할로 교체
    2. [정확한 기능] 섹션에 구체적인 기능 나열
    3. [필수 사용 상황]을 실제 트리거 조건들로 교체
    4. 실제 비즈니스 로직으로 구현 교체
    """
    # TODO: 실제 로직 구현
    result = f"Processed: {parameter}"
    return result

# TODO: 추가 도구들을 여기에 구현하세요
#
# @mcp.tool()
# async def search_database(query: str, category: str = "all") -> str:
#     """
#     [도구 역할]: 내부 데이터베이스에서 특정 정보를 검색하여 실시간 결과를 제공하는 전용 검색 도구
#     
#     [정확한 기능]:
#     - 키워드 기반 데이터베이스 전문 검색
#     - 카테고리별 필터링 및 정렬
#     - 검색 결과 관련도 순 정렬 및 요약 제공
#     
#     [필수 사용 상황]:
#     - 사용자가 "검색해줘", "찾아줘", "데이터베이스에서" 등을 언급할 때
#     - "최신", "업데이트된", "현재" 정보 요청 시
#     - 특정 레코드나 데이터 조회가 필요할 때
#     - 리스트나 목록 형태의 결과가 필요할 때
#     
#     [절대 사용 금지 상황]:
#     - 일반적인 지식이나 상식 질문
#     - 계산, 변환, 분석 요청
#     - 파일 시스템 관련 작업
#     - 외부 API 호출이 필요한 작업
#     
#     [입력 제약 조건]:
#     - query는 최소 2글자 이상, 최대 100글자
#     - 특수문자는 %, _, - 만 허용
#     - category는 "all", "users", "products", "orders" 중 하나
#     
#     Args:
#         query: [역할: 검색 키워드] 찾고자 하는 정보의 키워드나 문구
#               형식: "문자열 (2-100자)"
#               예시: "Python 튜토리얼", "사용자 관리", "주문 내역"
#         category: [역할: 검색 범위 제한] 검색할 데이터 카테고리
#                  기본값: "all", 허용값: ["all", "users", "products", "orders"]
#     
#     Returns:
#         [반환값 역할]: 검색 결과를 구조화된 리스트 형태로 제공
#         성공 시: "검색 결과 N개:\n1. [제목] - [요약]\n2. ..."
#         결과 없음: "검색 결과가 없습니다: [검색 조건 정리]"
#         오류 시: "검색 오류: [구체적 오류 원인]"
#     """
#     # 여기에 실제 검색 로직 구현
#     return f"검색 결과: {query} (카테고리: {category})"

# =============================================================================
# 서버 실행
# =============================================================================

def validate_config(transport_type: str, host: str, port: int) -> None:
    """서버 설정 검증"""
    if transport_type not in ["stdio", "streamable-http"]:
        raise ValueError(f"Invalid transport type: {transport_type}")
    
    if transport_type == "streamable-http":
        # Host 검증
        if not host:
            raise ValueError("Host is required for streamable-http transport")
        
        # Port 검증
        if not (1 <= port <= 65535):
            raise ValueError(f"Port must be between 1 and 65535, got: {port}")
        
        logger.info(f"Configuration validated for streamable-http: {host}:{port}")
    else:
        logger.info("Configuration validated for stdio transport")


def main(argv: Optional[list] = None) -> None:
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(
        prog="mcp-server", 
        description="MCP Server with configurable transport"
    )
    parser.add_argument(
        "--log-level",
        dest="log_level",
        help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL). Overrides env var if provided.",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
    )
    parser.add_argument(
        "--type",
        dest="transport_type",
        help="Transport type. Default: stdio",
        choices=["stdio", "streamable-http"],
        default="stdio"
    )
    parser.add_argument(
        "--host",
        dest="host",
        help="Host address for streamable-http transport. Default: 127.0.0.1",
        default="127.0.0.1"
    )
    parser.add_argument(
        "--port",
        dest="port",
        type=int,
        help="Port number for streamable-http transport. Default: 8080",
        default=8080
    )
    
    try:
        args = parser.parse_args(argv)
        
        # Determine log level: CLI arg > environment variable > default
        log_level = args.log_level or os.getenv("MCP_LOG_LEVEL", "INFO")
        
        # Set logging level
        numeric_level = getattr(logging, log_level.upper(), None)
        if not isinstance(numeric_level, int):
            raise ValueError(f'Invalid log level: {log_level}')
        
        logger.setLevel(numeric_level)
        logging.getLogger().setLevel(numeric_level)
        
        # Reduce noise from external libraries at DEBUG level
        logging.getLogger("aiohttp.client").setLevel(logging.WARNING)
        logging.getLogger("asyncio").setLevel(logging.WARNING)
        
        if args.log_level:
            logger.info("Log level set via CLI to %s", args.log_level)
        elif os.getenv("MCP_LOG_LEVEL"):
            logger.info("Log level set via environment variable to %s", log_level)
        else:
            logger.info("Using default log level: %s", log_level)

        # 우선순위: CLI 인수 > 환경변수 > 기본값
        transport_type = args.transport_type or os.getenv("FASTMCP_TYPE", "stdio")
        host = args.host or os.getenv("FASTMCP_HOST", "127.0.0.1") 
        port = args.port if args.port != 8080 else int(os.getenv("FASTMCP_PORT", "8080"))
        
        # 설정 검증
        validate_config(transport_type, host, port)
        
        # Transport 모드에 따른 실행
        if transport_type == "streamable-http":
            logger.info(f"Starting MCP server with streamable-http transport on {host}:{port}")
            mcp.run(transport="streamable-http", host=host, port=port)
        else:
            logger.info("Starting MCP server with stdio transport")
            mcp.run(transport='stdio')
            
    except KeyboardInterrupt:
        logger.info("Server shutdown requested by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    """Entrypoint for MCP server.

    Supports optional CLI arguments while remaining backward-compatible 
    with stdio launcher expectations.
    """
    main()