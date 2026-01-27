time_travel_summarization extension의 사용법에 대한 README를 작성하려고해(현재 폴더명은 timetravel_dreamai 이지만 time_travel_summarization으로 변경 예정). Extension이 구현하는 프레임워크의 작동 순서대로 각각의 모듈에 대한 설명을 할거야. 모듈 설명은 하는 역할과 사용 방법 위주로 설명할거야. 익스텐션에 포함된 각각의 모듈의 실제 구현 사항과 내가 작성한 내용을 비교 검토하면서 가독성 좋게 다듬어줘.


이 문서는 현재 버전의 TimeTravel Summarization Extension 사용법이다.
해당 익스텐션은 여러 모듈로 구성된 Time Travel Summarization Framework를 구현하며 시계열 궤적 데이터를 활용하여 디지털트윈 기반의 Event-based Summarization을 생성한다. (현재 요약 가능한 event는 '충돌')

Note
- 이 문서에서 Time Travel이란 시간의 흐름에 따라 객체의 위치 상태를 복원하는 기능을 뜻한다(= 과거 상태 복원). 다만 공식적인(교수님 관점) "Time Travel"은 단순한 과거 상태를 복원을 넘어 통합적인 시공간 분석 기능의 통칭을 뜻한다. 즉 해당 Time Travel summarization 프레임워크는 "Time Travel"을 도와주는 하나의 시공간 분석 기능이다.
- 전체 프레임워크의 핵심이 되는 과거 상태 복원 기능을 제공하는 TimeTravel은 core.py, window.py에 구현되었고 이외에 VLM 분석을 도와주는 기능 (view_overlay, vlm_client, event_post_processing)은 각각의 명칭_core.py, 명칭_window.py 에 구현되었다. Extension.py를 통해 통합적으로 초기화된다.
- Movie Capture Extension은 USD Composer에 기본적으로 설치되어있는 Extension이다. 
- Extention의 초기 이름은 netai.timetravel_dreamai 이었다. 따라서 extension ID 는 netai.timetravel_dreamai 이다.

### 사용법
1. 궤적 데이터 생성
utils/trajectory_data_generater_XAI_Studio.py 실행

2. config 설정 (config.py)
- 생성된 궤적 데이터로 "data_path" 설정
- timetravel용 객체 생성에 참조할 USD 파일의 경로 설정. (즉 객체의 모습으로 선택할 USD 파일 지정)

3. Extension Initialization: USD Composer의 Extension창에서 Time_Travel_summarization extension initialization.
- Framework를 구성하는 모듈들의 window UI 초기화. (Time Travel, View overlay, VLS Client, Event Post Processing)

4. Time Travel 모듈: 디지털트윈의 과거 상태 재현 및 수동 탐색
4-1 Time Travel 모듈 기능
- 과거 상태 복원: 시계열 좌표 데이터를 기반으로 astronaut 위치 반영
- time travel 객체 생성: 데이터에 포함된 id의 갯수 만큼 astronaut 생성 및 objid 매핑
- Go to Time: 특정 시점(timestamp)의 과거 상태 재현
- 타임 스크롤: 선형적으로 timestamp 조절
- Play 버튼: 시간의 흐름에 따라 과거 재생 
- Speed: 재생 속도 조절 가능
4-2 구현
- core.py
- window.py 를 통해 Extension의 window UI 구현

5. View Overlay: 복원된 장면에 objectID, Timestamp를 overlay. (View Overlay)
5-1 목적
복원된 디지털트윈
5-2 구현
-view_overlay_core.py 는 overlay logic 담당
-view_overlay_window.py는 UI window 담당.

6. 부분 시각화 및 재생 속도 조절: 디지털트윈 환경 세팅
VLM 추론에 효과적인 영상 데이터를 제공하기 위한 목적이다.
6-1 Visual Abstraction: 디지털트윈 장면의 시각적 복잡도 조절하여 VLM 추론 성능 향상
- Omniverse(USD Composer)의 Stage 창에 '눈' 모양을 선택하여 프림 그룹 단위로 부분적 시각화. (킹렬님이 구조화를 해주셔서 편하게 가능)
- 단계별로 시각화 가능. 논문에서는 Full Digital Twin (전부 시각화), Simplified (Furniture, Equipment 비활성화), Abstract (Furniture, Equipment, A_Exterior 비활성화: View Overlay만 남긴 영상) 로 단계를 나누었음.
6-2 Temporal Acceleration: 디지털트윈 재생 속도를 빠르게하여 VLM 추론 속도를 단축
- 논문의 '충돌' 이벤트 검출에서는 3배속 영상을 사용해도 성능 하락이 나타나지 않았음. 검출하려는 이벤트에 특징에 따라 재생 속도 조절 필요함.
- 적용된 동영상 데이터 생성 방법은 '7. 동영상 추출' 단계에서 설명함

7. 동영상 추출 (Movie Capture Extension)
USD Composer에 기존 설치된 Movie Capture Extension 활용. (Window -> Rendering -> Movie Capture)
이 부분에서 시간적인 병목 현상이 크게 발생함. 
따라서 추후에는 VLM에 영상 전달 방식을 스트리밍으로 확장 필요 (VLM 서버에서 동영상 청킹, 디코딩 등 pipeline 역할을 하는 NVIDIA VSS가 RTSP(real time streaming protocol)를 지원함)
7-1 캡쳐 가이드
- Camera: BEV_cam
- Framerate: 30
- Custom Range: Seconds
-- End: 촬영 결과물에 맞게 설정
-- End 설정 예시: 1분 timespan의 궤적 데이터 기준으로, 1배속 영상 생성시 60초, 3배속 영상 생성시 20초로 설정
-- 이때, 1배속 영상(60초)을 생성하기 위해서는 timetravel 재생속도를 0.33x 해줘야하며, 3배속 영상 (20초) 생성할 때는 timetravel 1x 재생속도로 설정 해야함
-- 그 이유는, movie capture는 Framerate*CustomRange_End 수 만큼의 장면을 default 10FPS로 캡쳐하기 때문에 캡쳐 속도가 느림. (Real time capture 용도가 아니라 그런듯) 즉 1분짜리 영상 캡쳐를 위해 Frame rate을 30, CustomRange_End를 60으로 설정하면, 30x60 장의 이미지를 FPS 10 속도로 촬영함. 결과적으로 3분에 결쳐 촬영이 진행됨. 따라서 재생속도를 0.33으로 늦춰서 재생(시뮬레이션)도 3분동안 진행되도록 설정해야함. 촬영이 끝난 이후 30x60장의 이미지를 인코딩해서 FPS 30 영상을 생성함. 
-- 따라서 Frame rate와 custom range 설정 후, 실제 시뮬레이션 및 렌더링 속도를 조절하여 capture 해야함
-- 1배속 60초 동영상 생성 설정 = (Frame rate: 30, Custom Range: 60, Time Travel play speed: 0.33x)
--- sampling rate가 30FPS. 즉 
-- 3배속 20초 동영상 생성 설정 = (Frame rate: 30, Custom Range: 20, Time Travel play speed: 1x) -> 이 조건으로 생성한 영상이 6-2의 Temporal Acceleration 영상.

- Resolution: 532*280 (변경해도 상관 무)
-- 이 Resolution은 Cosmos-Reason1 의 기본 input resolution config를 따름
-- 빠른 추론속도와 성능을 위하여 2K Vision Token을 유지 (Cosmos-reason1 기준. 모델 마다 토큰 계산 방식이 다름)
-- 참조: https://docs.nvidia.com/vss/latest/content/via_customization.html, [Tuning the Input Vision Token Length for Cosmos-Reason1]
- Output Path: 적당한 경로 설정
- Name: 주의, 동영상 이름은 **video_n** 의 형태 이어야함. VSS 가 해당 이름 형식을 필요로함. 
- 캡쳐 형태: mp4로 설정.

8. VLM Client를 통해 VLM Server에 동영상 전달 및 결과 수신
vlm_output 경로에 VLM 추론 결과 반환됨
8-1 기능
- video: 앞서 생성한 동영상 이름
- Upload 버튼을 통해 업로드. Generate 버튼을 통해 결과 생성 요청 및 반환.
- Model: VLM 서버에서 실행중인 모델의 이름을 선택
- Preset: vlm_client_core.py에 미리 저장해둔 Prompt 선택 (twin_view, simple_view)
-- Twin_view: VLM에 전달되는 동영상을 디지털트윈 기반의 시뮬레이션으로 묘사
-- Simple view: VLM에 전달되는 동영상을 도형의 움직임 수준으로 묘사
8-2 구현
- vlm_client_core.py
- vlm_cleint_window.py

9. Event Post Processing 모듈로 vlm_output을 Event list로 가공
9-1 기능 
- vlm_outputs: VLM이 반환한 json file 명 입력
- Process Events: event_list 경로에 *_eventlist.jsonl 생성
-- intermediate.jsonl (정돈된 vlm 결과값) 을 거쳐 최종 eventlist.jsonl (위치정보 포함) 생성
9-2 구현
- event_post_processing_core.py
- event_post_processing_window.py

10. Time Travel window에서 Event based summary mode 체크박스 선택
play시 event list에 포함된 이벤트를 순회하며 _event_playback_duration 만큼 재생한뒤 다음 이벤트로 이동.
- 각 이벤트의 timestamp에 해당하는 과거 상태를 복원하며, 동시에 해당 이벤트 발생 위치에 해당하는 공간으로 viewport 이동
- core.py의 _event_playback_duration 만큼 재생하고 다음 이벤트로 이동
10-1 기능 (체크박스 선택 된 상태)
- play: Event-based summarization, 이벤트 발생 시공간으로 이동하며 재생
- Next Event 버튼 (Paused 상태): 이벤트 탐색. 버튼을 누르면 다음 이벤트의 발생 직전의 시공간으로 이동.

