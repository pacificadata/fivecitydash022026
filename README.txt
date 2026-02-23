

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
├─ venv/                  # Environment
├─ app.py                 # Main Entry
├─ pages/                 # Multi-page app
│   └─ dashboard.py
├─ data/                  # CSV / parquet / json
│   └─ sales.csv
├─ components/            # UI / Chart Func
│   └─ kpi_cards.py
├─ utils/                 # Logic/Helpers
│   └─ loaders.py
├─ assets/                # Images, Icons, etc
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