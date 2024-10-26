# WebRTC 피어 연결 매뉴얼

이 매뉴얼은 `offerer_filetype.py`와 `answerer_filetype.py` 스크립트를 사용하여 파일을 통한 SDP 교환으로 WebRTC 피어 간의 데이터 채널을 설정하고 메시지를 주고받는 방법을 설명합니다.

## 목차

- [WebRTC 피어 연결 매뉴얼](#webrtc-피어-연결-매뉴얼)
  - [목차](#목차)
  - [개요](#개요)
  - [필요한 사전 준비](#필요한-사전-준비)
  - [스크립트 설명](#스크립트-설명)
    - [Offerer 스크립트 (`offerer_filetype.py`)](#offerer-스크립트-offerer_filetypepy)
    - [Answerer 스크립트 (`answerer_filetype.py`)](#answerer-스크립트-answerer_filetypepy)
  - [실행 단계](#실행-단계)
    - [1단계: Offerer 실행](#1단계-offerer-실행)
    - [2단계: Answerer 실행](#2단계-answerer-실행)
    - [3단계: Offerer에서 Answer SDP 설정](#3단계-offerer에서-answer-sdp-설정)
  - [실행 결과 확인](#실행-결과-확인)
  - [문제 해결](#문제-해결)
  - [참고 자료](#참고-자료)

---

## 개요

WebRTC(웹 실시간 통신)는 브라우저나 애플리케이션 간의 실시간 통신을 가능하게 하는 기술입니다. 이 매뉴얼에서는 Python의 `aiortc` 라이브러리를 사용하여 두 피어 간에 데이터 채널을 설정하고 메시지를 주고받는 방법을 설명합니다. SDP(Session Description Protocol) 교환을 파일을 통해 수동으로 수행하여 피어 간 연결을 설정합니다.

## 필요한 사전 준비

- **Python 설치**: Python 3.7 이상이 필요합니다. [Python 다운로드](https://www.python.org/downloads/)
- **aiortc 라이브러리 설치**:
    ```bash
    pip install aiortc
    ```
- **두 개의 터미널 또는 컴퓨터**: 하나는 Offerer 역할을, 다른 하나는 Answerer 역할을 수행합니다.

## 스크립트 설명

### Offerer 스크립트 (`offerer_filetype.py`)

이 스크립트는 WebRTC 연결을 시작하는 Offerer 역할을 수행합니다. 주요 기능은 다음과 같습니다:

- 피어 연결 생성
- 데이터 채널 생성 및 메시지 송신
- Offer SDP 생성 및 파일에 저장
- Answer SDP 파일을 읽어 원격 설명 설정

### Answerer 스크립트 (`answerer_filetype.py`)

이 스크립트는 Offerer의 SDP를 받아들여 응답하는 Answerer 역할을 수행합니다. 주요 기능은 다음과 같습니다:

- 피어 연결 생성
- 데이터 채널 수신 및 메시지 수신/송신
- Offer SDP 파일을 읽어 원격 설명 설정
- Answer SDP 생성 및 파일에 저장

## 실행 단계

### 1단계: Offerer 실행

1. **스크립트 준비**: `offerer_filetype.py`를 원하는 디렉토리에 저장합니다.
2. **Offerer 실행**:
    ```bash
    python offerer_filetype.py
    ```
3. **Offer SDP 생성**: 스크립트가 실행되면 `offer_sdp.txt` 파일이 생성됩니다. 이 파일에는 Offer SDP 정보가 포함됩니다.
4. **Answer SDP 입력 대기**: 스크립트는 `answer_sdp.txt` 파일이 준비될 때까지 대기합니다.

### 2단계: Answerer 실행

1. **스크립트 준비**: `answerer_filetype.py`를 원하는 디렉토리에 저장합니다.
2. **Answerer 실행**:
    ```bash
    python answerer_filetype.py
    ```
3. **Offer SDP 읽기**: Answerer는 `offer_sdp.txt` 파일을 읽어 원격 설명으로 설정합니다.
4. **Answer SDP 생성**: Answer SDP가 생성되어 `answer_sdp.txt` 파일에 저장됩니다.

### 3단계: Offerer에서 Answer SDP 설정

1. **Answer SDP 준비**: Answerer 실행 후 `answer_sdp.txt` 파일이 생성됩니다.
2. **Offerer에 Answer SDP 제공**: Offerer 스크립트의 터미널로 돌아가서 `Enter` 키를 누릅니다. 이는 `answer_sdp.txt` 파일을 읽어 원격 설명으로 설정합니다.
    ```
    Press Enter after putting Answer SDP in 'answer_sdp.txt'...
    ```

## 실행 결과 확인

- **Offerer**:
    - `offer_sdp.txt` 파일이 생성됩니다.
    - Answerer가 메시지를 수신하면 "Received message from Peer B: Hello from Peer B!"가 출력됩니다.

- **Answerer**:
    - `answer_sdp.txt` 파일이 생성됩니다.
    - Offerer가 메시지를 수신하면 "Received message from Peer A: Hello from Peer A!"가 출력됩니다.

- **데이터 채널 메시지**:
    - Offerer가 연결이 열리면 "Hello from Peer A!" 메시지를 전송합니다.
    - Answerer는 해당 메시지를 수신하고 "Hello from Peer B!"로 응답합니다.

## 문제 해결

1. **파일 경로 문제**:
    - 스크립트가 실행되는 디렉토리에 `offer_sdp.txt`와 `answer_sdp.txt` 파일이 있는지 확인하세요.
    - 파일 경로를 절대 경로나 상대 경로로 올바르게 지정했는지 확인하세요.

2. **포트 충돌 또는 방화벽 문제**:
    - 네트워크 설정이 WebRTC 연결을 방해하지 않는지 확인하세요.
    - 필요한 포트가 열려 있는지 확인하세요.

3. **aiortc 설치 오류**:
    - `aiortc` 라이브러리가 제대로 설치되었는지 확인하세요.
    - Python 버전이 호환되는지 확인하세요.

4. **비동기 처리 문제**:
    - 스크립트가 비동기적으로 실행되므로, 올바르게 `asyncio` 이벤트 루프가 동작하는지 확인하세요.

## 참고 자료

- [aiortc 공식 문서](https://aiortc.readthedocs.io/)
- [WebRTC 공식 문서](https://webrtc.org/getting-started/overview)
- [Python asyncio 문서](https://docs.python.org/3/library/asyncio.html)

---

이 매뉴얼을 통해 `offerer_filetype.py`와 `answerer_filetype.py` 스크립트를 사용하여 파일을 통한 SDP 교환으로 WebRTC 데이터 채널을 설정하고 메시지를 주고받을 수 있습니다. 추가적인 질문이나 문제가 발생하면 관련 문서를 참고하거나 커뮤니티 포럼에 문의하세요.