/* Métricas presentadas a partir de las asignaciones calculadas por el backend. */
function spread(order){
	const result=Object.fromEntries(AR.map(area=>[area,{}]));
	for(const allocation of order.allocations||[]){
		if(!result[allocation.area])result[allocation.area]={};
		const week=allocation.week;
		result[allocation.area][week]=(result[allocation.area][week]||0)+allocation.allocated_hours;
	}
	return result;
}
const stCap=(station,week=S.week)=>{
	const metrics=S.capacityByWeek[weekKey(week)]?.stations.find(item=>item.station_id===station.id);
	return metrics?.capacity_hours||0;
};
const aSt=area=>S.st.filter(station=>station.area===area);
const aRaw=area=>S.capacityByWeek[weekKey(S.week)]?.areas[area]?.capacity_hours||0;
const aCap=(area,week)=>S.capacityByWeek[weekKey(week)]?.areas[area]?.capacity_hours||0;
const load=(area,week,orders)=>orders.reduce((total,order)=>total+(spread(order)[area]?.[weekKey(week)]||0),0);
const pct=(capacity,loaded)=>capacity>0?loaded/capacity:(loaded>0?9.99:0),cls=value=>value>=1?'er':value>=.8?'wn':'ok';
function sl(station,week){
	const metrics=S.capacityByWeek[weekKey(week)]?.stations.find(item=>item.station_id===station.id);
	const loaded=metrics?.committed_hours||0;
	const orders=S.or.flatMap((order,index)=>(order.allocations||[])
		.filter(allocation=>allocation.station_id===station.id&&allocation.week===weekKey(week))
		.map(allocation=>({o:order,i:index,h:allocation.allocated_hours})));
	return{cap:metrics?.capacity_hours||0,load:loaded,segs:orders};
}
