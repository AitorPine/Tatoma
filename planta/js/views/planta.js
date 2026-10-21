/* Vista Plano: semanas, áreas, puestos y edición del plano */
const at=(x,y)=>S.st.find(s=>x>=s.x&&x<s.x+s.w&&y>=s.y&&y<s.y+s.h);
function vPlanta(){const w=S.week,rs=S.st.map(s=>sl(s,w)),mx=Math.max(1,...rs.map(r=>Math.max(r.cap,r.load)));
const strip=Array.from({length:weeksInYear(S.year)},(_,i)=>{const k=i+1,p=(S.heatmapByWeek[weekKey(k)]?.peak_station_occupancy_pct||0)/100;return`<button class="${cls(p)} ${k==w?'cur':''}" onclick="gw(${k})" title="${weekKey(k)}: ${Math.round(p*100)}%">${k}</button>`}).join('');
const chips=AR.map(a=>{const p=pct(aCap(a,w),load(a,w,S.or));return`<div class="chip ${cls(p)}"><b>${a}</b> ${Math.round(load(a,w,S.or))} de ${Math.round(aCap(a,w))} h · <b style="color:var(--c)">${Math.round(p*100)}%</b></div>`}).join('');
let cells='';if(edit)for(let y=0;y<S.g.r;y++)for(let x=0;x<S.g.c;x++)if(!at(x,y))cells+=`<button class="empty" style="grid-column:${x+1};grid-row:${y+1}" onclick="addSt(${x},${y})" aria-label="Añadir puesto">+</button>`;
const cards=S.st.map((s,i)=>{const r=rs[i],p=pct(r.cap,r.load);return`<div class="st ${cls(p)} ${sel==s.id&&edit?'sel':''}" style="grid-column:${s.x+1}/span ${s.w};grid-row:${s.y+1}/span ${s.h};--a:var(${AC[s.area]})" onclick="pick(${s.id})"><div class="top"><b>${esc(s.name)}</b><span class="dot ${s.status}" title="${SL[s.status]}"></span></div><div class="meta"><span>${s.workers} operarios</span><span>${Math.round(r.load)} / ${Math.round(r.cap)} h</span><em>${Math.round(p*100)}%</em></div><div class="bar">${r.segs.map(g=>`<i style="width:${g.h/mx*100}%;background:${col(g.i)}" title="${esc(g.o.cli)} ${esc(g.o.of)}: ${Math.round(g.h)} h"></i>`).join('')}<u style="left:${Math.min(100,r.cap/mx*100)}%" title="Capacidad"></u></div></div>`}).join('');
const wo=S.or.map((o,i)=>({o,i,h:AR.reduce((t,a)=>t+(spread(o)[a][w]||0),0)})).filter(x=>x.h>0);
return`<div class="wk"><button class="b" onclick="gw(${w-1})" aria-label="Semana anterior">◀</button><h2>${weekKey(w)}</h2><button class="b" onclick="gw(${w+1})" aria-label="Semana siguiente">▶</button><div class="sp"></div>${canPlan()?'<button class="b" onclick="adjCap()">Ajustar capacidad</button>':''}${adm()?`<button class="b ${edit?'p':''}" onclick="edit=!edit;sel=null;draw()">${edit?'Terminar edición':'Editar plano'}</button>`:''}</div>
<div class="strip" aria-label="Ocupación máxima por semana">${strip}</div><div class="areas">${chips}</div>
<div class="scroll"><div class="plan" style="grid-template-columns:repeat(${S.g.c},minmax(0,1fr))">${cells}${cards}</div></div>
<div class="lg"><span><i style="background:var(--ok)"></i>Activa</span><span><i style="background:var(--er)"></i>Parada</span><span><i style="background:#e8902c"></i>Mantenimiento</span><span>Borde: verde &lt;80 %, ámbar 80–99 %, rojo ≥100 %</span><span>La barra se divide por pedido; la marca negra es la capacidad.</span></div>
<div class="lg">${wo.map(x=>`<span><i style="background:${col(x.i)}"></i>${esc(x.o.cli)} ${esc(x.o.of)} · ${Math.round(x.h)} h</span>`).join('')||'Sin carga esta semana.'}</div>${panel()}`}
function panel(){const s=S.st.find(x=>x.id===sel);let h='';if(edit)h+=`<section class="pn"><div class="fg"><label>Columnas<input type="number" value="${S.g.c}" min="1" max="20" onchange="S.g.c=+this.value;saveLayout()"></label><label>Filas<input type="number" value="${S.g.r}" min="1" max="20" onchange="S.g.r=+this.value;saveLayout()"></label></div><p class="lg">Pulsa + para crear un puesto y un puesto para editarlo.</p></section>`;
if(!edit||!s)return h;const f=(k,l)=>`<label>${l}<input type="number" min="0" value="${s[k]}" onchange="up('${k}',+this.value)"></label>`;
return h+`<section class="pn"><div class="fg"><label>Nombre<input value="${esc(s.name)}" onchange="up('name',this.value)"></label><label>Área<select onchange="up('area',this.value)">${AR.map(a=>`<option ${a==s.area?'selected':''}>${a}</option>`).join('')}</select></label><label>Estado<select onchange="up('status',this.value)">${Object.entries(SL).map(([k,v])=>`<option value="${k}" ${k==s.status?'selected':''}>${v}</option>`).join('')}</select></label>${f('workers','Operarios')}${f('shifts','Turnos')}${f('hps','Horas por turno')}${f('max_shifts','Máximo de turnos') }<label>Unidades por turno<input type="number" min="1" value="${s.unitsPerShift??''}" onchange="up('unitsPerShift',this.value===''?null:+this.value)"></label><label>Habilidades permitidas<input value="${esc((s.skills||[]).join(', '))}" onchange="updateSkills(this.value)"></label>${f('w','Ancho (celdas)')}${f('h','Alto (celdas)')}</div><p><button class="b d" onclick="delSt()">Eliminar puesto</button></p></section>`}
const gw=async w=>{
	let year=S.year,week=w;
	if(week>weeksInYear(year)){year++;week=1}
	if(week<1){year--;week=weeksInYear(year)}
	try{
		if(year!==S.year)await loadAppData(year,week);
		else{S.week=week;await loadPlantStatus()}
		draw();
	}catch(e){showError(e.message)}
},pick=id=>{if(edit){sel=id;draw()}};
async function addSt(x,y){
	const id=`WEB-${Date.now()}`;
	try{
		await apiFetch('/stations',{method:'POST',body:{id,name:'Puesto nuevo',area:'soldadura',x,y,w:1,h:1,workers:1,shifts:1,hoursPerShift:8,status:'active'}});
		await loadAppData();sel=id;draw();
	}catch(e){showError(e.message)}
}
async function up(key,value){
	const station=S.st.find(item=>item.id===sel);
	if(!station)return;
	const field=key==='hps'?'hoursPerShift':key;
	const payload=key==='status'?{status:({act:'active',parada:'stopped',mant:'maintenance'})[value]}:{[field]:value};
	try{await apiFetch(`/stations/${encodeURIComponent(station.id)}`,{method:'PATCH',body:payload});await loadAppData();draw()}
	catch(e){showError(e.message)}
}
async function updateSkills(value){
	const station=S.st.find(item=>item.id===sel);
	if(!station)return;
	const skills=value.split(',').map(skill=>skill.trim()).filter(Boolean);
	try{await apiFetch(`/stations/${encodeURIComponent(station.id)}/skills`,{method:'PUT',body:{skills}});await loadAppData();draw()}
	catch(e){showError(e.message)}
}
async function saveLayout(){
	try{
		await apiFetch('/plants/armentera/layout',{method:'PUT',body:{cols:S.g.c,rows:S.g.r,positions:S.st.map(({id,x,y,w,h})=>({id,x,y,w,h}))}});
		await loadAppData();draw();
	}catch(e){showError(e.message)}
}
async function delSt(){
	try{await apiFetch(`/stations/${encodeURIComponent(sel)}`,{method:'DELETE'});sel=null;await loadAppData();draw()}
	catch(e){showError(e.message)}
}
async function adjCap(){
	const area=prompt('Área a ajustar: soldadura, pintura o montaje');
	if(!AR.includes(area))return;
	const hours=Number(prompt(`Horas a restar en la semana ${S.week}. Usa 0 para quitar el ajuste.`));
	if(!Number.isFinite(hours)||hours<0)return;
	const week=weekKey(S.week);
	const adjustments=S.adjustments.filter(item=>!(item.week===week&&item.area===area&&!item.station_id));
	if(hours)adjustments.push({week,area,hours_delta:-hours,reason:'averia'});
	try{
		await apiFetch('/capacity/adjustments',{method:'PUT',body:{adjustments}});
		await loadAppData();draw();
	}catch(e){showError(e.message)}
}
