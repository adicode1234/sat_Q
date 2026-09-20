import io,json
import numpy as np
import pytest,httpx
from PIL import Image
from fastapi.testclient import TestClient
from gateway.app import app
from models import cloud_vision
from models.reliability import water_agreement,apply_answer_gate

@pytest.fixture(autouse=True)
def isolated_cloud(monkeypatch):
    monkeypatch.setattr(cloud_vision,'_key',None);monkeypatch.setattr(cloud_vision,'_enabled',False)
    monkeypatch.setattr(cloud_vision,'_provider','openai')
    monkeypatch.delenv('OPENAI_API_KEY',raising=False)
    monkeypatch.delenv('GEMINI_API_KEY',raising=False)


def test_disagreement_withholds_a_positive_water_prediction():
    a=np.zeros((10,10),bool);b=np.ones_like(a)
    result=water_agreement(a,b,np.ones_like(a))
    assert result['mask_iou']==0 and not result['reliable']


def test_low_trust_cannot_leave_a_direct_river_finding():
    result={'short_answer':'river'};apply_answer_gate(result,{'status':'LOW_TRUST'})
    assert result['short_answer'] is None


def test_settings_block_cross_origin_and_missing_csrf():
    client=TestClient(app,base_url='http://localhost')
    assert client.get('/api/vision/settings',headers={'Origin':'https://evil.example'}).status_code==403
    assert client.post('/api/vision/settings',json={'api_key':'private-secret'*4}).status_code==403
    assert TestClient(app,base_url='http://evil.example').get('/api/vision/settings').status_code==403


def test_key_not_in_status_response_or_setup_html(monkeypatch):
    cloud_vision.configure('private-secret'*4)
    client=TestClient(app,base_url='http://localhost')
    for path in ['/api/vision/settings','/vision-setup']:
        response=client.get(path);assert response.status_code==200 and 'private-secret' not in response.text


def test_settings_validate_then_clear_credentials(monkeypatch):
    async def get(self,url,**kwargs):return httpx.Response(200,json={'id':'gpt-4.1'})
    monkeypatch.setattr(httpx.AsyncClient,'get',get)
    client=TestClient(app,base_url='http://localhost');token=client.get('/api/vision/settings').json()['csrf_token'];headers={'X-SatQuery-CSRF':token}
    response=client.post('/api/vision/settings',headers=headers,json={'api_key':'private-secret'*4,'enabled':True})
    assert response.status_code==200 and response.json()['enabled']
    assert 'private-secret' not in response.text
    assert client.post('/api/vision/settings',headers=headers,json={'enabled':False}).json()['enabled'] is False


def test_real_upload_routes_to_cloud_without_local_fake_mask(monkeypatch):
    cloud_vision.configure('private-secret'*4)
    captured={}
    def post(url,**kwargs):
        captured.update(kwargs['json'])
        text=json.dumps({'answer':'Large rectangular roof structures and surrounding vegetation are visible. No river is clearly identifiable.','image_type':'annotated map screenshot','visible_features':['Rectangular roof structures','Vegetation'],'uncertainties':['Roof purpose cannot be established.'], 'detections':[{'image_id':'img1','label':'Building','box':[.1,.2,.4,.6]}]})
        return httpx.Response(200,json={'status':'completed','id':'mock-response','output':[{'type':'message','content':[{'type':'output_text','text':text}]}]})
    monkeypatch.setattr(httpx,'post',post)
    buffer=io.BytesIO();Image.fromarray(np.random.default_rng(1).integers(0,255,(64,64,3),dtype='uint8')).save(buffer,format='PNG')
    client=TestClient(app,base_url='http://localhost');response=client.post('/api/analyze',files={'images':('map.png',buffer.getvalue(),'image/png')},data={'query':'Where is the river?','scenario':'SINGLE','options':'[{}]'})
    assert response.status_code==200,response.text
    data=response.json();assert data['interpretation_source']=='openai'
    assert data['overlay'] is None and data['composition']=={} and data['short_answer'] is None
    assert data['spatial_overlays'][0]['image_id'] == 'img1'
    assert data['spatial_overlays'][0]['data'] == [{'label': 'Building', 'box': [.1,.2,.4,.6]}]
    assert data['scene_inventory']['composition'] == {}
    assert data['absent'] == []
    assert all('%' not in item['detail'] for item in data['present'])
    assert data['confidence_breakdown']['neural'] is None
    assert data['decision']['status']=='VISUAL_INTERPRETATION'
    assert not captured.get('store')
    assert captured['input'][0]['content'][2]['type']=='input_image'
    assert 'private-secret' not in response.text


def test_provider_failure_is_explicit_without_key_leak(monkeypatch):
    from gateway.errors import InputError
    cloud_vision.configure('private-secret'*4)
    monkeypatch.setattr(httpx,'post',lambda *a,**kw:httpx.Response(429,json={'error':'private-secret'}))
    monkeypatch.setattr(cloud_vision,'payload',lambda *a:{})
    with pytest.raises(InputError,match='quota') as e:cloud_vision.analyze({},'describe')
    assert 'private-secret' not in str(e.value)


def test_gemini_upload_uses_google_and_real_image_payload(monkeypatch):
    cloud_vision.configure('test-google-credential'*2,provider='gemini',model='gemini-2.5-flash')
    def post(url,**kwargs):
        assert url=='https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent'
        assert kwargs['headers']=={'x-goog-api-key':'test-google-credential'*2}
        request=kwargs['json']
        assert request['contents'][0]['parts'][2]['inlineData']['mimeType']=='image/png'
        assert request['generationConfig']['responseMimeType']=='application/json'
        output={'answer':'Buildings and vegetation are visible.','image_type':'aerial image','visible_features':['Buildings'],'uncertainties':['Purpose uncertain.']}
        return httpx.Response(200,json={'responseId':'google-mock','candidates':[{'finishReason':'STOP','content':{'parts':[{'text':json.dumps(output)}]}}]})
    monkeypatch.setattr(httpx,'post',post)
    buffer=io.BytesIO();Image.fromarray(np.zeros((64,64,3),dtype='uint8')).save(buffer,format='PNG')
    response=TestClient(app,base_url='http://localhost').post('/api/analyze',files={'images':('map.png',buffer.getvalue(),'image/png')},data={'query':'Describe image','scenario':'SINGLE','options':'[{}]'})
    assert response.status_code==200,response.text
    result=response.json()
    assert result['interpretation_source']=='gemini' and result['provenance']['provider']=='Google Gemini'
    assert result['overlay'] is None and result['composition']=={}


def test_gemini_setup_and_provider_mismatch(monkeypatch):
    captured=[]
    async def get(self,url,**kwargs):
        captured.append(url)
        assert 'generativelanguage.googleapis.com' in url
        assert 'x-goog-api-key' in kwargs['headers']
        return httpx.Response(200,json={'name':'models/gemini-2.5-flash'})
    monkeypatch.setattr(httpx.AsyncClient,'get',get)
    client=TestClient(app,base_url='http://localhost')
    headers={'X-SatQuery-CSRF':client.get('/api/vision/settings').json()['csrf_token']}
    key='AIza'+'test-only-placeholder'*2
    assert client.post('/api/vision/settings',headers=headers,json={'provider':'openai','api_key':key}).status_code==400
    assert not captured
    response=client.post('/api/vision/settings',headers=headers,json={'provider':'gemini','api_key':key})
    assert response.status_code==200 and response.json()['provider_id']=='gemini'
    assert key not in response.text


def test_gemini_blocked_response_is_not_a_finding(monkeypatch):
    from gateway.errors import InputError
    cloud_vision.configure('test-google-credential'*2,provider='gemini')
    monkeypatch.setattr(cloud_vision,'payload',lambda *args:{'input':[{'content':[]}]})
    monkeypatch.setattr(httpx,'post',lambda *args,**kw:httpx.Response(200,json={'candidates':[]}))
    with pytest.raises(InputError,match='blocked or incomplete'):cloud_vision.analyze({},'describe')


def test_ollama_not_running_raises_clear_error(monkeypatch):
    from gateway.errors import InputError
    cloud_vision.configure(None, provider='ollama', model='llama3.2-vision')
    monkeypatch.setattr(cloud_vision, 'is_ollama_running', lambda *a, **kw: False)
    assert not cloud_vision.enabled()
    with pytest.raises(InputError, match='Ollama server start karo'):
        cloud_vision.analyze({'images': []}, 'Where is the river?')


def test_ollama_missing_model_raises_clear_error(monkeypatch):
    from gateway.errors import InputError
    cloud_vision.configure(None, provider='ollama', model='')
    monkeypatch.setattr(cloud_vision, 'is_ollama_running', lambda *a, **kw: True)
    with pytest.raises(InputError, match='Ollama model naam'):
        cloud_vision.analyze({'images': []}, 'Where is the river?')


def test_ollama_successful_chat_response(monkeypatch):
    cloud_vision.configure(None, provider='ollama', model='llama3.2-vision')
    monkeypatch.setattr(cloud_vision, 'is_ollama_running', lambda *a, **kw: True)
    assert cloud_vision.enabled()

    captured = {}
    def mock_post(url, **kwargs):
        captured['url'] = url
        captured['json'] = kwargs['json']
        ollama_reply = {
            'message': {
                'role': 'assistant',
                'content': json.dumps({
                    'description': 'A dense urban scene with multiple transit corridors.',
                    'answer': 'Roads and transit routes are visible throughout.',
                    'image_type': 'satellite image',
                    'visible_features': ['Roads', 'Buildings'],
                    'uncertainties': ['Building heights cannot be established.']
                })
            },
            'done': True,
            'prompt_eval_count': 120,
            'eval_count': 45,
            'total_duration': 850000000
        }
        return httpx.Response(200, json=ollama_reply)

    monkeypatch.setattr(httpx, 'post', mock_post)
    buffer = io.BytesIO()
    Image.fromarray(np.zeros((64, 64, 3), dtype='uint8')).save(buffer, format='PNG')
    client = TestClient(app, base_url='http://localhost')
    res = client.post('/api/analyze', files={'images': ('map.png', buffer.getvalue(), 'image/png')}, data={'query': 'Highlight roads', 'scenario': 'SINGLE', 'options': '[{}]'})
    assert res.status_code == 200, res.text
    data = res.json()
    assert data['interpretation_source'] == 'ollama'
    assert data['provenance']['provider'] == 'Local Ollama'
    assert data['cloud_vision']['provider'] == 'Local Ollama'
    assert data['cloud_vision']['model'] == 'llama3.2-vision'
    assert data['description'] == 'A dense urban scene with multiple transit corridors.'
    assert 'Roads' in data['visible_features']
    assert 'Building heights cannot be established.' in data['uncertainties']
    assert captured['url'] == 'http://localhost:11434/api/chat'
    assert captured['json']['model'] == 'llama3.2-vision'
    assert len(captured['json']['messages'][1]['images']) == 1


def test_ollama_setup_settings_endpoint(monkeypatch):
    monkeypatch.setattr(cloud_vision, 'is_ollama_running', lambda *a, **kw: True)
    client = TestClient(app, base_url='http://localhost')
    headers = {'X-SatQuery-CSRF': client.get('/api/vision/settings').json()['csrf_token']}
    res = client.post('/api/vision/settings', headers=headers, json={'provider': 'ollama', 'model': 'llama3.2-vision'})
    assert res.status_code == 200
    d = res.json()
    assert d['provider_id'] == 'ollama'
    assert d['model'] == 'llama3.2-vision'
    assert d['enabled'] is True

