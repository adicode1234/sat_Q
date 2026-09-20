"""Download a small reproducible public-data slice; never substitute synthetic data.

VRSBench uses official evaluation annotations and byte-range ZIP access.
CDVQA uses a community WebDataset mirror's explicit test split.
RSVQA fallback is a community validation subset, NOT an official test result.
Every attempted source and failure is recorded.
"""
import io,json,tarfile,zipfile,hashlib
from pathlib import Path
import requests
ROOT=Path(__file__).resolve().parents[1]

def get(url,**kwargs):
    r=requests.get(url,timeout=60,**kwargs);r.raise_for_status();return r

class RemoteZip(io.RawIOBase):
    def __init__(self,url):
        self.url=url;self.pos=0
        r=get(url,headers={'Range':'bytes=0-0'},stream=True)
        if r.status_code!=206:r.close();raise ValueError('Server does not support bounded ZIP byte ranges')
        self.size=int(r.headers['Content-Range'].split('/')[-1]);r.close()
    def seekable(self):return True
    def tell(self):return self.pos
    def seek(self,offset,whence=0):
        self.pos=offset if whence==0 else self.pos+offset if whence==1 else self.size+offset;return self.pos
    def read(self,n=-1):
        if n<0:n=self.size-self.pos
        if n==0:return b''
        if n>32*1024*1024:raise ValueError('Remote ZIP read exceeds 32 MiB safety bound')
        end=min(self.pos+n,self.size)-1
        r=get(self.url,headers={'Range':f'bytes={self.pos}-{end}'},stream=True)
        if r.status_code!=206:r.close();raise ValueError('Range request ignored')
        content=r.content;r.close();self.pos+=len(content);return content

def main():
    samples=[];log=[]
    def save(folder,name,blob):
        path=ROOT/'data'/folder/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(blob)
        return str(path.relative_to(ROOT)).replace('\\','/')
    try:
        source='https://huggingface.co/datasets/xiang709/VRSBench'
        annotations=get(source+'/resolve/main/VRSBench_EVAL_vqa.json').json()
        with zipfile.ZipFile(RemoteZip(source+'/resolve/main/Images_val.zip')) as archive:
            names=archive.namelist()
            for row in annotations[:4]:
                name=next(n for n in names if n.endswith('/'+row['image_id']) or n==row['image_id'])
                path=save('vrsbench',row['image_id'],archive.read(name))
                samples.append({'dataset':'VRSBench','split':'official_eval','id':str(row['question_id']),'paths':[path],
                                'query':row['question'],'answer':row['ground_truth'],'scenario':'SINGLE',
                                'options':[{'modality':'optical','benchmark_source':source}],'source':source})
        log.append({'dataset':'VRSBench','status':'downloaded','count':4})
    except Exception as e:log.append({'dataset':'VRSBench','status':'blocked','reason':f'{type(e).__name__}: {e}'})
    try:
        source='https://huggingface.co/datasets/ljx620/CDVQA'
        response=get(source+'/resolve/main/test/test-00000.tar',stream=True)
        blobs={};count=0
        with tarfile.open(fileobj=response.raw,mode='r|') as archive:
            for member in archive:
                if not member.isfile():continue
                if member.size>8*1024*1024:raise ValueError('Unexpectedly large dataset member')
                key=member.name.split('.')[0];blobs[member.name]=archive.extractfile(member).read()
                if member.name.endswith('.json'):
                    row=json.loads(blobs[member.name]);paths=[]
                    from PIL import Image
                    for i in range(2):
                        im=Image.open(io.BytesIO(blobs[f'{key}.{i}.img'])).convert('RGB');buf=io.BytesIO();im.save(buf,format='PNG')
                        paths.append(save('cdvqa',f'{key}_{i}.png',buf.getvalue()))
                    options=[{'modality':'optical','benchmark_source':source,'coregistered':True,'time_index':i} for i in range(2)]
                    samples.append({'dataset':'CDVQA','split':'test_mirror','id':key,'paths':paths,'options':options,'scenario':'BITEMPORAL_PAIR',
                                    'query':row['conversations'][0]['value'].replace('Image 1: <image>\nImage 2: <image>\n',''),
                                    'answer':row['conversations'][1]['value'],'source':source,'source_metadata':row['meta']})
                    count+=1;blobs={}
                    if count>=4:break
        response.close();log.append({'dataset':'CDVQA','status':'downloaded','count':count})
    except Exception as e:log.append({'dataset':'CDVQA','status':'blocked','reason':f'{type(e).__name__}: {e}'})
    try:
        source='https://huggingface.co/datasets/dmarsili/RSVQA-LR-2k'
        response=get('https://datasets-server.huggingface.co/first-rows',params={'dataset':'dmarsili/RSVQA-LR-2k','config':'default','split':'validation'}).json()
        for item in response['rows'][:4]:
            row=item['row'];path=save('rsvqa',f'validation_{item["row_idx"]}.jpg',get(row['image']['src']).content)
            samples.append({'dataset':'RSVQA','split':'community_validation','id':str(item['row_idx']),'paths':[path],
                            'query':row['question'],'answer':row['answer'],'scenario':'SINGLE',
                            'options':[{'modality':'optical','benchmark_source':source}],'source':source})
        log.append({'dataset':'RSVQA','status':'partial','count':4,'reason':'Official Zenodo record 6344334 timed out. These are community validation samples, not official test data.'})
    except Exception as e:log.append({'dataset':'RSVQA','status':'blocked','reason':f'{type(e).__name__}: {e}'})
    for s in samples:s['sha256']=[hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in s['paths']]
    (ROOT/'evaluation/samples.json').write_text(json.dumps(samples,indent=2),encoding='utf-8')
    (ROOT/'evaluation/data_status.json').write_text(json.dumps(log,indent=2),encoding='utf-8')
    print(json.dumps(log,indent=2))
if __name__=='__main__':main()
