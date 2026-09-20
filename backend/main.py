import os,re,certifi
from dotenv import load_dotenv
from fastapi import FastAPI,HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from livekit import api
load_dotenv(); os.environ.setdefault('SSL_CERT_FILE',certifi.where()); os.environ.setdefault('SSL_CERT_DIR',os.path.dirname(certifi.where()))
LIVEKIT_URL=os.getenv('LIVEKIT_URL'); LIVEKIT_API_KEY=os.getenv('LIVEKIT_API_KEY'); LIVEKIT_API_SECRET=os.getenv('LIVEKIT_API_SECRET')
if not LIVEKIT_URL or not LIVEKIT_API_KEY or not LIVEKIT_API_SECRET: raise RuntimeError('LiveKit environment variables are missing')
app=FastAPI(title='Roxstar AI Voice Room')
app.add_middleware(CORSMiddleware,allow_origins=['*'],allow_credentials=True,allow_methods=['*'],allow_headers=['*'])
class TokenRequest(BaseModel): room_name:str; participant_name:str
def valid_room(name): return bool(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,63}',name.strip()))
@app.get('/')
def root(): return {'status':'ok','message':'Roxstar LiveKit Token Server is running'}
@app.post('/token')
async def create_token(request:TokenRequest):
    room_name=request.room_name.strip(); participant_name=request.participant_name.strip()
    if not valid_room(room_name): raise HTTPException(status_code=400,detail='Invalid room name')
    if not participant_name: raise HTTPException(status_code=400,detail='Participant name is required')
    token=(api.AccessToken(LIVEKIT_API_KEY,LIVEKIT_API_SECRET).with_identity(participant_name).with_name(participant_name).with_grants(api.VideoGrants(room_join=True,room=room_name)))
    lkapi=api.LiveKitAPI()
    try:
        dispatch=await lkapi.agent_dispatch.create_dispatch(api.CreateAgentDispatchRequest(agent_name='roxstar-dost',room=room_name))
        print(f'[DISPATCH] {dispatch}')
    except Exception as e:
        print(f'[DISPATCH ERROR] {e}'); raise HTTPException(status_code=500,detail=f'Agent dispatch failed: {e}')
    finally: await lkapi.aclose()
    return {'token':token.to_jwt(),'url':LIVEKIT_URL}
if __name__=='__main__':
    import uvicorn; uvicorn.run(app,host='127.0.0.1',port=8000)
