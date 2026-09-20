"""Opt-in contextual evidence from an allowlisted public weather archive."""
from datetime import date,timedelta
from typing import Protocol
import httpx
from rasterio.warp import transform


class ContextProvider(Protocol):
    def fetch(self,latitude:float,longitude:float,day:str)->dict: ...


class RainfallArchive:
    def fetch(self,latitude,longitude,day):
        end=date.fromisoformat(day);start=end-timedelta(days=6)
        with httpx.Client(timeout=15) as client:
            response=client.get('https://archive-api.open-meteo.com/v1/archive',params={
                'latitude':latitude,'longitude':longitude,'start_date':start.isoformat(),'end_date':end.isoformat(),
                'daily':'precipitation_sum','timezone':'UTC'})
            response.raise_for_status();data=response.json()
        daily=data.get('daily',{})
        return {'status':'AVAILABLE','source':'Open-Meteo Historical Weather API','source_url':'https://open-meteo.com/en/docs/historical-weather-api',
                'dates':daily.get('time',[]),'precipitation_mm':daily.get('precipitation_sum',[]),
                'interpretation':'Auxiliary gridded weather context, not imagery evidence or a causal explanation.'}


def context_for(image,provider=None):
    if image.get('source_type')=='synthetic_demo':return {'status':'UNAVAILABLE','reason':'Synthetic fixture coordinates/dates must not be treated as a real observation.'}
    if not image.get('georeferenced') or not image.get('geospatial_measurements_allowed',True) or not image.get('date'):
        return {'status':'UNAVAILABLE','reason':'A real georeferenced observation with an acquisition date is required.'}
    bounds=image['raster_metadata']['bounds']
    if not bounds:return {'status':'UNAVAILABLE','reason':'Spatial bounds unavailable.'}
    xs,ys=transform(image['crs'],'EPSG:4326',[(bounds[0]+bounds[2])/2],[(bounds[1]+bounds[3])/2])
    try:return (provider or RainfallArchive()).fetch(ys[0],xs[0],image['date'])
    except (httpx.HTTPError,ValueError,KeyError) as exc:return {'status':'UNAVAILABLE','reason':'Context provider could not return usable data.','error_type':type(exc).__name__}
