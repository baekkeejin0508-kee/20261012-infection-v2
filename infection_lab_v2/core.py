import io,sqlite3,hashlib,os
from pathlib import Path
import pandas as pd
import streamlit as st
DB=Path('/tmp/infection_lab_classroom.sqlite3')
def conn():
 c=sqlite3.connect(DB,timeout=10);c.execute('CREATE TABLE IF NOT EXISTS records (id INTEGER PRIMARY KEY AUTOINCREMENT, learner TEXT, kind TEXT, content TEXT, score INTEGER, created TEXT DEFAULT CURRENT_TIMESTAMP)');c.execute('CREATE TABLE IF NOT EXISTS comments (id INTEGER PRIMARY KEY AUTOINCREMENT, learner TEXT, feedback TEXT, created TEXT DEFAULT CURRENT_TIMESTAMP)');return c
def save(learner,kind,content,score=0):
 with conn() as c:c.execute('INSERT INTO records(learner,kind,content,score) VALUES(?,?,?,?)',(learner,kind,content,score))
def records(learner=None):
 with conn() as c:
  return pd.read_sql_query('SELECT learner,kind,content,score,created FROM records'+ (' WHERE learner=?' if learner else '')+' ORDER BY created DESC',c,params=(learner,) if learner else ())
def comments(learner=None):
 with conn() as c:return pd.read_sql_query('SELECT learner,feedback,created FROM comments'+(' WHERE learner=?' if learner else '')+' ORDER BY created DESC',c,params=(learner,) if learner else ())
def sign_in():
 st.sidebar.header('수업 접속 (시연)')
 who=st.sidebar.text_input('학습자 코드 (가명, 개인정보 금지)',value=st.session_state.get('learner',''),max_chars=20)
 if st.sidebar.button('학생으로 입장'):
  if who.strip():st.session_state['learner']=who.strip();st.session_state['role']='student';st.rerun()
 pin=st.sidebar.text_input('교사 PIN (선택)',type='password')
 if st.sidebar.button('교사 모드'):
  expected=st.secrets.get('TEACHER_PIN',os.environ.get('TEACHER_PIN',''))
  if expected and pin and hashlib.sha256(pin.encode()).digest()==hashlib.sha256(expected.encode()).digest():st.session_state['role']='teacher';st.rerun()
  st.sidebar.error('설정된 교사용 PIN이 일치하지 않습니다.')
 st.sidebar.caption('시연 계정만 사용. 학생 코드는 본인 확인 수단이 아닙니다. 실수업 인증용으로 사용 금지.')
 return st.session_state.get('learner',''),st.session_state.get('role','student')
def load_csv(upload):
 data=upload.getvalue()
 if len(data)>12_000_000:raise ValueError('파일은 12MB 이하만 허용합니다.')
 for encoding in ('utf-8-sig','cp949','euc-kr'):
  try:return pd.read_csv(io.BytesIO(data),encoding=encoding,low_memory=False)
  except UnicodeDecodeError:continue
 raise ValueError('CSV 인코딩을 확인하세요. UTF-8 또는 CP949가 필요합니다.')
def prepare(df,year,disease,value,country,grade):
 selected=[year,disease,value]+([country] if country!='없음' else [])+([grade] if grade!='없음' else [])
 data=df[selected].copy(); names={year:'year',disease:'disease',value:'value'}
 if country!='없음':names[country]='country'
 if grade!='없음':names[grade]='grade'
 data=data.rename(columns=names);data['year']=pd.to_numeric(data['year'].astype(str).str.extract(r'(\d{4})')[0],errors='coerce');data['value']=pd.to_numeric(data['value'].astype(str).str.replace(',','',regex=False),errors='coerce')
 data=data.dropna(subset=['year','value','disease']);data=data[(data.year>=1900)&(data.year<=2100)];data['year']=data['year'].astype(int)
 return data
