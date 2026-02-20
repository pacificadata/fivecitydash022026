

# start guide (helloworld) :: make sure the streamlit is installed
streamlit hello

# streamlit run:
streamlit run app.py


# When it's done later:
deactivate


# This keeps your system Python safe and avoids future headaches.




=============


!!!!!! IMPORTANT !!!!!

!!!!!!!
MAKE 'venv' folder (virtual env) PER PROJECT
!!!!!!!

EXAMPLE:

my_streamlit_app/
├─ venv/                  # 가상환경
├─ app.py                 # 메인 엔트리
├─ pages/                 # 멀티페이지 앱
│   └─ dashboard.py
├─ data/                  # CSV / parquet / json
│   └─ sales.csv
├─ components/            # UI / 차트 함수
│   └─ kpi_cards.py
├─ utils/                 # 로직 / 헬퍼
│   └─ loaders.py
├─ assets/                # 이미지, 아이콘
│   └─ logo.png
├─ requirements.txt
└─ README.md



The clean, correct fix (recommended)
Option 1: Use a virtual environment (best practice)
python3 -m venv venv
source venv/bin/activate
pip install streamlit


Then run:

streamlit run app.py


When you’re done later:

deactivate


This keeps your system Python safe and avoids future headaches.