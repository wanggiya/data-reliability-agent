const Map = ol.Map;
const View = ol.View;
const TileLayer = ol.layer.Tile;
const VectorLayer = ol.layer.Vector;
const OSM = ol.source.OSM;
const XYZ = ol.source.XYZ;
const VectorSource = ol.source.Vector;
const Feature = ol.Feature;
const Polygon = ol.geom.Polygon;
const Point = ol.geom.Point;
const CircleGeom = ol.geom.Circle;
const Style = ol.style.Style;
const Fill = ol.style.Fill;
const Stroke = ol.style.Stroke;
const CircleStyle = ol.style.Circle;
const fromLonLat = ol.proj.fromLonLat;
const {createEmpty, extend} = ol.extent;

const palette = {
  OPTICAL_L2SP: ['rgba(34,197,94,.24)', '#22c55e'],
  OPTICAL_L2A: ['rgba(245,158,11,.26)', '#f59e0b'],
  SAR_SLC: ['rgba(37,99,235,.24)', '#2563eb'],
  SAR_GRD: ['rgba(6,182,212,.24)', '#06b6d4'],
  DERIVED_INSAR: ['rgba(217,70,239,.28)', '#d946ef'],
};
const vectorSources = Object.fromEntries(Object.keys(palette).map(key => [key, new VectorSource()]));
const vectorLayers = Object.fromEntries(Object.entries(vectorSources).map(([key, source]) => [key, new VectorLayer({source, style: new Style({fill:new Fill({color:palette[key][0]}),stroke:new Stroke({color:palette[key][1],width:2})})})]));
const boundarySource = new VectorSource();
const boundaryLayer = new VectorLayer({source:boundarySource, style:new Style({fill:new Fill({color:'rgba(239,68,68,.04)'}),stroke:new Stroke({color:'#ff3b3b',width:3})})});
const impactSource = new VectorSource();
const impactLayer = new VectorLayer({source:impactSource,style:feature=>new Style({fill:new Fill({color:feature.get('fill')}),stroke:new Stroke({color:feature.get('stroke'),width:1.4})})});
const eventSource = new VectorSource();
const eventLayer = new VectorLayer({source:eventSource, style:new Style({image:new CircleStyle({radius:7,fill:new Fill({color:'#dc2626'}),stroke:new Stroke({color:'#fff',width:2})})})});

const basemapLayers = {
  light: new TileLayer({source:new OSM()}),
  dark: new TileLayer({source:new OSM(),className:'basemap-dark',visible:false}),
  terrain: new TileLayer({source:new XYZ({url:'https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}',attributions:'Tiles © Esri'}),visible:false}),
  satellite: new TileLayer({source:new XYZ({url:'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',attributions:'Tiles © Esri'}),visible:false}),
};
const hillshadeLayer=new TileLayer({source:new XYZ({url:'https://server.arcgisonline.com/ArcGIS/rest/services/Elevation/World_Hillshade/MapServer/tile/{z}/{y}/{x}',attributions:'Elevation hillshade © Esri'}),opacity:.48,visible:false});
const hydroLayer=new TileLayer({source:new XYZ({url:'https://tiles.arcgis.com/tiles/P3ePLMYs2RVChkJx/arcgis/rest/services/Esri_Hydro_Reference_Overlay/MapServer/tile/{z}/{y}/{x}',attributions:'Hydro reference © Esri'}),opacity:.9,visible:false});
const map = new Map({target:'map',layers:[...Object.values(basemapLayers),hillshadeLayer,hydroLayer,impactLayer,...Object.values(vectorLayers),boundaryLayer,eventLayer],view:new View({center:fromLonLat([15,18]),zoom:2,minZoom:2})});
let result = null;
let timelineDates = [];
const $ = id => document.getElementById(id);
const esc = value => String(value ?? '—').replace(/[&<>'"]/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[char]));
const projectRing = ring => ring.map(coord => fromLonLat(coord));

function sceneFeature(asset) {
  const feature = new Feature(new Polygon([projectRing(asset.footprint)]));
  feature.setProperties({kind:'Satellite footprint', title:asset.filename, asset});
  return feature;
}

function refreshScenes() {
  Object.values(vectorSources).forEach(source => source.clear());
  if (!result || !timelineDates.length) return;
  const lower = timelineDates[Number($('time-start').value)];
  const upper = timelineDates[Number($('time-end').value)];
  const visible = result.assets.filter(asset => asset.acquisition_date >= lower && asset.acquisition_date <= upper);
  visible.forEach(asset => vectorSources[asset.product_type]?.addFeature(sceneFeature(asset)));
  $('time-start-label').textContent = lower;
  $('time-end-label').textContent = upper;
  $('timeline-items').replaceChildren(...visible.map(asset => {
    const chip = document.createElement('div'); chip.className='scene-chip'; chip.style.borderColor=palette[asset.product_type]?.[1] ?? '#94a3b8';
    chip.innerHTML=`<b>${esc(asset.acquisition_date)} · ${esc(asset.temporal_phase)}</b><span>${esc(asset.platform)}</span><span>${esc(asset.product_type)}</span>`;
    chip.onclick=()=>showDetail(asset); return chip;
  }));
}

function refreshImpact() {
  impactSource.clear();
  if (result?.event?.longitude == null || result?.event?.latitude == null) return;
  const center=fromLonLat([result.event.longitude,result.event.latitude]);
  const radius=Number($('radius').value)*1000;
  const waterHazard=['flood','water','tsunami','storm','cyclone'].some(term=>String(result.event.hazard).toLowerCase().includes(term));
  [[1,.07],[.68,.10],[.36,.16]].forEach(([scale,alpha])=>{const feature=new Feature(new CircleGeom(center,radius*scale));feature.setProperties({kind:waterHazard?'Illustrative flood planning zone':'Affected-area planning zone',title:`${Math.round(radius*scale/1000)} km planning radius`,fill:waterHazard?`rgba(14,165,233,${alpha})`:`rgba(239,68,68,${alpha})`,stroke:waterHazard?'rgba(56,189,248,.78)':'rgba(248,113,113,.58)'});impactSource.addFeature(feature);});
}

function showDetail(asset) {
  $('detail-title').textContent=asset.filename;
  $('detail-body').innerHTML=`<p><b>${esc(asset.platform)} · ${esc(asset.product_type)}</b></p><p>Acquired: ${esc(asset.acquisition_datetime)}<br>Phase: ${esc(asset.temporal_phase)}<br>CRS: ${esc(asset.crs)}<br>Resolution: ${esc(asset.spatial_resolution_m)} m<br>Bands: ${esc(asset.bands.join(', '))}<br>Orbit: ${esc(asset.orbit_direction)}<br>Status: ${esc(asset.catalog_status)} · verified: ${esc(asset.verified_remote)}</p><p>${esc(asset.notes)}</p>`;
  $('detail').classList.remove('hidden');
}

function renderResult(data) {
  result=data; boundarySource.clear(); eventSource.clear();
  const waterHazard=['flood','water','tsunami','storm','cyclone'].some(term=>String(data.event.hazard).toLowerCase().includes(term));
  if(waterHazard){$('hydro').checked=true;hydroLayer.setVisible(true);}
  data.districts.forEach(district=>{const feature=new Feature(new Polygon([projectRing(district.boundary)]));feature.setProperties({kind:'Political administrative boundary',title:district.name,district});boundarySource.addFeature(feature);});
  if (data.event.longitude != null && data.event.latitude != null) {const feature=new Feature(new Point(fromLonLat([data.event.longitude,data.event.latitude])));feature.setProperties({kind:'Event epicenter',title:data.event.event_name,event:data.event});eventSource.addFeature(feature);}
  timelineDates=[...new Set(data.assets.map(asset=>asset.acquisition_date))].sort();
  ['time-start','time-end'].forEach(id=>{$(id).max=Math.max(0,timelineDates.length-1)}); $('time-start').value=0; $('time-end').value=Math.max(0,timelineDates.length-1);
  $('event-date').textContent=`Event: ${data.event.start_date} · ${data.event.event_name}`;
  refreshScenes(); refreshImpact();
  const extent=createEmpty(); [boundarySource,eventSource,...Object.values(vectorSources)].forEach(source=>{if(source.getFeatures().length)extend(extent,source.getExtent())});
  const hasExtent=extent.every(Number.isFinite);
  if(hasExtent){map.getView().fit(extent,{padding:[70,275,205,430],duration:1200,maxZoom:8});}
  else if(data.event.longitude!=null&&data.event.latitude!=null){map.getView().animate({center:fromLonLat([data.event.longitude,data.event.latitude]),zoom:7,duration:900});}
  const noGeometry=!hasExtent&&data.event.longitude==null;
  $('status').textContent=noGeometry
    ? `Resolved without coordinates · check Ollama model/configuration · ${data.warnings[0]??'no mapped results'}`
    : `${data.assets.length} candidates · ${data.districts.length} areas · ${data.warnings.length ? data.warnings[0] : 'boundaries resolved'}`;
}

$('search').onclick=async()=>{
  $('status').textContent='Resolving event, political boundaries, and satellite candidates…'; $('search').disabled=true;
  try {const response=await fetch(`/discover?mode=${encodeURIComponent($('mode').value)}`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({query:$('query').value,start_date:$('start').value,end_date:$('end').value,platforms:[],product_types:[]})});if(!response.ok)throw new Error(await response.text());renderResult(await response.json());}
  catch(error){$('status').textContent=`Search failed: ${error.message}`;} finally{$('search').disabled=false;}
};

document.querySelectorAll('[data-layer]').forEach(input=>input.onchange=()=>vectorLayers[input.dataset.layer].setVisible(input.checked));
$('basemap').onchange=()=>Object.entries(basemapLayers).forEach(([name,layer])=>layer.setVisible(name===$('basemap').value));
$('hillshade').onchange=()=>hillshadeLayer.setVisible($('hillshade').checked);
$('hydro').onchange=()=>hydroLayer.setVisible($('hydro').checked);
document.querySelectorAll('[data-collapse]').forEach(button=>button.onclick=()=>{
  const panel=button.closest('.panel'); panel.classList.toggle('collapsed');
  button.textContent=panel.classList.contains('collapsed')?'+':'−';
  button.setAttribute('aria-expanded',String(!panel.classList.contains('collapsed')));
  window.setTimeout(()=>map.updateSize(),220);
});
$('boundaries').onchange=()=>boundaryLayer.setVisible($('boundaries').checked);
$('affected').onchange=()=>impactLayer.setVisible($('affected').checked);
$('radius').oninput=()=>{$('radius-value').textContent=`${$('radius').value} km`;refreshImpact();};
$('time-start').oninput=()=>{if(+$('time-start').value>+$('time-end').value)$('time-start').value=$('time-end').value;refreshScenes();};
$('time-end').oninput=()=>{if(+$('time-end').value<+$('time-start').value)$('time-end').value=$('time-start').value;refreshScenes();};
$('detail-close').onclick=()=>$('detail').classList.add('hidden');

map.on('pointermove',event=>{const popup=$('popup');const feature=map.forEachFeatureAtPixel(event.pixel,item=>item);if(!feature){popup.classList.add('hidden');return;}const asset=feature.get('asset'),district=feature.get('district'),title=feature.get('title');popup.innerHTML=`<b>${esc(feature.get('kind'))}</b><br>${esc(title)}${asset?`<br>${esc(asset.acquisition_date)} · ${esc(asset.temporal_phase)}<br>${esc(asset.crs)} · ${esc(asset.bands.join(', '))}`:''}${district?`<br>${esc(district.boundary_source)} · ${esc(district.boundary_status)}`:''}`;popup.style.left=`${event.pixel[0]+14}px`;popup.style.top=`${event.pixel[1]+14}px`;popup.classList.remove('hidden');});
map.on('click',event=>{const feature=map.forEachFeatureAtPixel(event.pixel,item=>item);if(feature?.get('asset'))showDetail(feature.get('asset'));});
