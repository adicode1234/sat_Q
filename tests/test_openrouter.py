import io,json
import httpx,numpy as np,pytest
from PIL import Image
from fastapi.testclient import TestClient
from gateway.app import app
from models import cloud_vision

KEY='sk-or-v1-'+'test-not-a-real-key'*3
MODEL='google/gemini-2.5-flash'

@pytest.fixture(autouse=True)
def isolate(monkeypatch):
    for key,value in [('_key',None),('_enabled',False),('_provider','openrouter'),('_model',''),('_output_format','json_schema')]:
        monkeypatch.setattr(cloud_vision,key,value)
    monkeypatch.setenv('SATQUERY_PIPELINE','specialists')
    monkeypatch.delenv('OPENROUTER_API_KEY',raising=False)


def setup(client):
    token=client.get('/api/vision/settings').json()['csrf_token']
    return {'X-SatQuery-CSRF':token}


def catalog(image=True,structured=True):
    return {'data':[{'id':MODEL,'architecture':{'input_modalities':['text','image'] if image else ['text']},'supported_parameters':['structured_outputs'] if structured else []}]}


def mock_get(monkeypatch,image=True,structured=True):
    async def get(self,url,**kwargs):
        if url.endswith('/key'):
            assert kwargs['headers']=={'Authorization':'Bearer '+KEY}
            return httpx.Response(200,json={'data':{'label':'not echoed'}})
        assert url=='https://openrouter.ai/api/v1/models'
        return httpx.Response(200,json=catalog(image,structured),request=httpx.Request('GET',url))
    monkeypatch.setattr(httpx.AsyncClient,'get',get)


def test_setup_validates_key_and_model_without_echo(monkeypatch):
    mock_get(monkeypatch)
    c=TestClient(app,base_url='http://localhost')
    r=c.post('/api/vision/settings',headers=setup(c),json={'provider':'openrouter','api_key':KEY})
    assert r.status_code==200,r.text
    assert r.json()['provider_id']=='openrouter' and r.json()['model']==MODEL
    assert KEY not in r.text
    assert 'OpenRouter' in c.get('/vision-setup').text
    assert c.post('/api/vision/settings',headers=setup(c),json={'enabled':False}).json()['enabled'] is False


@pytest.mark.parametrize('image,structured',[(False,True)])
def test_nonvision_or_unstructured_model_rejected(monkeypatch,image,structured):
    mock_get(monkeypatch,image,structured)
    c=TestClient(app,base_url='http://localhost')
    r=c.post('/api/vision/settings',headers=setup(c),json={'provider':'openrouter','api_key':KEY})
    assert r.status_code==400 and not cloud_vision.enabled()


def test_key_error_never_echoes_credentials(monkeypatch):
    async def get(*a,**kw):return httpx.Response(401,json={'error':{'message':KEY}})
    monkeypatch.setattr(httpx.AsyncClient,'get',get)
    c=TestClient(app,base_url='http://localhost')
    r=c.post('/api/vision/settings',headers=setup(c),json={'provider':'openrouter','api_key':KEY})
    assert r.status_code==400 and KEY not in r.text


def png():
    b=io.BytesIO();Image.fromarray(np.random.default_rng(2).integers(0,255,(64,64,3),dtype='uint8')).save(b,format='PNG')
    return b.getvalue()


def test_real_upload_goes_to_openrouter_default_pipeline(monkeypatch):
    cloud_vision.configure(KEY,provider='openrouter')
    captured={}
    answer={'answer':'The test image is inconclusive.','description':'Uncertain image content.', 'image_type':'image','visible_features':[],'uncertainties':['Insufficient evidence.']}
    def post(url,**kwargs):
        assert url=='https://openrouter.ai/api/v1/chat/completions'
        assert kwargs['headers']['Authorization']=='Bearer '+KEY
        captured.update(kwargs['json'])
        return httpx.Response(200,json={'id':'mock-openrouter','model':MODEL,'choices':[{'finish_reason':'stop','message':{'content':json.dumps(answer)}}],'usage':{'total_tokens':10}})
    monkeypatch.setattr(httpx,'post',post)
    c=TestClient(app,base_url='http://localhost')
    r=c.post('/api/analyze',files={'images':('image.png',png(),'image/png')},data={'query':'Describe image','options':'[{}]'})
    assert r.status_code==200,r.text
    out=r.json()
    assert out['interpretation_source']=='openrouter'
    assert out['answer']==answer['answer'] and out['analysis_report']['specialist']=='OpenRouter cloud vision'
    assert not out['absent'] and out['overlay'] is None and out['trust_score'] is None
    assert out['specialists']==[] and KEY not in json.dumps(out)
    assert captured['model']==MODEL and captured['provider']['require_parameters']
    assert captured['messages'][1]['content'][2]['image_url']['url'].startswith('data:image/png;base64,')
    assert c.get(out['report_url']).json()['analysis_report']==out['analysis_report']
    assert 'OpenRouter cloud vision' in c.get(out['html_report_url']).text


@pytest.mark.parametrize('code',[401,402,403,429,500])
def test_provider_errors_are_controlled_and_redacted(monkeypatch,code):
    cloud_vision.configure(KEY,provider='openrouter')
    monkeypatch.setattr(cloud_vision,'payload',lambda *a:{'input':[{'content':[]}]})
    monkeypatch.setattr(httpx,'post',lambda *a,**kw:httpx.Response(code,json={'error':KEY}))
    from gateway.errors import InputError
    with pytest.raises(InputError) as e:cloud_vision.analyze({},'Describe')
    assert KEY not in str(e.value) and str(code) in str(e.value)


@pytest.mark.parametrize('data',[
    {'error':{'message':KEY}}, {'choices':[]},
    {'choices':[{'finish_reason':'length','message':{'content':'partial'}}]},
    {'choices':[{'finish_reason':'stop','message':{'content':'not json '+KEY}}]},
])
def test_malformed_or_incomplete_output_not_a_finding(monkeypatch,data):
    cloud_vision.configure(KEY,provider='openrouter')
    monkeypatch.setattr(cloud_vision,'payload',lambda *a:{'input':[{'content':[]}]})
    monkeypatch.setattr(httpx,'post',lambda *a,**kw:httpx.Response(200,json=data))
    from gateway.errors import InputError
    with pytest.raises(InputError) as e:cloud_vision.analyze({},'Describe')
    assert KEY not in str(e.value)


def test_temporal_question_does_not_call_provider(monkeypatch):
    cloud_vision.configure(KEY,provider='openrouter')
    def forbidden(*a,**kw):raise AssertionError('API must not run')
    monkeypatch.setattr(httpx,'post',forbidden)
    r=TestClient(app).post('/api/analyze',files={'images':('image.png',png(),'image/png')},data={'query':'What changed?','options':'[{}]'})
    assert r.status_code==422


@pytest.mark.parametrize('parameters,expected',[
    (['structured_outputs','response_format'],'json_schema'),
    (['response_format'],'json_object'),([], 'prompt_json'),(None, 'prompt_json'),
])
def test_vision_model_without_native_schema_can_connect(monkeypatch,parameters,expected):
    async def get(self,url,**kwargs):
        data={'data':{'label':'test'}} if url.endswith('/key') else catalog()
        if not url.endswith('/key'):data['data'][0]['supported_parameters']=parameters
        return httpx.Response(200,json=data,request=httpx.Request('GET',url))
    monkeypatch.setattr(httpx.AsyncClient,'get',get)
    c=TestClient(app,base_url='http://localhost')
    r=c.post('/api/vision/settings',headers=setup(c),json={'provider':'openrouter','api_key':KEY})
    assert r.status_code==200,r.text
    assert r.json()['output_format']==expected


@pytest.mark.parametrize('mode',['json_object','prompt_json'])
def test_json_compatibility_request_still_validates_response(monkeypatch,mode):
    cloud_vision.configure(KEY,provider='openrouter',output_format=mode)
    monkeypatch.setattr(cloud_vision,'payload',lambda *a:{'input':[{'content':[]}]})
    def post(url,**kwargs):
        request=kwargs['json']
        if mode=='json_object':assert request['response_format']=={'type':'json_object'}
        else:assert 'response_format' not in request
        assert 'Return ONLY a JSON object' in request['messages'][0]['content']
        return httpx.Response(200,json={'choices':[{'finish_reason':'stop','message':{'content':'{"answer":"unsupported partial output"}'}}]})
    monkeypatch.setattr(httpx,'post',post)
    from gateway.errors import InputError
    with pytest.raises(InputError,match='malformed interpretation'):cloud_vision.analyze({},'Describe')
