/* Estado de sesión; la API es la única fuente de datos persistentes. */
let U=null,edit=false,sel=null,view='planta',plantSocket=null;
const DEF=()=>[{n:'Soldadura',a:'soldadura',k:'soldadura',f:2,t:2},{n:'Pintura',a:'pintura',k:'pintura',f:1,t:1},{n:'Montaje',a:'montaje',k:'montaje',f:0,t:0}];
function calendarWeek(date=new Date()){
	const day=new Date(Date.UTC(date.getFullYear(),date.getMonth(),date.getDate()));
	day.setUTCDate(day.getUTCDate()+4-(day.getUTCDay()||7));
	const year=day.getUTCFullYear();
	const week=Math.ceil((((day-new Date(Date.UTC(year,0,1)))/86400000)+1)/7);
	return{year,week};
}
const weekKey=week=>`${S.year}-W${String(week).padStart(2,'0')}`;
const weekNumber=value=>Number(String(value).match(/W(\d{1,2})$/)?.[1]||value);
const weeksInYear=year=>calendarWeek(new Date(Date.UTC(year,11,28))).week;

async function loadCalendarData(year){
	const from=`${year}-W01`,to=`${year}-W${String(weeksInYear(year)).padStart(2,'0')}`;
	const [capacity,heatmap]=await Promise.all([
		apiFetch(`/capacity?from=${from}&to=${to}`),apiFetch(`/heatmap?from=${from}&to=${to}`)
	]);
	S.capacityByWeek=Object.fromEntries(capacity.map(item=>[item.week,item]));
	S.heatmapByWeek=Object.fromEntries(heatmap.map(item=>[item.week,item]));
}

async function loadPlantStatus(week=S.week){
	const data=await apiFetch(`/plant-status?week=${encodeURIComponent(weekKey(week))}`);
	S.stationStatus=Object.fromEntries(data.stations.map(st=>[st.id,st]));
}

async function loadAppData(year=S?.year,selectedWeek=S?.week){
	const current=calendarWeek();
	year=year||current.year;
	selectedWeek=selectedWeek||current.week;
	S={year,week:selectedWeek,g:{c:14,r:8},st:[],or:[],team:[],flow:DEF(),adjustments:[],adj:{},capacityByWeek:{},heatmapByWeek:{},stationStatus:{}};
	const [plant,stations,orders,workers,workflow,adjustments]=await Promise.all([
		apiFetch('/plants/armentera'),apiFetch('/stations'),apiFetch('/orders'),apiFetch('/workers'),apiFetch('/workflow'),
		apiFetch('/capacity/adjustments')
	]);
	S.g={c:plant.cols,r:plant.rows};
	S.st=stations.map(st=>({...st,hps:st.hoursPerShift,status:({active:'act',stopped:'parada',maintenance:'mant'})[st.status]||'act'}));
	S.or=orders.map(order=>({
		id:order.id,of:order.code,cli:order.client,q:order.quantity,d:weekNumber(order.delivery_week),
		delivery_week:order.delivery_week,current_week:order.current_week,lead:order.lead_time_weeks,
		hs:order.hours_per_unit.soldadura||0,hp:order.hours_per_unit.pintura||0,hm:order.hours_per_unit.montaje||0,
		hours_per_unit:order.hours_per_unit,active_phases:order.active_phases,status:order.status,
		required_skill:order.required_skill,allocations:order.allocations||[]
	}));
	S.team=workers.map(worker=>({id:worker.id,n:worker.name,sid:worker.station_id,skills:worker.skills,absences:worker.absences}));
	S.flow=workflow.length?workflow.map(step=>({
		n:step.name,a:step.area_id,k:step.area_id,f:step.offset_weeks_before_delivery,t:step.offset_weeks_before_delivery,
		step_order:step.step_order,is_optional:step.is_optional
	})):DEF();
	S.adjustments=adjustments;
	S.adj=Object.fromEntries(adjustments.map(item=>[`${item.week}|${item.area}`,(S.adj[`${item.week}|${item.area}`]||0)-item.hours_delta]));
	await loadCalendarData(year);
	await loadPlantStatus();
}

function connectPlantUpdates(){
	disconnectPlantUpdates();
	const protocol=location.protocol==='https:'?'wss:':'ws:';
	plantSocket=new WebSocket(`${protocol}//${location.host}/api/v1/ws/plant`);
	plantSocket.onmessage=async()=>{if(!U)return;try{await loadAppData();draw()}catch(e){showError(e.message)}};
	plantSocket.onclose=()=>{plantSocket=null};
}

function disconnectPlantUpdates(){if(plantSocket){plantSocket.close();plantSocket=null}}
