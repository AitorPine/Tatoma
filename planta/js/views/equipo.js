/* Vista Equipo: operarios, puesto asignado y calendario de ausencias. */
function vTeam(){const stations=S.st.map(station=>`<option value="${station.id}">${esc(station.name)}</option>`).join('');return`<div class="card tw"><h2>Equipo</h2><div class="fg"><label>Nombre<input id="wn" required></label><label>Puesto<select id="ws">${stations}</select></label><label>&nbsp;<button class="b p" onclick="addW()">Añadir trabajador</button></label></div><table><tr><th>Nombre</th><th>Puesto</th><th>Habilidades</th><th>Ausencias</th><th></th></tr>${S.team.map((worker,index)=>`<tr><td>${esc(worker.n)}</td><td><select onchange="mvW(${index},this.value)">${S.st.map(station=>`<option value="${station.id}" ${station.id===worker.sid?'selected':''}>${esc(station.name)}</option>`).join('')}</select></td><td>${worker.skills.map(esc).join(', ')}</td><td>${worker.absences.map(absence=>`${esc(absence.week)} · ${absence.hours} h · ${esc(absence.reason)}`).join('<br>')||'—'} <button class="b" onclick="editAbsences(${index})">Editar</button></td><td><button class="b d" onclick="delW(${index})">Quitar</button></td></tr>`).join('')}</table></div>`}

async function addW(){
	const name=$('#wn').value.trim(),station_id=$('#ws').value;
	if(!name)return;
	try{await apiFetch('/workers',{method:'POST',body:{name,station_id,skills:['general']}});await loadAppData();draw()}
	catch(e){showError(e.message)}
}

async function delW(index){
	try{await apiFetch(`/workers/${S.team[index].id}`,{method:'DELETE'});await loadAppData();draw()}
	catch(e){showError(e.message)}
}

async function mvW(index,station_id){
	const worker=S.team[index];
	if(worker.sid===station_id)return;
	try{await apiFetch(`/workers/${worker.id}`,{method:'PATCH',body:{station_id}});await loadAppData();draw()}
	catch(e){showError(e.message)}
}

async function editAbsences(index){
	const worker=S.team[index];
	const entered=prompt('Semana de la ausencia (por ejemplo 2026-W08):');
	if(!entered)return;
	const week=/^\d{4}-W\d{1,2}$/i.test(entered)?entered.toUpperCase():`${S.year}-W${String(Number(entered)).padStart(2,'0')}`;
	const hours=Number(prompt('Horas de ausencia; usa 0 para quitar esta semana:', '0'));
	if(!Number.isFinite(hours)||hours<0)return;
	const reason=hours?prompt('Motivo: vacaciones o baja', 'vacaciones'):'vacaciones';
	if(hours&&reason!=='vacaciones'&&reason!=='baja')return;
	const absences=worker.absences.filter(absence=>absence.week!==week);
	if(hours)absences.push({week,hours,reason});
	try{await apiFetch(`/workers/${worker.id}/absences`,{method:'PUT',body:{absences}});await loadAppData();draw()}
	catch(e){showError(e.message)}
}
